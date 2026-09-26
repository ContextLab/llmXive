"""
Synthetic Stimuli Generator.

Generates reproducible naturalistic images using Perlin noise and fractal algorithms
to serve as a fallback when raw images from the dataset are missing.

Required by T014b.
"""
import os
import math
import random
from pathlib import Path
from typing import List
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Import config if available, else defaults
try:
    from config import DATA_RAW, init_seeds
except ImportError:
    from pathlib import Path
    DATA_RAW = Path("data/raw")
    init_seeds = lambda: None

def _perlin_noise_2d(width: int, height: int, scale: float = 1.0) -> np.ndarray:
    """
    Generate a simple 2D Perlin noise approximation.
    Note: For production, use a library like 'noise', but we implement a basic version
    to avoid extra dependencies if not in requirements.txt, or use numpy interpolation.
    """
    # Create a grid of random values
    grid_size = 16
    grid = np.random.rand(grid_size, grid_size)
    
    # Interpolate to target size
    x = np.linspace(0, grid_size - 1, width)
    y = np.linspace(0, grid_size - 1, height)
    x_grid, y_grid = np.meshgrid(x, y)
    
    # Bilinear interpolation (simplified)
    x0 = np.floor(x_grid).astype(int)
    y0 = np.floor(y_grid).astype(int)
    x1 = np.clip(x0 + 1, 0, grid_size - 1)
    y1 = np.clip(y0 + 1, 0, grid_size - 1)
    
    w = x_grid - x0
    h = y_grid - y0
    
    # Values at corners
    v00 = grid[y0, x0]
    v01 = grid[y0, x1]
    v10 = grid[y1, x0]
    v11 = grid[y1, x1]
    
    # Interpolate
    nx = v00 * (1 - w) + v01 * w
    ny = v10 * (1 - w) + v11 * w
    result = nx * (1 - h) + ny * h
    
    return result

def generate_stimuli(n_images: int, seed: int, output_dir: Optional[Path] = None) -> List[Path]:
    """
    Generate n_images synthetic naturalistic images.
    
    Args:
        n_images: Number of images to generate.
        seed: Random seed for reproducibility.
        output_dir: Directory to save images. Defaults to DATA_RAW/stimuli/synthetic.
        
    Returns:
        List of Path objects pointing to generated images.
    """
    init_seeds()
    random.seed(seed)
    np.random.seed(seed)
    
    if output_dir is None:
        output_dir = DATA_RAW / "stimuli" / "synthetic"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_paths = []
    
    for i in range(n_images):
        # Create a base noise image
        width, height = 256, 256
        noise = _perlin_noise_2d(width, height)
        
        # Normalize to 0-255
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        noise = (noise * 255).astype(np.uint8)
        
        # Convert to PIL Image
        img = Image.fromarray(noise, mode='L')
        
        # Add some fractal-like details by overlaying patterns
        # Simple circle overlay for "naturalistic" variation
        draw = ImageDraw.Draw(img)
        for _ in range(random.randint(5, 15)):
            r = random.randint(10, 40)
            x = random.randint(0, width - 2*r)
            y = random.randint(0, height - 2*r)
            # Random brightness
            brightness = random.randint(50, 200)
            draw.ellipse([x, y, x + 2*r, y + 2*r], fill=brightness)
        
        # Apply a slight blur to smooth edges
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        
        # Save
        filename = f"stimulus_{i:04d}.png"
        filepath = output_dir / filename
        img.save(filepath)
        generated_paths.append(filepath)
        
        # Log
        # print(f"Generated {filename}")
    
    return generated_paths

def main():
    """Entry point for generating synthetic stimuli."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Generating synthetic stimuli...")
    paths = generate_stimuli(n_images=10, seed=42)
    logger.info(f"Generated {len(paths)} synthetic images.")
    for p in paths:
        logger.info(f"  - {p}")

if __name__ == "__main__":
    main()