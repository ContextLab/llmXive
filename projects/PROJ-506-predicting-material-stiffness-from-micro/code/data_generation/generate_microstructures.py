import numpy as np
from skimage.draw import disk, ellipse
from skimage import io
from skimage.measure import regionprops, label
from skimage import morphology
from pathlib import Path
import logging
from typing import Tuple, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_microstructure(
    seed: int,
    density: float,
    topology: str,
    size: int = 128
) -> np.ndarray:
    """
    Generate a synthetic 2D microstructure image.
    
    Args:
        seed: Random seed for reproducibility.
        density: Inclusion density (0.0 to 1.0).
        topology: 'void' or 'inclusion' (stratification target).
        size: Image dimensions (default 128x128).
    
    Returns:
        np.ndarray: Binary image (0=matrix, 1=inclusion/void).
    """
    np.random.seed(seed)
    image = np.zeros((size, size), dtype=np.uint8)
    
    if topology == 'void':
        # Generate voids (black holes in white matrix)
        # We'll generate the matrix as 1s and voids as 0s
        image = np.ones((size, size), dtype=np.uint8)
        target_void_area = int(size * size * density)
        current_void_area = 0
        
        while current_void_area < target_void_area:
            # Random center
            cy, cx = np.random.randint(10, size - 10, 2)
            # Random radius
            radius = np.random.randint(5, 20)
            
            # Create disk
            y, x = disk((cy, cx), radius, shape=(size, size))
            if np.any(y < size) and np.any(x < size):
                new_void = (image[y, x] == 1).sum()
                if current_void_area + new_void <= target_void_area:
                    image[y, x] = 0
                    current_void_area += new_void
                    # Check for convergence
                    if new_void == 0:
                        break
    elif topology == 'inclusion':
        # Generate inclusions (white particles in black matrix)
        target_inclusion_area = int(size * size * density)
        current_inclusion_area = 0
        
        while current_inclusion_area < target_inclusion_area:
            cy, cx = np.random.randint(10, size - 10, 2)
            radius = np.random.randint(5, 20)
            
            y, x = disk((cy, cx), radius, shape=(size, size))
            if np.any(y < size) and np.any(x < size):
                new_inclusion = (image[y, x] == 0).sum()
                if current_inclusion_area + new_inclusion <= target_inclusion_area:
                    image[y, x] = 1
                    current_inclusion_area += new_inclusion
                    if new_inclusion == 0:
                        break
    else:
        raise ValueError(f"Unknown topology: {topology}")
    
    return image

def calculate_topological_metrics(image: np.ndarray) -> Dict[str, float]:
    """
    Calculate topological metrics: shape_factor and connectivity.
    
    Args:
        image: Binary image (0=background, 1=foreground).
    
    Returns:
        Dict containing:
            - shape_factor: Ratio of area to perimeter squared (normalized).
            - connectivity: Euler number (components - holes).
    """
    if image.max() == 0:
        # Empty image
        return {
            "shape_factor": 0.0,
            "connectivity": 0.0
        }
    
    # Label connected components
    labeled_image = label(image, connectivity=1)
    regions = regionprops(labeled_image)
    
    if not regions:
        return {
            "shape_factor": 0.0,
            "connectivity": 0.0
        }
    
    # Calculate shape factor for each region and average
    shape_factors = []
    for region in regions:
        area = region.area
        perimeter = region.perimeter
        if perimeter > 0:
            # Shape factor: 4 * pi * area / perimeter^2 (1.0 for circle, <1 for others)
            sf = (4 * np.pi * area) / (perimeter ** 2)
            shape_factors.append(sf)
    
    avg_shape_factor = np.mean(shape_factors) if shape_factors else 0.0
    
    # Calculate connectivity (Euler number)
    # Euler number = number of objects - number of holes
    # For binary images, we can use the Euler characteristic
    # Using 8-connectivity for objects, 4-connectivity for holes
    euler_number = 0
    for region in regions:
        euler_number += region.euler_number
    
    # Normalize connectivity by number of objects to get a relative measure
    n_objects = len(regions)
    relative_connectivity = euler_number / n_objects if n_objects > 0 else 0.0
    
    return {
        "shape_factor": float(avg_shape_factor),
        "connectivity": float(relative_connectivity)
    }

def save_microstructure(
    image: np.ndarray,
    seed: int,
    output_dir: Path
) -> Path:
    """
    Save microstructure image to disk.
    
    Args:
        image: Binary image to save.
        seed: Seed used for generation (for filename).
        output_dir: Directory to save to.
    
    Returns:
        Path to saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"micro_{seed}.png"
    filepath = output_dir / filename
    io.imsave(filepath, image, check_contrast=False)
    logger.info(f"Saved microstructure: {filepath}")
    return filepath

def main():
    """
    CLI entry point for microstructure generation.
    Generates images and calculates topological metrics.
    """
    import argparse
    import json
    import sys
    
    parser = argparse.ArgumentParser(description="Generate microstructures with topological metrics")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--density", type=float, required=True, help="Inclusion density (0-1)")
    parser.add_argument("--topology", type=str, required=True, choices=["void", "inclusion"], help="Topology type")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory for images")
    parser.add_argument("--metadata-dir", type=str, default="data/processed", help="Directory for metadata files")
    args = parser.parse_args()
    
    # Generate
    logger.info(f"Generating microstructure with seed={args.seed}, density={args.density}, topology={args.topology}")
    image = generate_microstructure(
        seed=args.seed,
        density=args.density,
        topology=args.topology,
        size=128
    )
    
    # Calculate topological metrics
    metrics = calculate_topological_metrics(image)
    logger.info(f"Topological metrics: {metrics}")
    
    # Save image
    output_path = save_microstructure(image, args.seed, Path(args.output_dir))
    
    # Save metadata
    metadata = {
        "seed": args.seed,
        "density": args.density,
        "topology_type": args.topology,
        "image_path": str(output_path),
        "shape_factor": metrics["shape_factor"],
        "connectivity": metrics["connectivity"],
        "size": 128
    }
    
    metadata_dir = Path(args.metadata_dir)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = metadata_dir / f"metadata_{args.seed}.json"
    
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved metadata to {metadata_file}")
    print(json.dumps(metadata))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())