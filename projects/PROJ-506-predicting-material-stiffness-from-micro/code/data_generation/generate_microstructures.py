"""
Stratified microstructure generator.

Generates 128x128 pixel synthetic microstructure images with varying
void/inclusion densities and topologies.
"""
import numpy as np
from skimage.draw import disk, ellipse
from skimage import io
from pathlib import Path
import random
import json
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_microstructure(
    seed: int,
    density: float,
    topology_type: str,
    size: int = 128
) -> np.ndarray:
    """
    Generate a single microstructure image.
    
    Args:
        seed: Random seed for reproducibility
        density: Inclusion density (0.0 to 1.0)
        topology_type: One of 'random', 'aligned', 'clustered'
        size: Image size (default 128x128)
        
    Returns:
        2D numpy array representing the microstructure (0=void, 1=inclusion)
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Initialize empty image (void phase)
    image = np.zeros((size, size), dtype=np.float32)
    
    # Calculate number of inclusions based on density
    # Approximate inclusion area as 1% of total for estimation
    avg_inclusion_area = (size * size) * 0.01
    target_inclusion_area = density * (size * size)
    n_inclusions = max(1, int(target_inclusion_area / avg_inclusion_area))
    
    for i in range(n_inclusions):
        # Random center
        cx = np.random.randint(5, size - 5)
        cy = np.random.randint(5, size - 5)
        
        # Random radius (scaled for size)
        radius = np.random.randint(3, 10)
        
        if topology_type == 'random':
            # Random orientation and position
            rr, cc = disk((cx, cy), radius)
            # Ensure within bounds
            mask = (rr >= 0) & (rr < size) & (cc >= 0) & (cc < size)
            if mask.any():
                image[rr[mask], cc[mask]] = 1.0
                
        elif topology_type == 'aligned':
            # Aligned in a grid-like pattern
            # Use deterministic offset based on iteration
            offset_x = (i * 7) % (size - 10)
            offset_y = (i * 11) % (size - 10)
            rr, cc = disk((offset_x + 5, offset_y + 5), radius)
            mask = (rr >= 0) & (rr < size) & (cc >= 0) & (cc < size)
            if mask.any():
                image[rr[mask], cc[mask]] = 1.0
                
        elif topology_type == 'clustered':
            # Cluster around a few centers
            cluster_centers = [
                (size // 3, size // 3),
                (2 * size // 3, size // 3),
                (size // 2, 2 * size // 3)
            ]
            center = cluster_centers[i % len(cluster_centers)]
            # Add small random perturbation
            cx = center[0] + np.random.randint(-10, 10)
            cy = center[1] + np.random.randint(-10, 10)
            cx = np.clip(cx, 5, size - 5)
            cy = np.clip(cy, 5, size - 5)
            rr, cc = disk((cx, cy), radius)
            mask = (rr >= 0) & (rr < size) & (cc >= 0) & (cc < size)
            if mask.any():
                image[rr[mask], cc[mask]] = 1.0
        else:
            raise ValueError(f"Unknown topology_type: {topology_type}")
    
    return image

def save_microstructure(
    image: np.ndarray,
    output_path: Path,
    seed: int
) -> None:
    """Save microstructure image to disk."""
    # Normalize to 0-255 for PNG
    image_8bit = (image * 255).astype(np.uint8)
    io.imsave(output_path, image_8bit, check_contrast=False)
    logger.info(f"Saved microstructure to {output_path}")

def calculate_topological_metrics(
    image: np.ndarray
) -> Dict[str, float]:
    """
    Calculate topological metrics for a microstructure.
    
    Args:
        image: Binary microstructure image
        
    Returns:
        Dictionary with shape_factor and connectivity metrics
    """
    # Calculate inclusion density (fraction of non-zero pixels)
    density = float(np.mean(image > 0.5))
    
    # Calculate shape factor (perimeter^2 / (4 * pi * area))
    # For a perfect circle, shape_factor = 1.0
    # Higher values indicate more irregular shapes
    from skimage.measure import label, regionprops
    
    labeled = label(image > 0.5)
    regions = regionprops(labeled)
    
    if not regions:
        return {
            'shape_factor': 0.0,
            'connectivity': 0.0,
            'inclusion_density': density
        }
    
    # Aggregate metrics across all regions
    total_area = 0
    total_perimeter_sq = 0
    n_components = len(regions)
    
    for region in regions:
        area = region.area
        perimeter = region.perimeter
        total_area += area
        total_perimeter_sq += perimeter ** 2
    
    shape_factor = total_perimeter_sq / (4 * np.pi * total_area) if total_area > 0 else 0.0
    
    # Connectivity: ratio of number of components to expected for random distribution
    # Simplified: use number of components normalized by area
    connectivity = 1.0 / (1.0 + n_components * 0.1) if total_area > 0 else 0.0
    
    return {
        'shape_factor': float(shape_factor),
        'connectivity': float(connectivity),
        'inclusion_density': density,
        'n_components': n_components
    }

def main(args) -> int:
    """
    Main entry point for microstructure generation.
    
    Args:
        args: Namespace with seed, n_samples, output_dir
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seeds = list(range(args.seed, args.seed + args.n_samples))
    metadata = []
    
    # Define stratification parameters
    densities = [0.1, 0.2, 0.3, 0.4, 0.5]
    topology_types = ['random', 'aligned', 'clustered']
    
    logger.info(f"Generating {args.n_samples} microstructures...")
    
    for i, seed in enumerate(seeds):
        # Cycle through densities and topologies for stratification
        density = densities[i % len(densities)]
        topology_type = topology_types[i % len(topology_types)]
        
        try:
            # Generate image
            image = generate_microstructure(
                seed=seed,
                density=density,
                topology_type=topology_type,
                size=128
            )
            
            # Calculate topological metrics
            metrics = calculate_topological_metrics(image)
            
            # Save image
            output_path = output_dir / f"micro_{seed}.png"
            save_microstructure(image, output_path, seed)
            
            # Record metadata
            entry = {
                'seed': seed,
                'image_path': str(output_path),
                'inclusion_density': metrics['inclusion_density'],
                'topology_type': topology_type,
                'shape_factor': metrics['shape_factor'],
                'connectivity': metrics['connectivity']
            }
            metadata.append(entry)
            
        except Exception as e:
            logger.error(f"Failed to generate microstructure {seed}: {e}")
            return 1
    
    # Save metadata
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Generated {len(metadata)} microstructures. Metadata saved to {metadata_path}")
    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic microstructures")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_samples", type=int, default=10)
    parser.add_argument("--output_dir", type=str, default="data/raw")
    args = parser.parse_args()
    exit(main(args))
