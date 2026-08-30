import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure deterministic behavior for reproducibility
def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)

def generate_grain_structure(
    width: int = 128,
    height: int = 128,
    num_grains: int = 15,
    grain_size_min: int = 10,
    grain_size_max: int = 40,
    seed: int = 42
) -> Image.Image:
    """
    Generates a synthetic microstructure image simulating polycrystalline grain boundaries.
    Uses Voronoi-like segmentation with smoothed boundaries to mimic real metallography.
    """
    set_seed(seed)
    
    # Create blank image
    img = Image.new('L', (width, height), color=128)
    draw = ImageDraw.Draw(img)
    
    # Generate random seed points for grains
    points = []
    for _ in range(num_grains):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        points.append((x, y))
    
    # Create a numpy array to store grain IDs
    grid = np.zeros((height, width), dtype=int) - 1
    
    # Assign each pixel to the nearest seed point (Voronoi)
    for y in range(height):
        for x in range(width):
            min_dist = float('inf')
            nearest_idx = 0
            for idx, (px, py) in enumerate(points):
                dist = (x - px)**2 + (y - py)**2
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = idx
            grid[y, x] = nearest_idx
    
    # Assign random grayscale values to each grain
    grain_values = [random.randint(50, 200) for _ in range(num_grains)]
    for y in range(height):
        for x in range(width):
            grain_id = grid[y, x]
            img.putpixel((x, y), grain_values[grain_id])
    
    # Apply Gaussian blur to soften boundaries and simulate optical resolution limits
    # Resolution limit assumption: 0.5 um per pixel, kernel simulates ~2-3 um blur
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    
    return img

def calculate_physics_informed_k_ic(
    img: Image.Image,
    grain_count: int,
    avg_grain_size: float,
    alloy_family: str
) -> float:
    """
    Calculates a physics-informed fracture toughness (K_IC) value based on:
    1. Hall-Petch relationship: K_IC ~ k * d^(-0.5) (finer grains -> higher toughness)
    2. Alloy family specific constants (Steel > Ti > Al in typical toughness)
    3. Microstructural complexity factor (grain count variance)
    
    Returns K_IC in MPa√m
    """
    # Base constants by alloy family (approximate real-world ranges)
    base_constants = {
        'steel': 60.0,   # Typical structural steel range
        'al': 25.0,      # Aluminum alloys
        'ti': 45.0       # Titanium alloys
    }
    
    if alloy_family not in base_constants:
        alloy_family = 'steel'
    
    base_k = base_constants[alloy_family]
    
    # Hall-Petch effect: finer grains increase toughness
    # K_IC = K_0 + k_y * d^(-0.5)
    # Simplified: higher grain count (finer microstructure) -> higher K_IC
    grain_factor = 1.0 + (0.5 * (1.0 / (avg_grain_size + 1e-6)))
    
    # Complexity factor: more uniform grain size distribution -> higher toughness
    # (simulated by random noise around expected value)
    complexity_noise = random.gauss(0, 0.05)
    
    # Calculate final K_IC
    k_ic = base_k * grain_factor * (1.0 + complexity_noise)
    
    # Clamp to physically realistic ranges (MPa√m)
    min_k = 15.0
    max_k = 120.0
    k_ic = max(min_k, min(max_k, k_ic))
    
    return round(k_ic, 2)

def generate_dataset(
    output_dir: str,
    num_images: int = 2000,
    img_size: int = 128,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generates a synthetic dataset of microstructure images with physics-informed K_IC values.
    Saves images as PNG and metadata as JSON.
    """
    set_seed(seed)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata = []
    alloy_families = ['steel', 'al', 'ti']
    
    print(f"Generating {num_images} synthetic microstructure images...")
    
    for i in range(num_images):
        # Randomize microstructure parameters
        num_grains = random.randint(10, 30)
        grain_size_min = random.randint(8, 15)
        grain_size_max = random.randint(25, 45)
        alloy_family = random.choice(alloy_families)
        
        # Generate image
        img = generate_grain_structure(
            width=img_size,
            height=img_size,
            num_grains=num_grains,
            grain_size_min=grain_size_min,
            grain_size_max=grain_size_max,
            seed=seed + i
        )
        
        # Calculate average grain size (approximate)
        avg_grain_size = (grain_size_min + grain_size_max) / 2.0
        
        # Calculate physics-informed K_IC
        k_ic = calculate_physics_informed_k_ic(
            img, num_grains, avg_grain_size, alloy_family
        )
        
        # Save image
        filename = f"image_{i+1:04d}.png"
        img_path = output_path / filename
        img.save(img_path, "PNG")
        
        # Record metadata
        meta_entry = {
            "image_id": f"image_{i+1:04d}",
            "filename": filename,
            "alloy_family": alloy_family,
            "k_ic": k_ic,
            "num_grains": num_grains,
            "grain_size_min": grain_size_min,
            "grain_size_max": grain_size_max,
            "image_size": img_size
        }
        metadata.append(meta_entry)
        
        if (i + 1) % 500 == 0:
            print(f"  Generated {i+1}/{num_images} images...")
    
    # Save metadata
    metadata_path = output_path / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Dataset generation complete.")
    print(f"  Images saved to: {output_path}")
    print(f"  Metadata saved to: {metadata_path}")
    print(f"  Total images: {len(metadata)}")
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic microstructure dataset")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory for images and metadata")
    parser.add_argument("--num-images", type=int, default=2000, help="Number of images to generate")
    parser.add_argument("--img-size", type=int, default=128, help="Image size (width and height)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    generate_dataset(
        output_dir=args.output,
        num_images=args.num_images,
        img_size=args.img_size,
        seed=args.seed
    )

if __name__ == "__main__":
    main()