"""
Synthetic data generation for planetary nebulae.
Generates images with known ground-truth ellipticity and asymmetry.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from astropy.io import fits

from code.config import DEFAULT_SEED, DEFAULT_SYNTHETIC_COUNT

def generate_nebula_base(shape: Tuple[int, int], center: Tuple[int, int], 
                         ellipticity: float, asymmetry: float, 
                         seed: int) -> np.ndarray:
    """
    Generate a base synthetic planetary nebula image.
    Uses a Gaussian profile with controlled ellipticity and asymmetry.
    """
    np.random.seed(seed)
    y, x = np.indices(shape)
    cy, cx = center

    # Elliptical Gaussian
    # Ellipticity e = 1 - b/a. We need sigma_x and sigma_y.
    # Let sigma_x = 2.0, sigma_y = 2.0 * (1 - ellipticity)
    sigma_x = 2.0
    sigma_y = 2.0 * max(0.1, 1 - ellipticity)

    # Rotate 45 degrees for asymmetry effect
    theta = np.pi / 4.0
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    dx = x - cx
    dy = y - cy
    dx_rot = dx * cos_t + dy * sin_t
    dy_rot = -dx * sin_t + dy * cos_t

    # Gaussian profile
    exponent = -0.5 * ((dx_rot / sigma_x)**2 + (dy_rot / sigma_y)**2)
    image = np.exp(exponent)

    # Add asymmetry: skew the profile
    # Asymmetry index A (Conselice) involves rotation by 180.
    # We simulate it by adding a lopsided component.
    if asymmetry > 0:
        # Create a lobe offset
        offset_x = int(asymmetry * 5)
        offset_y = int(asymmetry * 5)
        lobe = np.exp(-0.5 * (((x - (cx + offset_x))/sigma_x)**2 + 
                              ((y - (cy + offset_y))/sigma_y)**2))
        image += asymmetry * lobe

    # Normalize to 0-1
    image = image / image.max()

    # Add central star (point source)
    star = np.zeros_like(image)
    star[cy, cx] = 1.0
    image += 0.1 * star

    return image

def calculate_true_ellipticity(ellipticity: float) -> float:
    """Return the input ellipticity as the ground truth."""
    return ellipticity

def calculate_true_asymmetry(asymmetry: float) -> float:
    """Return the input asymmetry as the ground truth."""
    return asymmetry

def generate_synthetic_nebula(image_id: int, shape: Tuple[int, int] = (64, 64),
                              seed: int = DEFAULT_SEED) -> Tuple[np.ndarray, float, float]:
    """
    Generate a single synthetic nebula.
    Returns (image, true_ellipticity, true_asymmetry).
    """
    # Randomize parameters within defined ranges
    # Ellipticity: 0.0 to 0.5
    true_e = np.random.uniform(0.0, 0.5)
    # Asymmetry: 0.0 to 0.3
    true_a = np.random.uniform(0.0, 0.3)

    center = (shape[0] // 2, shape[1] // 2)
    img = generate_nebula_base(shape, center, true_e, true_a, seed + image_id)
    
    return img, true_e, true_a

def generate_gt_metadata(n_images: int, seed: int, output_dir: Path) -> None:
    """
    Generate N synthetic images and save ground truth metadata.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = []

    np.random.seed(seed)

    for i in range(n_images):
        img, true_e, true_a = generate_synthetic_nebula(i, seed=seed)
        filename = f"synth_{i:03d}.fits"
        filepath = output_dir / filename

        # Save FITS
        hdu = fits.PrimaryHDU(img.astype(np.float32))
        hdu.header['COMMENT'] = f"Synthetic Nebula {i}"
        hdu.header['ELLIPTICITY'] = true_e
        hdu.header['ASYMMETRY'] = true_a
        hdu.writeto(filepath, overwrite=True)

        # Checksum (simplified for this implementation)
        checksum = hash(filename) % 1000000 # Placeholder for real checksum logic from writer

        metadata.append({
            "image_id": f"{i:03d}",
            "filename": filename,
            "ellipticity": true_e,
            "asymmetry": true_a,
            "checksum": str(checksum)
        })

    # Save metadata
    meta_path = output_dir / "gt_metadata.json"
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logging.getLogger("generator").info(f"Generated {n_images} images and saved metadata to {meta_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=DEFAULT_SYNTHETIC_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    output_path = Path(args.output)
    generate_gt_metadata(args.n, args.seed, output_path)

if __name__ == "__main__":
    main()
