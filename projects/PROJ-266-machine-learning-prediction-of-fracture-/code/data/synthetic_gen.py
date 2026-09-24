import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import existing config and logger utilities
from code.utils.config import get_config_dict
from code.utils.logger import get_logger

logger = get_logger(__name__)
CONFIG = get_config_dict()

# Constants for synthetic generation
NUM_IMAGES = 2000
IMAGE_SIZE = 128
ALLOY_FAMILIES = ['steel', 'Al', 'Ti']

# Parameters for K_IC formula (synthetic ground truth)
# K_IC = base_value + alpha * grain_size + beta * precipitate_density + noise
K_IC_PARAMS = {
    'steel': {'base_value': 45.0, 'alpha': 0.5, 'beta': -0.3},
    'Al': {'base_value': 25.0, 'alpha': 0.3, 'beta': -0.2},
    'Ti': {'base_value': 60.0, 'alpha': 0.6, 'beta': -0.4}
}
NOISE_STD = 2.0

def generate_sample_metadata(index: int, alloy_family: str) -> Dict[str, Any]:
    """Generate metadata for a single sample including sample preparation parameters."""
    # Sample preparation metadata (T053 logic)
    magnification_calibration = random.uniform(1000, 5000)  # pixels/micron
    section_thickness = random.uniform(10, 50)  # nm
    
    # Grain structure parameters
    grain_size = random.uniform(5, 50)  # microns
    num_grains = random.randint(20, 100)
    precipitate_density = random.uniform(0.1, 0.8)
    
    # Calculate synthetic K_IC using formula from research.md Section 3.2
    params = K_IC_PARAMS[alloy_family]
    noise = np.random.normal(0, NOISE_STD)
    k_ic = params['base_value'] + params['alpha'] * grain_size + params['beta'] * precipitate_density + noise
    
    metadata = {
        'image_id': f'sample_{index:05d}',
        'alloy_family': alloy_family,
        'magnification_calibration': round(magnification_calibration, 2),
        'section_thickness': round(section_thickness, 2),
        'grain_size': round(grain_size, 2),
        'num_grains': num_grains,
        'precipitate_density': round(precipitate_density, 3),
        'k_ic': round(k_ic, 3),
        'noise': round(noise, 3)
    }
    
    return metadata

def generate_grain_structure(
    width: int, 
    height: int, 
  num_grains: int, 
    grain_size: float,
    alloy_family: str
) -> Image.Image:
    """Generate a synthetic microstructure image with grain boundaries."""
    # Create base image
    img = Image.new('L', (width, height), color=200)
    draw = ImageDraw.Draw(img)
    
    # Generate grain centers
    centers = []
    for _ in range(num_grains):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        centers.append((x, y))
    
    # Draw grains using Voronoi-like approximation with circles
    grain_colors = [random.randint(150, 220) for _ in range(num_grains)]
    
    for i, (cx, cy) in enumerate(centers):
        # Radius based on grain_size parameter
        radius = max(5, int(grain_size * random.uniform(0.5, 1.5)))
        radius = min(radius, min(width, height) // 2)
        
        # Draw grain
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=grain_colors[i],
            outline=grain_colors[i] - 20 if grain_colors[i] > 20 else 0
        )
    
    # Add precipitates based on density
    img_array = np.array(img)
    precipitate_count = int(num_grains * 0.5)
    for _ in range(precipitate_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        size = random.randint(1, 3)
        img_array[y:y+size, x:x+size] = random.randint(50, 100)
    
    # Apply slight blur to simulate imaging
    img = Image.fromarray(img_array)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return img

def calculate_physics_informed_k_ic(
    alloy_family: str, 
    grain_size: float, 
    precipitate_density: float
) -> float:
    """Calculate K_IC using the formula from research.md Section 3.2."""
    params = K_IC_PARAMS[alloy_family]
    noise = np.random.normal(0, NOISE_STD)
    k_ic = params['base_value'] + params['alpha'] * grain_size + params['beta'] * precipitate_density + noise
    return k_ic

def generate_dataset(
    output_dir: str = 'data/raw',
    num_images: int = NUM_IMAGES,
    image_size: int = IMAGE_SIZE
) -> List[Dict[str, Any]]:
    """Generate synthetic microstructure dataset with ground truth K_IC values."""
    logger.info(f"Starting synthetic dataset generation: {num_images} images")
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    metadata_list = []
    
    # Ensure at least one sample per alloy family
    alloy_distribution = []
    for family in ALLOY_FAMILIES:
        alloy_distribution.append(family)
    
    # Fill remaining with random distribution
    remaining = num_images - len(ALLOY_FAMILIES)
    for _ in range(remaining):
        alloy_distribution.append(random.choice(ALLOY_FAMILIES))
    
    # Shuffle to randomize order
    random.shuffle(alloy_distribution)
    
    for i, alloy_family in enumerate(alloy_distribution):
        # Generate metadata first to get parameters
        meta = generate_sample_metadata(i, alloy_family)
        metadata_list.append(meta)
        
        # Generate image using parameters from metadata
        img = generate_grain_structure(
            width=image_size,
            height=image_size,
            num_grains=meta['num_grains'],
            grain_size=meta['grain_size'],
            alloy_family=alloy_family
        )
        
        # Save image
        img_path = os.path.join(output_dir, f"{meta['image_id']}.png")
        img.save(img_path)
        
        if (i + 1) % 500 == 0:
            logger.info(f"Generated {i + 1}/{num_images} images")
    
    # Save metadata to JSON
    metadata_path = os.path.join(output_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.info(f"Dataset generation complete. {num_images} images saved to {output_dir}")
    logger.info(f"Metadata saved to {metadata_path}")
    
    return metadata_list

def main():
    """Main entry point for synthetic dataset generation."""
    parser = argparse.ArgumentParser(description='Generate synthetic microstructure dataset')
    parser.add_argument('--num_images', type=int, default=NUM_IMAGES, 
                      help='Number of images to generate')
    parser.add_argument('--output_dir', type=str, default='data/raw',
                      help='Output directory for generated data')
    parser.add_argument('--image_size', type=int, default=IMAGE_SIZE,
                      help='Size of generated images (square)')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    if 'train_seed' in CONFIG:
        random.seed(CONFIG['train_seed'])
        np.random.seed(CONFIG['train_seed'])
    
    generate_dataset(
        output_dir=args.output_dir,
        num_images=args.num_images,
        image_size=args.image_size
    )

if __name__ == '__main__':
    main()
