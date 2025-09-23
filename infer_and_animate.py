"""
kolam_animator_ui.py

Polished Tkinter Kolam Animator
- Accepts stroke sequences of form [[dx,dy,pen], ...] (deltas normalized or pixels).
- Demo generator included if no file is loaded.
- Controls: Play/Pause, Step Forward, Step Back, Rewind, Speed, Load JSON, Toggle Grid, Save Snapshot.
- Sparkle particle effect when stroke ends (pen==1).
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import ImageGrab, Image, ImageTk, ImageOps
import json, math, random, os, time

# -------------------------
# Utilities / Demo sequence
# -------------------------
def demo_spiral_sequence(center=(300, 250), spacing=2.0, turns=3, points_per_turn=120):
    """Create a spiral stroke (list of deltas). pen=0 during stroke, pen=1 at end."""
    cx, cy = center
    points = []
    for i in range(turns * points_per_turn):
        t = i / points_per_turn
        angle = 2 * math.pi * t
        rad = spacing * angle / (2 * math.pi)
        x = cx + rad * math.cos(angle)
        y = cy + rad * math.sin(angle)
        points.append((x, y))
    # convert absolute points to deltas
    seq = []
    last = None
    for p in points:
        if last is None:
            dx, dy = p[0], p[1]
        else:
            dx, dy = p[0] - last[0], p[1] - last[1]
        seq.append([dx, dy, 0.0])
        last = p
    seq.append([0.0, 0.0, 1.0])  # pen lift at end
    return seq

def demo_diamond_grid(rows=5, cols=5, spacing=60, offset=(120,100)):
    """Create several diamond strokes around each grid dot."""
    ox, oy = offset
    strokes = []
    for r in range(rows):
        for c in range(cols):
            cx = ox + c*spacing
            cy = oy + r*spacing
            r0 = spacing*0.35
            pts = [(cx, cy-r0), (cx+r0, cy), (cx, cy+r0), (cx-r0, cy), (cx, cy-r0)]
            stroke = []
            for i in range(len(pts)-1):
                a, b = pts[i], pts[i+1]
                # minor interpolation for smoothness
                for t in range(8):
                    tnorm = t/(8-1)
                    x = a[0] + (b[0]-a[0])*tnorm
                    y = a[1] + (b[1]-a[1])*tnorm
                    stroke.append((x,y))
            strokes.append(stroke)
    # Flatten strokes to delta sequence with pen lifts
    seq = []
    for s in strokes:
        last = None
        for p in s:
            if last is None:
                dx, dy = p[0], p[1]
            else:
                dx, dy = p[0]-last[0], p[1]-last[1]
            seq.append([dx, dy, 0.0])
            last = p
        seq.append([0.0, 0.0, 1.0])
    return seq

# -------------------------
# Animator UI
# -------------------------
class KolamAnimator:
    def __init__(self, root, width=800, height=600):
        self.root = root
        self.root.title("Kolam Animator — Step-by-step AI Kolam")
        self.width = width
        self.height = height

        # Canvas & drawing state
        self.canvas = tk.Canvas(root, bg="white", width=width, height=height)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = tk.Frame(root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        # Controls
        self.playing = False
        self.index = 0  # current index in sequence
        self.sequence = []  # list of [dx,dy,pen]
        self.abs_positions = []  # computed absolute positions for each item
        self.drawn_items = []  # canvas item ids for lines drawn (for undo/back)
        self.speed_ms = tk.IntVar(value=30)  # animation interval in ms
        self.grid_visible = tk.BooleanVar(value=True)
        self.dots = []  # list of (x,y) for grid sparkle points (if provided)
        self.particle_items = []  # active sparkle particle ids

        # Create controls
        self._create_controls()

        # Bind keyboard shortcuts
        root.bind("<space>", lambda e: self.toggle_play())
        root.bind("<Right>", lambda e: self.step_forward())
        root.bind("<Left>", lambda e: self.step_back())
        root.bind("r", lambda e: self.rewind())

        # Load demo by default
        self.load_demo_sequence()

    def _create_controls(self):
        btn_play = ttk.Button(self.toolbar, text="Play ▶", command=self.toggle_play)
        btn_play.pack(side=tk.LEFT, padx=4)
        ttk.Button(self.toolbar, text="Pause ⏸", command=self.pause).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.toolbar, text="Step ▶", command=self.step_forward).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.toolbar, text="Step ◀", command=self.step_back).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.toolbar, text="Rewind ⟲", command=self.rewind).pack(side=tk.LEFT, padx=4)

        ttk.Label(self.toolbar, text="Speed:").pack(side=tk.LEFT, padx=(12,4))
        speed_slider = ttk.Scale(self.toolbar, from_=5, to=200, variable=self.speed_ms, orient=tk.HORIZONTAL)
        speed_slider.pack(side=tk.LEFT, padx=4, ipadx=100)

        ttk.Button(self.toolbar, text="Toggle Grid", command=self.toggle_grid).pack(side=tk.LEFT, padx=8)
        ttk.Button(self.toolbar, text="Load JSON", command=self.load_sequence_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.toolbar, text="Save Snapshot", command=self.save_snapshot).pack(side=tk.LEFT, padx=4)

        self.step_label = ttk.Label(self.toolbar, text="Step: 0 / 0")
        self.step_label.pack(side=tk.RIGHT, padx=6)

    # -------------------------
    # Sequence loading / processing
    # -------------------------
    def load_demo_sequence(self):
        # Compose a mixed demo: diamond grid + spiral
        seq1 = demo_diamond_grid(rows=4, cols=4, spacing=70, offset=(150,120))
        seq2 = demo_spiral_sequence(center=(420,320), spacing=2.5, turns=2, points_per_turn=120)
        # combine
        self.sequence = seq1 + [[0,0,1.0]] + seq2
        self.normalize_sequence()
        self.prepare_abs_positions()
        self._reset_canvas()
        self.draw_grid_dots_from_demo()
        self.update_step_label()

    def load_sequence_file(self):
        path = filedialog.askopenfilename(title="Open stroke JSON", filetypes=[("JSON files","*.json"),("All","*.*")])
        if not path:
            return
        try:
            j = json.load(open(path, 'r'))
            if isinstance(j, dict) and 'seq' in j:
                self.sequence = j['seq']
                # optional dots from file: positions to sparkle around
                self.dots = j.get('dots', [])
            elif isinstance(j, list):
                self.sequence = j
            else:
                messagebox.showerror("Invalid file", "JSON must contain 'seq' (list of [dx,dy,pen]) or be a list of deltas.")
                return
            self.normalize_sequence()
            self.prepare_abs_positions()
            self._reset_canvas()
            self.draw_grid_dots_from_file()
            self.update_step_label()
        except Exception as e:
            messagebox.showerror("Load error", f"Could not load file: {e}")

    def normalize_sequence(self):
        """
        Detect if sequence looks normalized (small dx,dy like [-1..1]) or absolute/pixel deltas.
        If normalized, scale to pixels (assume spacing ~40). If already large, leave as-is.
        """
        if not self.sequence:
            return
        sample = [abs(x) for x,y,p in self.sequence[:min(50,len(self.sequence))]] + [abs(y) for x,y,p in self.sequence[:min(50,len(self.sequence))]]
        avg = sum(sample)/len(sample)
        # if average small (<2), treat as normalized and scale
        if avg < 2.5:
            scale = 40.0
            self.sequence = [[dx*scale, dy*scale, p] for dx,dy,p in self.sequence]

    def prepare_abs_positions(self, start_pos=None):
        """
        Compute absolute positions from deltas for quick animation.
        If stroke deltas are absolute coordinates for stroke starts, handle that too.
        """
        if not self.sequence:
            self.abs_positions = []
            return
        abs_pos = []
        cur_x, cur_y = self.width * 0.25, self.height * 0.3  # default start
        expecting_absolute = False
        # Heuristic: if first delta looks like a coordinate (large), treat as absolute start
        first_dx = abs(self.sequence[0][0])
        if first_dx > 50:
            expecting_absolute = True
        for dx, dy, pen in self.sequence:
            if expecting_absolute:
                # treat dx,dy as absolute coordinates
                nx, ny = dx, dy
                abs_pos.append((nx, ny, pen))
                # next items likely deltas -> compute delta style by making expecting_absolute False
                expecting_absolute = False
                cur_x, cur_y = nx, ny
            else:
                nx = cur_x + dx
                ny = cur_y + dy
                abs_pos.append((nx, ny, pen))
                if pen == 1.0:
                    # pen lift resets current position for next stroke
                    cur_x, cur_y = nx, ny  # keep position; next stroke typically starts with absolute move or big delta
                    cur_x, cur_y = cur_x, cur_y
                    cur_x = cur_x  # no-op to avoid unused
                    # We'll not automatically set to None because sequence usually gives next start as coordinates or big delta
                else:
                    cur_x, cur_y = nx, ny
        self.abs_positions = abs_pos

    # -------------------------
    # Canvas helpers
    # -------------------------
    def _reset_canvas(self):
        self.canvas.delete("all")
        self.drawn_items.clear()
        self.index = 0
        self.playing = False
        self.update_step_label()

    def draw_grid_dots_from_demo(self):
        # If demo used, generate a visible dot grid for tracing effect
        spacing = 70
        offset = (150,120)
        rows = cols = 4
        self.dots = []
        for r in range(rows):
            for c in range(cols):
                x = offset[0] + c*spacing
                y = offset[1] + r*spacing
                self.dots.append((x,y))
        if self.grid_visible.get():
            for (x,y) in self.dots:
                self.canvas.create_oval(x-3,y-3,x+3,y+3, fill="black", tags="grid_dot")

    def draw_grid_dots_from_file(self):
        # Draw dots if loaded from file
        if self.grid_visible.get():
            for (x,y) in self.dots:
                self.canvas.create_oval(x-3,y-3,x+3,y+3, fill="black", tags="grid_dot")

    def toggle_grid(self):
        self.grid_visible.set(not self.grid_visible.get())
        if not self.grid_visible.get():
            self.canvas.delete("grid_dot")
        else:
            # redraw dots
            self.canvas.delete("grid_dot")
            for (x,y) in self.dots:
                self.canvas.create_oval(x-3,y-3,x+3,y+3, fill="black", tags="grid_dot")

    # -------------------------
    # Animation controls
    # -------------------------
    def toggle_play(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def play(self):
        if not self.sequence or not self.abs_positions:
            return
        self.playing = True
        self._animate_step()

    def pause(self):
        self.playing = False

    def rewind(self):
        self.pause()
        # clear strokes and particles, reset index
        for item in self.drawn_items:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        self.drawn_items.clear()
        for p in list(self.particle_items):
            try:
                self.canvas.delete(p)
            except Exception:
                pass
        self.particle_items.clear()
        self.index = 0
        self.update_step_label()

    def step_forward(self):
        if not self.abs_positions:
            return
        if self.index >= len(self.abs_positions):
            return
        # draw this step
        self._draw_at_index(self.index)
        self.index += 1
        self.update_step_label()

    def step_back(self):
        # Removes last drawn element (if any) and steps back one index
        if not self.drawn_items:
            # nothing to undo
            return
        last = self.drawn_items.pop()
        try:
            self.canvas.delete(last)
        except Exception:
            pass
        # attempt to step back index (ensure >=0)
        self.index = max(0, self.index-1)
        self.update_step_label()

    def _animate_step(self):
        if not self.playing:
            return
        if self.index >= len(self.abs_positions):
            self.playing = False
            return
        self._draw_at_index(self.index)
        self.index += 1
        self.update_step_label()
        # schedule next
        delay = int(self.speed_ms.get())
        self.root.after(delay, self._animate_step)

    def _draw_at_index(self, idx):
        # Draws a tiny segment from previous point to this point unless it's a stroke start
        x, y, pen = self.abs_positions[idx]
        # If pen==1, we treat as stroke end and create sparkle effect near this point
        if pen == 1.0:
            # make particles around last known location (if available)
            if idx>0:
                lx, ly, _ = self.abs_positions[idx-1]
                self._create_sparkle_at(lx, ly)
            return
        # find previous drawn coordinate to make a line; skip if idx==0 or previous was pen lift
        prev_x = None; prev_y = None
        if idx > 0:
            px, py, ppen = self.abs_positions[idx-1]
            if ppen != 1.0:
                prev_x, prev_y = px, py
        if prev_x is None:
            # move-to: no visible line, but we can draw a tiny dot as stroke start
            dot = self.canvas.create_oval(x-1.5,y-1.5,x+1.5,y+1.5, fill="black")
            self.drawn_items.append(dot)
        else:
            li = self.canvas.create_line(prev_x, prev_y, x, y, width=2, capstyle=tk.ROUND, smooth=True)
            self.drawn_items.append(li)

    # -------------------------
    # Sparkle particle effect
    # -------------------------
    def _create_sparkle_at(self, x, y, n_particles=10, speed=5, lifetime=600):
        # create n_particles small circles that expand and fade
        particles = []
        for i in range(n_particles):
            angle = random.random() * 2*math.pi
            dx = math.cos(angle) * (random.random()*speed + 1)
            dy = math.sin(angle) * (random.random()*speed + 1)
            size = random.uniform(2, 5)
            color = "#%02x%02x%02x" % (random.randint(180,255), random.randint(140,255), random.randint(100,255))
            pid = self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline="")
            particles.append({"id": pid, "vx": dx, "vy": dy, "age": 0, "size": size})
            self.particle_items.append(pid)
        # Animate particles frame-by-frame using after
        start_time = time.time()
        def step():
            remove = []
            for p in particles:
                # move
                self.canvas.move(p["id"], p["vx"], p["vy"])
                # grow slightly and fade by adjusting alpha-like by recoloring to near-white
                p["age"] += 40  # ms-ish
                sx = p["size"] * (1 + p["age"]/800.0)
                # we can't change alpha easily; instead shrink color saturation
                if p["age"] > lifetime:
                    remove.append(p)
            for p in remove:
                try:
                    self.canvas.delete(p["id"])
                    self.particle_items.remove(p["id"])
                except Exception:
                    pass
                particles.remove(p)
            if particles:
                self.root.after(40, step)
        step()

    # -------------------------
    # Save snapshot of canvas
    # -------------------------
    def save_snapshot(self):
        # Save canvas region to a PNG file (uses ImageGrab)
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if not path:
            return
        try:
            img = ImageGrab.grab().crop((x, y, x1, y1))
            img.save(path)
            messagebox.showinfo("Saved", f"Snapshot saved to {path}")
        except Exception as e:
            messagebox.showerror("Save error", f"Could not save snapshot: {e}")

    def update_step_label(self):
        total = len(self.abs_positions) if self.abs_positions else 0
        self.step_label.config(text=f"Step: {self.index} / {total}")

# -------------------------
# Main
# -------------------------
def main():
    root = tk.Tk()
    app = KolamAnimator(root)
    root.geometry("1000x700")
    root.mainloop()

if __name__ == "__main__":
    main()
