import numpy as np
from skimage.draw import disk, ellipse
from skimage import io
from pathlib import Path
import random
import json
import logging
from typing import Dict, Tuple, List, Optional
from skimage.measure import label, regionprops
from scipy import ndimage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_microstructure(
    seed: int,
    size: int = 128,
    inclusion_density: float = 0.2,
    topology_type: str = "circular"
) -> np.ndarray:
    """
    Generate a synthetic microstructure image with specified parameters.

    Args:
        seed: Random seed for reproducibility
        size: Image size (size x size)
        inclusion_density: Fraction of area covered by inclusions (0.0 to 1.0)
        topology_type: Type of inclusion shape ("circular", "elliptical", "mixed")

    Returns:
        2D numpy array representing the microstructure (0 = matrix, 1 = inclusion)
    """
    random.seed(seed)
    np.random.seed(seed)

    image = np.zeros((size, size), dtype=np.float32)

    # Determine number of inclusions based on density and topology
    if topology_type == "circular":
        num_inclusions = int(inclusion_density * size * size / (np.pi * (size/10)**2))
        num_inclusions = max(1, num_inclusions)
        for _ in range(num_inclusions):
            center_x = random.randint(int(size*0.1), int(size*0.9))
            center_y = random.randint(int(size*0.1), int(size*0.9))
            radius = random.randint(int(size*0.05), int(size*0.15))
            rr, cc = disk((center_x, center_y), radius, shape=image.shape)
            # Clip to image bounds
            rr = np.clip(rr, 0, size-1)
            cc = np.clip(cc, 0, size-1)
            image[rr, cc] = 1.0

    elif topology_type == "elliptical":
        num_inclusions = int(inclusion_density * size * size / (np.pi * (size/10) * (size/20)))
        num_inclusions = max(1, num_inclusions)
        for _ in range(num_inclusions):
            center_x = random.randint(int(size*0.1), int(size*0.9))
            center_y = random.randint(int(size*0.1), int(size*0.9))
            radius_x = random.randint(int(size*0.05), int(size*0.15))
            radius_y = random.randint(int(size*0.03), int(size*0.1))
            angle = random.uniform(0, np.pi)
            rr, cc = ellipse(center_x, center_y, radius_x, radius_y, shape=image.shape, rotation=angle)
            rr = np.clip(rr, 0, size-1)
            cc = np.clip(cc, 0, size-1)
            image[rr, cc] = 1.0

    elif topology_type == "mixed":
        # Mix of circular and elliptical
        num_inclusions = int(inclusion_density * size * size / (np.pi * (size/10)**2))
        num_inclusions = max(1, num_inclusions)
        for _ in range(num_inclusions):
            center_x = random.randint(int(size*0.1), int(size*0.9))
            center_y = random.randint(int(size*0.1), int(size*0.9))
            shape_choice = random.choice(["circular", "elliptical"])
            if shape_choice == "circular":
                radius = random.randint(int(size*0.05), int(size*0.15))
                rr, cc = disk((center_x, center_y), radius, shape=image.shape)
            else:
                radius_x = random.randint(int(size*0.05), int(size*0.15))
                radius_y = random.randint(int(size*0.03), int(size*0.1))
                angle = random.uniform(0, np.pi)
                rr, cc = ellipse(center_x, center_y, radius_x, radius_y, shape=image.shape, rotation=angle)
            rr = np.clip(rr, 0, size-1)
            cc = np.clip(cc, 0, size-1)
            image[rr, cc] = 1.0
    else:
        raise ValueError(f"Unknown topology_type: {topology_type}")

    # Ensure binary output
    image = (image > 0).astype(np.float32)
    return image

