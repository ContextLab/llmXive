import numpy as np
from skimage.draw import disk, ellipse
from skimage import io
from skimage.measure import regionprops, label
from skimage import morphology
from pathlib import Path
import json
import logging
import argparse
from typing import Tuple, List, Dict, Any, Optional

# Import the verified topological metrics utility
from code.utils.topology_metrics import calculate_topological_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_microstructure(
    seed: int,
    topology_type: str,
    inclusion_density: float,
    size: int = 128
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a synthetic 128x128 microstructure image based on specified parameters.

    Args:
        seed: Random seed for reproducibility.
        topology_type: One of 'random', 'aligned', 'percolating'.
        inclusion_density: Volume fraction of inclusions (0.0 to 1.0).
        size: Image dimensions (default 128x128).

    Returns:
        Tuple of (image_array, metadata_dict).
        image_array: 2D numpy array (0=matrix, 1=inclusion).
        metadata_dict: Contains seed, topology_type, inclusion_density.
    """
    np.random.seed(seed)

    if not 0.0 <= inclusion_density <= 1.0:
        raise ValueError(f"inclusion_density must be between 0.0 and 1.0, got {inclusion_density}")

    if topology_type not in ["random", "aligned", "percolating"]:
        raise ValueError(f"Invalid topology_type: {topology_type}. Must be 'random', 'aligned', or 'percolating'.")

    image = np.zeros((size, size), dtype=np.uint8)

    # Calculate approximate number of inclusions needed
    # Area of one inclusion ~ (size/10)^2 to (size/5)^2 depending on density
    # We will generate objects until we reach the target density
    target_inclusion_pixels = int(size * size * inclusion_density)
    current_inclusion_pixels = 0

    attempts = 0
    max_attempts = 10000

    while current_inclusion_pixels < target_inclusion_pixels and attempts < max_attempts:
        attempts += 1

        # Random center
        cy, cx = np.random.randint(10, size - 10), np.random.randint(10, size - 10)

        # Random size and shape based on topology
        if topology_type == "random":
            # Random ellipses with varied orientation
            radius_x = np.random.randint(3, 15)
            radius_y = np.random.randint(3, 15)
            angle = np.random.uniform(0, np.pi)
            rr, cc = ellipse(cy, cx, radius_y, radius_x, rotation=angle, shape=(size, size))

        elif topology_type == "aligned":
            # Ellipses aligned with axes
            radius_x = np.random.randint(3, 15)
            radius_y = np.random.randint(3, 15)
            # No rotation or very small
            rr, cc = ellipse(cy, cx, radius_y, radius_x, shape=(size, size))

        elif topology_type == "percolating":
            # Larger, more connected shapes
            radius_x = np.random.randint(10, 25)
            radius_y = np.random.randint(10, 25)
            angle = np.random.uniform(0, np.pi)
            rr, cc = ellipse(cy, cx, radius_y, radius_x, rotation=angle, shape=(size, size))

        # Clip to image bounds
        rr = np.clip(rr, 0, size - 1)
        cc = np.clip(cc, 0, size - 1)

        # Check bounds to avoid index errors
        valid_mask = (rr < size) & (cc < size)
        if not np.any(valid_mask):
            continue

        # Draw inclusion
        # Only add pixels that are currently 0 to avoid double counting if we overlap (optional, but keeps density accurate)
        # For simplicity in this generator, we allow overlap but track total unique pixels.
        # However, to strictly control density, we should count unique pixels.
        
        # Mask for new pixels
        new_pixels = (image[rr, cc] == 0)
        
        if np.any(new_pixels):
            image[rr[new_pixels], cc[new_pixels]] = 1
            current_inclusion_pixels = np.sum(image)

    # If we failed to reach density, log warning but proceed
    if current_inclusion_pixels < target_inclusion_pixels:
        logger.warning(f"Seed {seed}: Could only reach density {current_inclusion_pixels / (size*size):.3f} (target {inclusion_density}) after {attempts} attempts.")

    # Calculate topological metrics for this generated image
    # This satisfies T017b requirements
    shape_factor, connectivity = calculate_topological_metrics(image)

    metadata = {
        "seed": seed,
        "topology_type": topology_type,
        "inclusion_density": float(current_inclusion_pixels / (size * size)),
        "shape_factor": shape_factor,
        "connectivity": connectivity,
        "size": size
    }

    return image, metadata

def save_microstructure(
    image: np.ndarray,
    metadata: Dict[str, Any],
    output_dir: Path,
    seed: int
) -> str:
    """
    Save the microstructure image and update metadata.

    Args:
        image: 2D numpy array.
        metadata: Dictionary with generation parameters.
        output_dir: Directory to save files.
        seed: Seed used for filename.

    Returns:
        Path to the saved image file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"micro_{seed}.png"
    
    # Save image as PNG (0 and 1 values, will be saved as grayscale)
    io.imsave(str(image_path), image, check_contrast=False)
    
    return str(image_path)

def main():
    """
    CLI entry point for generating microstructures.
    Usage: python -m code.data_generation.generate_microstructures --n_samples 100 --output_dir data/raw
    """
    parser = argparse.ArgumentParser(description="Generate synthetic microstructure images.")
    parser.add_argument("--n_samples", type=int, default=100, help="Number of samples to generate.")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Output directory for images.")
    parser.add_argument("--density_range", type=str, default="0.1,0.5", help="Comma-separated min,max density range.")
    parser.add_argument("--topologies", type=str, default="random,aligned,percolating", help="Comma-separated list of topologies.")
    
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    min_density, max_density = map(float, args.density_range.split(","))
    topologies = [t.strip() for t in args.topologies.split(",")]

    logger.info(f"Generating {args.n_samples} microstructures in {output_dir}")
    logger.info(f"Density range: {min_density} - {max_density}")
    logger.info(f"Topologies: {topologies}")

    all_metadata = []
    seeds_used = []

    for i in range(args.n_samples):
        seed = i  # Simple deterministic seed mapping for reproducibility
        seeds_used.append(seed)
        
        # Stratified sampling logic:
        # Cycle through topologies and distribute density
        topology = topologies[i % len(topologies)]
        
        # Distribute density uniformly across the range for this topology
        # To ensure coverage, we can use a simple linear mapping or random within range
        # For strict stratification, we might want to ensure equal counts per bin, 
        # but for a generator script, random within range per sample is acceptable 
        # as long as the dataset as a whole covers the space.
        # Let's use a deterministic distribution based on index to ensure coverage.
        density = min_density + (max_density - min_density) * ((i // len(topologies)) / (args.n_samples // len(topologies) + 1))
        # Clamp to range just in case
        density = np.clip(density, min_density, max_density)

        try:
            image, metadata = generate_microstructure(
                seed=seed,
                topology_type=topology,
                inclusion_density=density,
                size=128
            )
            
            image_path = save_microstructure(image, metadata, output_dir, seed)
            metadata["image_path"] = image_path
            
            all_metadata.append(metadata)
            logger.info(f"Generated {i+1}/{args.n_samples}: seed={seed}, topo={topology}, density={metadata['inclusion_density']:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to generate sample {seed}: {e}")
            continue

    # Save metadata to a JSON file
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump({
            "seeds": seeds_used,
            "parameters": {
                "density_range": [min_density, max_density],
                "topologies": topologies
            },
            "samples": all_metadata
        }, f, indent=2)

    logger.info(f"Generation complete. Metadata saved to {metadata_path}")
    return 0

if __name__ == "__main__":
    exit(main())
