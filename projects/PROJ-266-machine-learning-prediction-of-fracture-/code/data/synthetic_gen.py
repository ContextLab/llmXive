import os
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import CONFIG from the shared config module to ensure consistency
from code.utils.config import CONFIG

# Constants for synthetic generation
ALLOY_FAMILIES = ['steel', 'Al', 'Ti']
BASE_K_IC_VALUES = {
    'steel': 120.0,
    'Al': 45.0,
    'Ti': 80.0
}
ALPHA_COEFF = 0.5  # Grain size coefficient
BETA_COEFF = 1.2   # Precipitate density coefficient
NOISE_STD = 5.0    # Standard deviation for noise

def generate_grain_structure(
    width: int,
    height: int,
    grain_size: float,
    num_grains: int,
    seed: int
) -> Image.Image:
    """
    Generates a synthetic microstructure image representing grain boundaries.
    
    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        grain_size: Average grain size (used to determine number of grains).
        num_grains: Number of Voronoi-like regions to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        PIL Image representing the microstructure.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    img = Image.new('L', (width, height), color=128)
    draw = ImageDraw.Draw(img)
    
    # Generate random seed points for grains
    points = []
    for _ in range(num_grains):
        x = random.randint(0, width)
        y = random.randint(0, height)
        points.append((x, y))
    
    # Assign random colors (grayscale values) to each grain
    grain_colors = [random.randint(0, 200) for _ in range(num_grains)]
    
    # Simple Voronoi-like tessellation by distance
    for y in range(height):
        for x in range(width):
            min_dist = float('inf')
            closest_idx = 0
            for i, (px, py) in enumerate(points):
                dist = (x - px)**2 + (y - py)**2
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            img.putpixel((x, y), grain_colors[closest_idx])
    
    # Apply slight blur to simulate grain boundary diffusion
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    return img

def calculate_physics_informed_k_ic(
    grain_size: float,
    precipitate_density: float,
    alloy_family: str
) -> float:
    """
    Calculates K_IC based on the synthetic ground truth formula defined in research.md.
    
    Formula: K_IC = base_value + alpha*grain_size + beta*precipitate_density + noise
    
    Args:
        grain_size: Grain size in microns.
        precipitate_density: Density of precipitates (arbitrary units).
        alloy_family: The alloy family ('steel', 'Al', 'Ti').
        
    Returns:
        Calculated K_IC value.
    """
    base_value = BASE_K_IC_VALUES.get(alloy_family, 100.0)
    noise = np.random.normal(0, NOISE_STD)
    k_ic = base_value + ALPHA_COEFF * grain_size + BETA_COEFF * precipitate_density + noise
    return float(k_ic)

def generate_sample_metadata(
    image_path: str,
    grain_size: float,
    precipitate_density: float,
    alloy_family: str,
    k_ic: float,
    magnification_calibration: float,
    section_thickness: float
) -> Dict[str, Any]:
    """
    Generates a metadata dictionary for a single sample.
    
    Args:
        image_path: Path to the generated image.
        grain_size: Simulated grain size.
        precipitate_density: Simulated precipitate density.
        alloy_family: Alloy family label.
        k_ic: Calculated fracture toughness.
        magnification_calibration: Pixels per micron.
        section_thickness: Section thickness in nm.
        
    Returns:
        Dictionary containing sample metadata.
    """
    return {
        "image_path": image_path,
        "alloy_family": alloy_family,
        "grain_size_microns": grain_size,
        "precipitate_density": precipitate_density,
        "k_ic": k_ic,
        "magnification_calibration": magnification_calibration,
        "section_thickness_nm": section_thickness
    }

def generate_dataset(target_size: int, output_dir: str) -> List[Dict[str, Any]]:
    """
    Generates the full synthetic dataset of microstructure images and metadata.
    
    Args:
        target_size: Number of samples to generate (from CONFIG['target_sample_size']).
        output_dir: Directory to save images and metadata.
        
    Returns:
        List of metadata dictionaries.
    """
    # Ensure output directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize RNG with split_seed for reproducible alloy assignment
    split_seed = CONFIG.get('split_seed', 42)
    random.seed(split_seed)
    np.random.seed(split_seed)
    
    metadata_list = []
    image_files = []
    
    # Ensure at least one sample per alloy family
    guaranteed_families = ALLOY_FAMILIES.copy()
    random.shuffle(guaranteed_families)
    
    for i, family in enumerate(guaranteed_families):
        idx = i
        # Generate parameters
        grain_size = np.random.uniform(5.0, 50.0)
        precipitate_density = np.random.uniform(0.1, 2.0)
        
        # Sample preparation metadata
        magnification_calibration = np.random.uniform(10.0, 100.0) # pixels/micron
        section_thickness = np.random.uniform(10.0, 50.0) # nm
        
        k_ic = calculate_physics_informed_k_ic(grain_size, precipitate_density, family)
        
        # Generate image
        img = generate_grain_structure(
            width=128,
            height=128,
            grain_size=grain_size,
            num_grains=int(10 + grain_size),
            seed=split_seed + idx
        )
        
        img_filename = f"sample_{idx:04d}.png"
        img_path = os.path.join(output_dir, img_filename)
        img.save(img_path)
        
        # Record metadata
        meta = generate_sample_metadata(
            image_path=img_filename, # Store relative path
            grain_size=grain_size,
            precipitate_density=precipitate_density,
            alloy_family=family,
            k_ic=k_ic,
            magnification_calibration=magnification_calibration,
            section_thickness=section_thickness
        )
        metadata_list.append(meta)
        image_files.append(img_filename)
    
    # Generate remaining samples
    remaining_count = target_size - len(guaranteed_families)
    for i in range(remaining_count):
        idx = len(guaranteed_families) + i
        family = random.choice(ALLOY_FAMILIES)
        
        grain_size = np.random.uniform(5.0, 50.0)
        precipitate_density = np.random.uniform(0.1, 2.0)
        
        magnification_calibration = np.random.uniform(10.0, 100.0)
        section_thickness = np.random.uniform(10.0, 50.0)
        
        k_ic = calculate_physics_informed_k_ic(grain_size, precipitate_density, family)
        
        img = generate_grain_structure(
            width=128,
            height=128,
            grain_size=grain_size,
            num_grains=int(10 + grain_size),
            seed=split_seed + idx
        )
        
        img_filename = f"sample_{idx:04d}.png"
        img_path = os.path.join(output_dir, img_filename)
        img.save(img_path)
        
        meta = generate_sample_metadata(
            image_path=img_filename,
            grain_size=grain_size,
            precipitate_density=precipitate_density,
            alloy_family=family,
            k_ic=k_ic,
            magnification_calibration=magnification_calibration,
            section_thickness=section_thickness
        )
        metadata_list.append(meta)
        image_files.append(img_filename)
    
    return metadata_list

def compute_sha256_checksum(file_path: str) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for the synthetic dataset generation.
    Produces images, metadata.json, and the required checksum file.
    """
    # Get configuration
    target_size = CONFIG.get('target_sample_size', 500)
    raw_data_dir = 'data/raw'
    benchmark_dir = 'data/benchmarks'
    
    # Ensure directories exist
    Path(raw_data_dir).mkdir(parents=True, exist_ok=True)
    Path(benchmark_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {target_size} synthetic samples...")
    
    # Generate dataset
    metadata = generate_dataset(target_size, raw_data_dir)
    
    # Save metadata to JSON
    metadata_path = os.path.join(raw_data_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to {metadata_path}")
    
    # Compute and save SHA-256 checksum (Constitution Principle III)
    checksum_hash = compute_sha256_checksum(metadata_path)
    checksum_data = {
        "metadata_file": "data/raw/metadata.json",
        "sha256": checksum_hash
    }
    checksum_path = os.path.join(benchmark_dir, 'metadata_checksum.json')
    with open(checksum_path, 'w') as f:
        json.dump(checksum_data, f, indent=2)
    
    print(f"Checksum saved to {checksum_path}")
    print(f"Synthetic generation complete. Total samples: {len(metadata)}")

if __name__ == "__main__":
    main()