def save_microstructure(image: np.ndarray, output_path: Path, seed: int) -> None:
    """
    Save a microstructure image to disk.

    Args:
        image: 2D numpy array
        output_path: Path to save the image
        seed: Seed used for generation (for naming)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    io.imsave(str(output_path), (image * 255).astype(np.uint8), check_contrast=False)

def calculate_topological_metrics(image: np.ndarray) -> Dict[str, float]:
    """
    Calculate topological metrics for a microstructure image.

    Args:
        image: 2D numpy array (binary: 0 = matrix, 1 = inclusion)

    Returns:
        Dictionary containing:
            - shape_factor: Ratio of perimeter^2 to area (normalized)
            - connectivity: Euler number (number of objects - number of holes)
    """
    # Ensure binary
    binary_image = (image > 0.5).astype(np.uint8)

    # Label connected components (8-connectivity for 2D)
    labeled_image = label(binary_image, connectivity=2)

    if labeled_image.max() == 0:
        # No inclusions
        return {
            "shape_factor": 0.0,
            "connectivity": 0.0
        }

    # Calculate shape factor and connectivity
    shape_factors = []
    num_holes = 0

    props = regionprops(labeled_image)
    for prop in props:
        area = prop.area
        if area == 0:
            continue
        # Perimeter calculation
        perimeter = prop.perimeter
        if perimeter == 0:
            continue
        # Shape factor: P^2 / (4 * pi * A) -> 1 for perfect circle, >1 for others
        sf = (perimeter ** 2) / (4 * np.pi * area)
        shape_factors.append(sf)

        # Count holes (inclusions with holes inside them)
        # This is a simplified approach; for complex microstructures,
        # a more robust method might be needed.
        # Euler number for the whole image: objects - holes
        # We'll approximate holes by checking if any inclusion has a hole
        # by looking at the labeled image's holes.
        # A simpler approach: use ndimage to find holes in binary image
        pass

    # Calculate Euler number (connectivity) using scipy
    # Euler number = # objects - # holes
    # For binary image, we can compute it directly
    # Using a 3x3 kernel for 8-connectivity
    structure = np.ones((3, 3), dtype=int)
    labeled_objects, num_objects = ndimage.label(binary_image, structure=structure)
    
    # Find holes: background regions completely surrounded by foreground
    # Invert binary image to find background
    inverted = 1 - binary_image
    labeled_background, num_background = ndimage.label(inverted, structure=structure)
    
    # Holes are background regions that do not touch the image border
    # Check if any background label touches the border
    border_indices = (
        np.any(labeled_background == 1, axis=1) | 
        np.any(labeled_background == num_background, axis=1) |
        np.any(labeled_background == 1, axis=0) |
        np.any(labeled_background == num_background, axis=0)
    )
    
    # Actually, a simpler way:
    # Holes = (number of background components) - 1 (the external background)
    # But this assumes the background is connected to the border.
    # Let's use a standard method:
    # Holes = num_background - 1 (if the external background is counted as one)
    # However, if the image is all foreground, num_background might be 0.
    
    # Robust method:
    # 1. Pad the inverted image with 0 (background) to ensure external background is connected
    # 2. Label the padded inverted image
    # 3. Holes = num_labels - 1 (the external background)
    padded_inverted = np.pad(inverted, pad_width=1, mode='constant', constant_values=0)
    labeled_padded, num_padded = ndimage.label(padded_inverted, structure=structure)
    num_holes = num_padded - 1  # Subtract the external background
    
    # Euler number (connectivity) = num_objects - num_holes
    connectivity = num_objects - num_holes

    # Average shape factor
    avg_shape_factor = np.mean(shape_factors) if shape_factors else 0.0

    return {
        "shape_factor": float(avg_shape_factor),
        "connectivity": float(connectivity)
    }

def main():
    """
    Main function to generate microstructures and calculate topological metrics.
    This script is intended to be called by the orchestration script (main.py).
    """
    import argparse
    parser = argparse.ArgumentParser(description="Generate microstructures and calculate metrics")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--n_samples", type=int, default=1, help="Number of samples to generate")
    parser.add_argument("--density", type=float, default=0.2, help="Inclusion density")
    parser.add_argument("--topology", type=str, default="circular", help="Topology type")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Output directory")
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata_list = []

    for i in range(args.n_samples):
        current_seed = args.seed + i
        logger.info(f"Generating microstructure {i+1}/{args.n_samples} with seed {current_seed}")
        
        image = generate_microstructure(
            seed=current_seed,
            size=128,
            inclusion_density=args.density,
            topology_type=args.topology
        )
        
        filename = f"micro_{current_seed}.png"
        save_microstructure(image, output_path / filename, current_seed)
        
        # Calculate topological metrics
        metrics = calculate_topological_metrics(image)
        
        # Create metadata entry
        metadata = {
            "seed": current_seed,
            "image_path": str((output_path / filename).resolve()),
            "inclusion_density": args.density,
            "topology_type": args.topology,
            "shape_factor": metrics["shape_factor"],
            "connectivity": metrics["connectivity"],
            "image_size": 128
        }
        metadata_list.append(metadata)
        
        logger.info(f"  Shape factor: {metrics['shape_factor']:.4f}, Connectivity: {metrics['connectivity']}")

    # Save metadata to a JSON file
    metadata_file = output_path / "generation_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.info(f"Saved metadata to {metadata_file}")

if __name__ == "__main__":
    main()