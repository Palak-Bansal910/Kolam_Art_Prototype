import matplotlib.pyplot as plt

def generate_dot_grid(rows, cols, spacing=1):
    dots = []
    for i in range(rows):
        for j in range(cols):
            dots.append((j*spacing, i*spacing))
    return dots

def draw_kolam(rows=5, cols=5, spacing=1):
    dots = generate_dot_grid(rows, cols, spacing)
    x, y = zip(*dots)

    plt.figure(figsize=(6,6))
    plt.scatter(x, y, color="black", s=30)

    # Example: connect dots in a diamond pattern
    for (x, y) in dots:
        if (x+spacing, y+spacing) in dots:
            plt.plot([x, x+spacing], [y, y+spacing], 'b')
        if (x-spacing, y+spacing) in dots:
            plt.plot([x, x-spacing], [y, y+spacing], 'r')

    plt.axis("equal")
    plt.axis("off")
    plt.show()

draw_kolam()
import matplotlib.pyplot as plt
import numpy as np

def kolam_circle(rows=5, cols=5, spacing=2, radius=0.8):
    plt.figure(figsize=(6,6))
    
    for i in range(rows):
        for j in range(cols):
            x, y = j*spacing, i*spacing
            circle = plt.Circle((x,y), radius, fill=False, color="blue")
            plt.gca().add_patch(circle)

    plt.axis("equal")
    plt.axis("off")
    plt.show()

kolam_circle()
