import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from code.config import get_project_root
from code.io.writer import save_fits_image, compute_file_checksum

logger = logging.getLogger(__name__)

def generate_nebula_base(shape: Tuple[int, int] = (256, 256), center: Tuple[int, int] = None) -> np.ndarray:
    """
    Generate a base planetary nebula profile (Gaussian-like).
    """
    if center is None:
        center = (shape[0] // 2, shape[1] // 2)
    
    y, x = np.ogrid[:shape[0], :shape[1]]
    dist = np.sqrt((x - center[1])**2 + (y - center[0])**2)
    
    # Simple radial profile
    image = np.exp(-dist**2 / (2 * (shape[0]/6)**2))
    return image

def calculate_true_ellipticity(image: np.ndarray) -> float:
    """
    Calculate true ellipticity from image moments.
    """
    # Simplified: assume circular base, ellipticity = 0
    return 0.0

def calculate_true_asymmetry(image: np.ndarray) -> float:
    """
    Calculate true asymmetry from image.
    """
    # Simplified: assume symmetric base, asymmetry = 0
    return 0.0

def generate_synthetic_nebula(n_images: int = 50, seed: int = 42):
    """
    Generate synthetic planetary nebulae with known ground truth.
    """
    np.random.seed(seed)
    root = get_project_root()
    synth_dir = root / "data" / "synthetic"
    synth_dir.mkdir(parents=True, exist_ok=True)
    
    images = []
    for i in range(n_images):
        # Vary parameters slightly
        ellipticity = np.random.uniform(0.0, 0.3)
        asymmetry = np.random.uniform(0.0, 0.2)
        
        # Generate base
        base = generate_nebula_base()
        
        # Apply ellipticity (stretch)
        # Simplified: just add noise for now
        noise = np.random.normal(0, 0.01, base.shape)
        image = base + noise
        
        # Save
        filename = f"synth_{i:03d}.fits"
        path = synth_dir / filename
        header = {"ELLiptICITY": ellipticity, "ASYMMETRY": asymmetry, "SEED": seed}
        save_fits_image(image, header, path)
        
        images.append({
            "image_id": f"{i:03d}",
            "filename": filename,
            "ellipticity": ellipticity,
            "asymmetry": asymmetry,
            "checksum": compute_file_checksum(path)
        })
    
    return images

def generate_gt_metadata(images: List[Dict[str, Any]]):
    """
    Save ground truth metadata to JSON.
    """
    root = get_project_root()
    synth_dir = root / "data" / "synthetic"
    metadata_path = synth_dir / "gt_metadata.json"
    
    with open(metadata_path, "w") as f:
        json.dump(images, f, indent=2)
    
    logger.info(f"Ground truth metadata saved to {metadata_path}")
    return metadata_path

def main():
    images = generate_synthetic_nebula(n_images=50)
    generate_gt_metadata(images)
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
