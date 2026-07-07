"""
Create the data directory structure for the fracture toughness prediction project.

This script ensures the existence of the following directories under `data/`:
- data/raw: For storing raw input images and metadata.
- data/processed: For storing standardized, preprocessed datasets.
- data/explainability: For storing Grad-CAM heatmaps and stability reports.

This implements task T004a.
"""

import os
import sys

def main():
    """Create the required data directory structure."""
    base_dir = "data"
    directories = [
        os.path.join(base_dir, "raw"),
        os.path.join(base_dir, "processed"),
        os.path.join(base_dir, "explainability"),
    ]

    created = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created == 0:
        print("No new directories created. All required directories exist.")
    else:
        print(f"Successfully created {created} new directory/directories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())