import tkinter as tk 
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk, ImageOps, ImageGrab
import json
import os

class KolamArtApp:
    def __init__(self,root):
        self.root = root
        self.root.title("Kolam Art Canvas")
        self.brush_colour = "black"
        self.brush_size = 5
        self.background_color = "white"
        self.drawing_mode = "draw"
        self.last_x, self.last_y = None,None
        self.actions = []

        #Canvas
        self.canvas = tk.Canvas(root, width = 800, height = 600, bg= self.background_color)
        self.canvas.pack(fill=tk.BOTH, expand =True)

        #Toolbar
        toolbar = tk.Frame(root)
        toolbar.pack(fill = tk.Y)
        tk.Button(toolbar, text = "Pencil", command = self.use_pencil).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Brush", command = self.use_brush).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Highlighter", command = self.use_highlighter).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Color", command = self.choose_color).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Eraser", command = self.use_eraser).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Undo", command = self.undo).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Save", command = self.save_canvas).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Size", command = self.choose_size).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Dot", command = self.draw_dot).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Triangle", command = self.draw_triangle).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Square", command = self.draw_square).pack(side=tk.LEFT)
        tk.Button(toolbar, text = "Circle", command = self.draw_circle).pack(side=tk.LEFT)
        tk.Button(toolbar, text="Show/Hide Grid", command=self.toggle_grid).pack(side=tk.LEFT)
        #Bind Mouse Events
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>",self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

    def use_pencil(self):
        self.brush_size = 2
        self.brush_color= self.brush_color
    def use_brush(self):
        self.brush_size = 5
        self.brush_color = self.brush_color

    def use_highlighter(self):
        self.brush_size =15
        self.brush_color = self.background_color

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.brush_color = color
            self.drawing_mode = "draw"
        background = colorchooser.askcolor()[1]
        if background:
            self.background_color = background
            self.canvas.config(bg=self.background_color)
    def draw_grid(self, spacing=40):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        for x in range(spacing, width, spacing):
            for y in range(spacing, height, spacing):
                dot = self.canvas.create_oval(x-2, y-2, x+2, y+2, fill="black")
                self.grid_dots.append(dot)
    def toggle_grid(self):
        if self.grid_visible:
            # Hide grid
            for dot in self.grid_dots:
                self.canvas.delete(dot)
            self.grid_dots.clear()
            self.grid_visible = False
        else:
            # Show grid
            self.draw_grid(spacing=40)  # You can adjust spacing
            self.grid_visible = True
    
    def use_eraser(self):
        self.drawing_mode = "erase"
        self.brush_color = self.background_color
        self.brush_size = 20
    def draw_dot(self):
        x,y = self.canvas.winfo_pointerxy()
        dot = self.canvas.create_oval(x,y, x+self.brush_size,y+self.brush_size, fill = self.background_color, outline = self.brush_color, width = self.brush_size)
        self.actions.append(dot)
    def draw_triangle(self):
        x,y = self.canvas.winfo_pointerxy()
        half_size = self.brush_size /2
        points = [x,y - half_size, x - half_size, y + half_size, x + half_size]
        triangle = self.canvas.create_polygon(points, fill = self.brush_color, outline = self.brush_color)
        self.actions.append(triangle)
    def draw_square(self):
        x,y = self.canvas.winfo_pointerxy()
        half_size = self.brush_size /2
        points = [x - half_size, y - half_size, x + half_size, y - half_size, x + half_size, y + half_size, x - half_size, y + half_size]
        square = self.canvas.create_polygon(points, fill = self.brush_color, outline = self.brush_color)
        self.actions.append(square)
    def draw_circle(self):
        x,y = self.canvas.winfo_pointerxy()
        half_size = self.brush_size /2
        circle = self.canvas.create_oval(x- half_size, y - half_size, x + half_size, y + half_size, fill = self.brush_color, outline = self.brush_color)
        self.actions.append(circle)
    def undo(self):
        if self.actions:
            last_action = self.actions.pop()
            self.canvas.delete(last_action)

    def save_canvas(self):
        #Save the canvas as an image
        x= self.root.winfo_rootx() + self.canvas.winfo_x()
        y= self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        filepath = filedialog.asksaveasfilename(defaultextension =".png", filetypes=[("PNG files","*.png")])
        if filepath:
            ImageGrab.grab().crop((x,y,x1,y1)).save(filepath)
            messagebox.showinfo("Save", f"Canvas saved as {os.path.basename(filepath)}")
    def reset(self,event):
        self.last_x, self.last_y = None,None

    def choose_size(self):
        size = tk.simpledialog.askinteger("Brush Size", "Enter brush size (1-100):", minvalue=1, maxvalue=100)
        if size:
            self.brush_size = size
    def start_draw(self,event):
        self.last_x, self.last_y = event.x, event.y
    def draw(self, event):
        if self.last_x and self.last_y:
            if self.drawing_mode == "draw":
                line = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width=self.brush_size, fill = self.brush_color, capstyle= tk.ROUND, smooth = True)
                self.actions.append(line)
                self.last_x, self.last_y = event.x, event.y
            elif self.drawing_mode == "erase":
                eraser = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, width= self.brush_size, fill = self.brush_color, capstyle = tk.ROUND, smooth = True)
                self.actions.append(eraser)
                self.last_x, self.last_y = event.x, event.y

if __name__ =="__main__":
    root = tk.Tk()
    app = KolamArtApp(root)
    root.mainloop()

    






        

        


