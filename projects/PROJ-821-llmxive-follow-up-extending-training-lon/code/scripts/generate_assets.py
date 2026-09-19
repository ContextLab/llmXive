"""
Script to generate fixed 336x336 geometric gradient images for synthetic data.

Generates 20 deterministic grayscale linear gradients using seed=42.
Images serve as valid references for the vision-language model.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image, ImageDraw

# Set seed for deterministic behavior (though gradients are formulaic)
import random
random.seed(42)

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def ensure_dirs() -> Path:
    """Ensure the assets directory exists and return its path."""
    root = get_project_root()
    assets_dir = root / "data" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_technical_diagram(idx: int, output_path: Path) -> None:
    """
    Create a single 336x336 image with a linear grayscale gradient.
    
    The gradient goes from black (0,0) to white (335,335).
    This satisfies the requirement for "linear grayscale gradients from black to white".
    
    Args:
        idx: Image index (0-19) used for deterministic variation in metadata.
        output_path: Path to save the image.
    """
    width, height = 336, 336
    
    # Create a new image in 'L' mode (grayscale)
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    
    # Draw a linear gradient from black (0) to white (255)
    # We iterate through rows and set the color based on the row index
    # to create a vertical linear gradient, or mix x and y for diagonal.
    # Requirement: "linear grayscale gradients from black to white (e.g., from (0,0) to (...))"
    # Let's do a diagonal gradient for visual distinctness and simplicity.
    # Value = (x + y) / (width + height) * 255
    
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            # Calculate intensity: 0 at (0,0), 255 at (335, 335)
            # Normalize sum of coordinates to [0, 1]
            max_sum = (width - 1) + (height - 1)
            current_sum = x + y
            intensity = int((current_sum / max_sum) * 255)
            pixels[x, y] = intensity
    
    # Save image
    img.save(output_path, "PNG")

def generate_assets() -> Dict[str, Any]:
    """
    Generate all 20 fixed images and create manifest.
    
    Returns:
        Dictionary containing manifest data.
    """
    assets_dir = ensure_dirs()
    manifest = {
        "count": 0,
        "images": []
    }
    
    for i in range(20):
        filename = f"img_{i:02d}.png"
        filepath = assets_dir / filename
        
        create_technical_diagram(i, filepath)
        
        sha_hash = compute_sha256(filepath)
        # Verify dimensions
        with Image.open(filepath) as img:
            w, h = img.size
            assert w == 336 and h == 336, f"Image {filename} has wrong dimensions: {w}x{h}"
        
        manifest["images"].append({
            "filename": filename,
            "sha256": sha_hash,
            "size_bytes": filepath.stat().st_size,
            "dimensions": [336, 336]
        })
        manifest["count"] += 1
            
    # Save manifest
    manifest_path = assets_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    return manifest

def main() -> None:
    """Main entry point for asset generation."""
    print("Generating 20 fixed 336x336 grayscale gradient images...")
    try:
        manifest = generate_assets()
        print(f"Successfully generated {manifest['count']} images.")
        print(f"Manifest saved to: {get_project_root() / 'data' / 'assets' / 'manifest.json'}")
    except Exception as e:
        print(f"Error generating assets: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()