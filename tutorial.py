import os
import matplotlib.pyplot as plt

def create_kolam_design(save_path, rows=5, cols=5, spacing=1):
    os.makedirs(save_path, exist_ok=True)

    dots = [(j*spacing, i*spacing) for i in range(rows) for j in range(cols)]

    plt.figure(figsize=(6,6))
    plt.axis("equal")
    plt.axis("off")

    # Step 1: plot dots
    x, y = zip(*dots)
    plt.scatter(x, y, color="black", s=30)
    plt.savefig(os.path.join(save_path, "step_01.png"), bbox_inches='tight')
    
    # Step 2: add diagonal connections
    for (x,y) in dots:
        if (x+spacing, y+spacing) in dots:
            plt.plot([x, x+spacing], [y, y+spacing], 'b')
    plt.savefig(os.path.join(save_path, "step_02.png"), bbox_inches='tight')

    # Step 3: add other symmetry lines
    for (x,y) in dots:
        if (x-spacing, y+spacing) in dots:
            plt.plot([x, x-spacing], [y, y+spacing], 'r')
    plt.savefig(os.path.join(save_path, "step_03.png"), bbox_inches='tight')

    # Step 4: final
    plt.savefig(os.path.join(save_path, "final.png"), bbox_inches='tight')
    plt.close()

# Generate dataset
dataset_root = "Kolam_Dataset"
for i in range(1, 6):   # 5 designs
    create_kolam_design(os.path.join(dataset_root, f"design_{i}"))
