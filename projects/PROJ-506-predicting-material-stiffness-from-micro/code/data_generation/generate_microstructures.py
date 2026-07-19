"""
Microstructure Generator for Synthetic Data.

Generates 2D microstructure images with varying void/inclusion densities.
"""

import numpy as np
from skimage.draw import disk, ellipse
from pathlib import Path
import random

def generate_microstructure(
    size: int = 128,
    inclusion_density: float = 0.2,
    seed: int = 42,
    n_inclusions: int = 10
) -> np.ndarray:
    """
    Generate a synthetic microstructure image.

    Args:
        size: Image size (size x size).
        inclusion_density: Target fraction of inclusion pixels.
        seed: Random seed for reproducibility.
        n_inclusions: Number of inclusion shapes to place.

    Returns:
        2D numpy array (size x size) with values 0.0 (matrix) and 1.0 (inclusion).
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Initialize empty image
    image = np.zeros((size, size), dtype=np.float32)
    
    # Generate inclusions
    for _ in range(n_inclusions):
        # Random center
        cy = random.randint(10, size - 10)
        cx = random.randint(10, size - 10)
        
        # Random radius
        r = random.randint(5, 15)
        
        # Random shape type (disk or ellipse)
        if random.random() > 0.5:
            # Disk
            rr, cc = disk((cy, cx), r, shape=(size, size))
        else:
            # Ellipse
            ry = random.randint(5, 12)
            rx = random.randint(5, 12)
            angle = random.uniform(0, np.pi)
            rr, cc = ellipse(cy, cx, ry, rx, rotation=angle, shape=(size, size))
        
        # Clip to image bounds
        rr = np.clip(rr, 0, size - 1)
        cc = np.clip(cc, 0, size - 1)
        
        # Set inclusion pixels
        image[rr, cc] = 1.0
    
    # Normalize density if needed (simple approach)
    current_density = np.mean(image)
    if current_density > inclusion_density:
        # Randomly remove some pixels
        mask = image > 0.5
        n_to_remove = int((current_density - inclusion_density) * size * size)
        indices = np.where(mask)[0]
        if len(indices) > n_to_remove:
            remove_idx = np.random.choice(indices, n_to_remove, replace=False)
            image[remove_idx // size, remove_idx % size] = 0.0
    
    return image

def save_microstructure(
    image: np.ndarray,
    output_path: Path,
    seed: int,
    density: float
) -> None:
    """
    Save a microstructure image to disk.

    Args:
        image: 2D numpy array.
        output_path: Path to save the PNG file.
        seed: Random seed used.
        density: Actual inclusion density.
    """
    from skimage import io
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as grayscale PNG
    # Scale to 0-255 for better visibility
    img_scaled = (image * 255).astype(np.uint8)
    io.imsave(output_path, img_scaled, check_contrast=False)

def main():
    """Generate sample microstructures."""
    print("Microstructure generator loaded.")
