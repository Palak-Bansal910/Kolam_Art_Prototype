# kolam_data.py
import math, random, json, os
import numpy as np
from svgwrite import Drawing  # pip install svgwrite

def make_dot_grid(rows, cols, spacing):
    dots = []
    for r in range(rows):
        for c in range(cols):
            dots.append((c*spacing, r*spacing))
    return dots

def line_points(p1, p2, n=20):
    x1,y1 = p1; x2,y2 = p2
    return [(x1 + (x2-x1)*t/(n-1), y1 + (y2-y1)*t/(n-1)) for t in range(n)]

def bezier_cubic(p0, p1, p2, p3, steps=30):
    pts = []
    for i in range(steps):
        t = i/(steps-1)
        a = (1-t)**3
        b = 3*(1-t)**2 * t
        c = 3*(1-t)*t**2
        d = t**3
        x = a*p0[0] + b*p1[0] + c*p2[0] + d*p3[0]
        y = a*p0[1] + b*p1[1] + c*p2[1] + d*p3[1]
        pts.append((x,y))
    return pts

def pattern_diamond(rows, cols, spacing, jitter=0.0):
    dots = make_dot_grid(rows, cols, spacing)
    strokes = []
    for (cx,cy) in dots:
        # diamond around each dot
        r = spacing*0.4
        pnts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy), (cx, cy-r)]
        stroke = []
        for a,b in zip(pnts[:-1], pnts[1:]):
            stroke += line_points(a,b,n=12)
        strokes.append(stroke)
    return strokes, dots

def pattern_spiral(center, turns=3, points_per_turn=80, spacing=4):
    cx,cy = center
    points = []
    for i in range(turns*points_per_turn):
        t = i/(points_per_turn)
        angle = 2*math.pi*t/points_per_turn
        rad = spacing * angle / (2*math.pi)
        x = cx + rad*math.cos(angle)
        y = cy + rad*math.sin(angle)
        points.append((x,y))
    return [points]

def strokes_to_deltas(strokes):
    """strokes: list of list of (x,y). returns a single sequence of (dx,dy,pen) items"""
    seq = []
    last_x, last_y = None, None
    for stroke in strokes:
        for (x,y) in stroke:
            if last_x is None:
                dx,dy = x, y
            else:
                dx,dy = x-last_x, y-last_y
            seq.append([dx,dy,0.0])  # pen=0 during stroke
            last_x, last_y = x, y
        # pen lift at end of stroke
        seq.append([0.0,0.0,1.0])
        last_x, last_y = None, None
    return seq

def generate_dataset(out_dir="data_kolam", n=200, grid=(5,5), spacing=40):
    os.makedirs(out_dir, exist_ok=True)
    meta = []
    for i in range(n):
        # pick generator randomly
        g = random.choice(["diamond","spiral"])
        if g=="diamond":
            strokes, dots = pattern_diamond(grid[0], grid[1], spacing)
            label = "diamond_grid"
        else:
            # spiral at center of canvas
            center = ((grid[1]-1)*spacing/2, (grid[0]-1)*spacing/2)
            strokes = pattern_spiral(center, turns=random.choice([2,3,4]))
            dots = make_dot_grid(grid[0], grid[1], spacing)

        seq = strokes_to_deltas(strokes)
        # normalize by spacing
        seq_n = [[dx/spacing, dy/spacing, pen] for dx,dy,pen in seq]
        fn = f"kolam_{i:04d}.json"
        with open(os.path.join(out_dir,fn),'w') as f:
            json.dump({"seq": seq_n, "label": label, "dots": dots}, f)
        meta.append(fn)
    # save meta
    with open(os.path.join(out_dir,"meta.json"),"w") as f:
        json.dump(meta,f)
    print("Generated", n, "examples in", out_dir)

if __name__ == "__main__":
    generate_dataset(n=500)
