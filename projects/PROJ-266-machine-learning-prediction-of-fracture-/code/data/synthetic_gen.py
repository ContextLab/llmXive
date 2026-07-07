"""
Synthetic Microstructure Generator for Fracture Toughness Prediction.

Generates >= 2,000 synthetic microstructure images with physics-informed
K_IC (fracture toughness) values based on simulated grain structures.

Output:
  - data/raw/synthetic_microstructures_*.png
  - data/raw/synthetic_metadata.json
"""

import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random
import argparse
from pathlib import Path

# Ensure reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Configuration
NUM_SAMPLES = 2500  # Exceeds the >= 2000 requirement
IMAGE_SIZE = 128    # Standardized size for downstream processing
OUTPUT_DIR = Path("data/raw")
METADATA_FILE = OUTPUT_DIR / "synthetic_metadata.json"

# Physics-informed parameters (approximate ranges for common alloys)
# K_IC ranges in MPa√m:
# Aluminum alloys: 20 - 40
# Steel alloys: 50 - 150
# Titanium alloys: 50 - 120
ALLOY_FAMILIES = {
    "Al": {"min_k": 20.0, "max_k": 40.0, "color": (200, 200, 200)},
    "Steel": {"min_k": 50.0, "max_k": 150.0, "color": (100, 100, 100)},
    "Ti": {"min_k": 50.0, "max_k": 120.0, "color": (180, 180, 180)}
}

def generate_grain_structure(size: int, num_grains: int, seed: int) -> np.ndarray:
    """
    Generates a synthetic microstructure image using a Voronoi-like approach
    to simulate grain boundaries.
    """
    np.random.seed(seed)
    img = np.zeros((size, size), dtype=np.uint8)
    draw = ImageDraw.ImageDraw(Image.fromarray(img))

    # Generate random grain centers
    centers = [(random.randint(0, size - 1), random.randint(0, size - 1)) for _ in range(num_grains)]

    # Assign random colors/grayscale values to grains
    grain_values = [random.randint(50, 200) for _ in range(num_grains)]

    # Create a rough Voronoi-like segmentation by distance
    # For efficiency in pure Python/PIL, we simulate grain shapes with polygons
    # or simply fill regions from centers outward.
    # A simpler, robust method for synthetic data: Random polygons.
    
    # Create a blank image for drawing
    pil_img = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(pil_img)

    for i, center in enumerate(centers):
        # Random grain size
        radius = random.randint(5, 15)
        # Random shape variation
        points = []
        for angle in np.linspace(0, 2 * np.pi, 8):
            r = radius * (0.8 + 0.4 * np.random.rand())
            x = int(center[0] + r * np.cos(angle))
            y = int(center[1] + r * np.sin(angle))
            points.append((x, y))
        
        draw.polygon(points, fill=grain_values[i])
    
    # Add some noise to simulate real imaging
    np_img = np.array(pil_img)
    noise = np.random.normal(0, 5, np_img.shape).astype(np.int16)
    np_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return np_img

def calculate_physics_informed_k_ic(alloy_family: str, microstructure_params: dict) -> float:
    """
    Calculates K_IC based on alloy family and microstructure parameters.
    
    Physics-informed logic:
    - Grain size (d): Hall-Petch relationship (K_IC ~ k * d^(-1/2))
    - Porosity: Reduces toughness
    - Precipitate density: Can increase or decrease depending on mechanism
    """
    base_range = ALLOY_FAMILIES[alloy_family]
    base_k = (base_range["min_k"] + base_range["max_k"]) / 2.0
    
    # Hall-Petch effect: Smaller grains -> Higher toughness (simplified)
    grain_size = microstructure_params["grain_size"] # pixels
    hp_factor = 1.0 + (20.0 / max(grain_size, 1)) # Normalize around 20px
    
    # Porosity effect: Higher porosity -> Lower toughness
    porosity = microstructure_params["porosity"]
    porosity_factor = 1.0 - (porosity * 0.5) # Up to 50% reduction at max porosity
    
    # Combine factors
    calculated_k = base_k * hp_factor * porosity_factor
    
    # Clamp to physical limits
    calculated_k = max(base_range["min_k"], min(base_range["max_k"], calculated_k))
    
    return round(calculated_k, 2)

def main():
    """
    Main execution function to generate synthetic dataset.
    """
    print(f"Starting synthetic microstructure generation...")
    print(f"Target samples: {NUM_SAMPLES}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata_records = []
    
    for i in range(NUM_SAMPLES):
        # 1. Select Alloy Family (stratified roughly)
        alloy_family = random.choice(list(ALLOY_FAMILIES.keys()))
        
        # 2. Generate Microstructure Parameters
        num_grains = random.randint(10, 30)
        grain_size = random.uniform(5.0, 20.0) # Simulated pixel scale
        porosity = random.uniform(0.0, 0.15)   # 0% to 15%
        resolution_um = random.uniform(0.5, 2.0) # um/pixel
        
        # 3. Generate Image
        seed_val = i + RANDOM_SEED
        img_array = generate_grain_structure(IMAGE_SIZE, num_grains, seed_val)
        
        # 4. Calculate Physics-Informed K_IC
        k_ic = calculate_physics_informed_k_ic(alloy_family, {
            "grain_size": grain_size,
            "porosity": porosity
        })
        
        # 5. Save Image
        img_filename = f"synthetic_microstructure_{i:04d}.png"
        img_path = OUTPUT_DIR / img_filename
        
        # Save as grayscale PNG
        img_pil = Image.fromarray(img_array, mode='L')
        img_pil.save(img_path)
        
        # 6. Record Metadata
        record = {
            "id": i,
            "filename": img_filename,
            "alloy_family": alloy_family,
            "k_ic_mpa_sqrtm": k_ic,
            "microstructure_params": {
                "num_grains": num_grains,
                "grain_size_um": grain_size, # Approximate mapping
                "porosity": porosity,
                "resolution_um": resolution_um,
                "preparation_protocol": "SEM" if random.random() > 0.5 else "TEM"
            },
            "seed": seed_val
        }
        metadata_records.append(record)
        
        if (i + 1) % 500 == 0:
            print(f"Generated {i + 1} / {NUM_SAMPLES} samples...")

    # Save Metadata JSON
    with open(METADATA_FILE, 'w') as f:
        json.dump({
            "version": "1.0",
            "total_samples": len(metadata_records),
            "generation_seed": RANDOM_SEED,
            "records": metadata_records
        }, f, indent=2)
    
    print(f"Generation complete.")
    print(f"Total images saved: {len(metadata_records)}")
    print(f"Metadata saved to: {METADATA_FILE}")
    
    # Verification Step
    if len(metadata_records) < 2000:
        print(f"ERROR: Generated {len(metadata_records)} samples, expected >= 2000.")
        return 1
    else:
        print(f"VERIFICATION PASSED: Generated {len(metadata_records)} samples (>= 2000).")
        return 0

if __name__ == "__main__":
    exit(main())
