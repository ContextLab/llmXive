"""
Stratified microstructure generator.
Generates 128x128 binary PNG images representing material microstructures
with varying void/inclusion densities.
"""
import numpy as np
from skimage.draw import disk, ellipse
from pathlib import Path
import random

def generate_microstructure(seed: int, density: float, topology: str, size: int = 128) -> np.ndarray:
    """
    Generate a single microstructure image.
    
    Args:
        seed: Random seed for reproducibility
        density: Target inclusion density (0.0 to 1.0)
        topology: 'random' or 'clustered'
        size: Image dimensions (default 128x128)
        
    Returns:
        2D numpy array (0=void, 1=inclusion)
    """
    np.random.seed(seed)
    random.seed(seed)
    
    image = np.zeros((size, size), dtype=np.float32)
    
    if topology == 'random':
        # Generate random circular inclusions
        n_inclusions = int((density * size * size) / (np.pi * (size * 0.05)**2))
        for _ in range(n_inclusions):
            center = (np.random.randint(10, size-10), np.random.randint(10, size-10))
            radius = np.random.uniform(3, 8)
            rr, cc = disk(center, radius, shape=image.shape)
            image[rr, cc] = 1.0
    elif topology == 'clustered':
        # Generate clustered inclusions
        n_clusters = int(density * 20)
        for _ in range(n_clusters):
            cluster_center = (np.random.randint(20, size-20), np.random.randint(20, size-20))
            for _ in range(5):
                offset = (np.random.normal(0, 10), np.random.normal(0, 10))
                center = (int(cluster_center[0] + offset[0]), int(cluster_center[1] + offset[1]))
                if 0 <= center[0] < size and 0 <= center[1] < size:
                    radius = np.random.uniform(2, 6)
                    rr, cc = disk(center, radius, shape=image.shape)
                    image[rr, cc] = 1.0
    else:
        raise ValueError(f"Unknown topology: {topology}")
        
    return image

def save_microstructure(image: np.ndarray, output_path: Path, seed: int):
    """Save microstructure as PNG."""
    from skimage.io import imsave
    # Normalize to 0-255 and save
    imsave(str(output_path), (image * 255).astype(np.uint8))

def main():
    """CLI entry point for generation."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate microstructures")
    parser.add_argument("--n_samples", type=int, default=10, help="Number of samples")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Output directory")
    args = parser.parse_args()
    
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    densities = [0.1, 0.2, 0.3, 0.4, 0.5]
    topologies = ['random', 'clustered']
    
    for i in range(args.n_samples):
        seed = i
        density = densities[i % len(densities)]
        topology = topologies[i % len(topologies)]
        
        image = generate_microstructure(seed, density, topology)
        save_microstructure(image, output_path / f"micro_{seed}.png", seed)
        
    print(f"Generated {args.n_samples} microstructures in {output_path}")

if __name__ == "__main__":
    main()
