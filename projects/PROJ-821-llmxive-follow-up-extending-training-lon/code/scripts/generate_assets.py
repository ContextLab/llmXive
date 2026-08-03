"""
Script to generate fixed technical manual style diagrams for synthetic data.

Generates 20 fixed 336x336 images using Pillow. Images are grayscale gradients
with OCR-readable text labels to simulate complexity uniformly.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont

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

def create_technical_diagram(idx: int, output_path: Path, font_path: str) -> None:
    """
    Create a single technical manual style diagram.
    
    Args:
        idx: Image index (0-19) used for deterministic variation.
        output_path: Path to save the image.
        font_path: Path to a standard font file.
    """
    # Fixed resolution
    width, height = 336, 336
    
    # Create white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a standard font, fallback to default if not found
    try:
        # Common font paths for Linux/Mac/Windows
        font_paths = [
            font_path,
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, 14)
                break
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Draw a gradient-like background pattern (grayscale steps)
    # Simulate technical manual complexity
    for y in range(0, height, 16):
        shade = int(240 - (y / height) * 100)
        draw.rectangle([(0, y), (width, y + 16)], fill=(shade, shade, shade))
    
    # Draw grid lines
    for x in range(0, width, 24):
        draw.line([(x, 0), (x, height)], fill=(200, 200, 200), width=1)
    for y in range(0, height, 24):
        draw.line([(0, y), (width, y)], fill=(200, 200, 200), width=1)
    
    # Add text labels (OCR-readable)
    label_text = f"FIGURE {idx + 1:02d} - DIAGRAM"
    text_bbox = draw.textbbox((0, 0), label_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center text at top
    x = (width - text_width) // 2
    y = 20
    draw.text((x, y), label_text, fill='black', font=font)
    
    # Add specific component labels based on index for variation
    components = [
        "VALVE A", "VALVE B", "PUMP X", "PUMP Y", "SENSOR 1",
        "SENSOR 2", "GAUGE 1", "GAUGE 2", "MOTOR 1", "MOTOR 2",
        "CIRCUIT A", "CIRCUIT B", "BATTERY 1", "BATTERY 2", "RELAY 1",
        "RELAY 2", "SWITCH 1", "SWITCH 2", "FUSE 1", "FUSE 2"
    ]
    
    comp_label = components[idx % len(components)]
    draw.text((10, height - 30), comp_label, fill='black', font=font)
    
    # Draw some geometric shapes to add complexity
    # Box
    draw.rectangle([50, 50, 150, 100], outline='black', width=2)
    # Circle
    draw.ellipse([200, 50, 250, 100], outline='black', width=2)
    # Line
    draw.line([(150, 75), (200, 75)], fill='black', width=2)
    
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
        
        create_technical_diagram(i, filepath, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        
        sha_hash = compute_sha256(filepath)
        manifest["images"].append({
            "filename": filename,
            "sha256": sha_hash,
            "size_bytes": filepath.stat().st_size
        })
        manifest["count"] += 1
        
    # Save manifest
    manifest_path = assets_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    return manifest

def main() -> None:
    """Main entry point for asset generation."""
    print("Generating technical manual assets...")
    try:
        manifest = generate_assets()
        print(f"Successfully generated {manifest['count']} images.")
        print(f"Manifest saved to: {get_project_root() / 'data' / 'assets' / 'manifest.json'}")
    except Exception as e:
        print(f"Error generating assets: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()