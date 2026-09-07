"""
Synthetic planetary nebulae generator.

Generates a configurable set of N synthetic planetary nebulae with known
ground-truth ellipticity and asymmetry. Saves images as FITS files and
ground-truth metadata as JSON.

Adheres to Constitution Principle IV (Ground Truth) and FR-001.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from astropy.io import fits
from astropy.wcs import WCS

from code.config import (
    get_project_root,
    GENERATOR_SEED,
    IMAGE_SIZE,
    DEFAULT_N_IMAGES,
    DATA_SYNTHETIC,
    GT_METADATA_FILE,
    FITS_EXT,
    JSON_EXT
)
from code.io.writer import compute_file_checksum, save_metadata_json

logger = logging.getLogger(__name__)

def generate_nebula_base(
    shape: Tuple[int, int],
    center: Tuple[float, float],
    ellipticity: float,
    position_angle: float,
    flux: float,
    seed: int
) -> np.ndarray:
    """
    Generate a base synthetic planetary nebula image (elliptical Gaussian).
    
    Args:
        shape: Image shape (height, width).
        center: Center of the nebula (x, y).
        ellipticity: Ellipticity value (0.0 = circle, 1.0 = line).
        position_angle: Position angle in radians.
        flux: Total flux of the nebula.
        seed: Random seed for minor asymmetry injection.
    
    Returns:
        2D numpy array representing the nebula image.
    """
    rng = np.random.default_rng(seed)
    h, w = shape
    y, x = np.ogrid[:h, :w]
    
    cx, cy = center
    
    # Calculate semi-major and semi-minor axes based on ellipticity
    # Assume a base sigma of 20 pixels
    sigma_base = 20.0
    if ellipticity >= 1.0:
        sigma_minor = 1.0
    else:
        sigma_minor = sigma_base * (1.0 - ellipticity)
    sigma_major = sigma_base
    
    # Rotation matrix
    cos_pa = np.cos(position_angle)
    sin_pa = np.sin(position_angle)
    
    # Rotated coordinates
    dx = x - cx
    dy = y - cy
    
    # Coordinate transformation for ellipse
    # x' = x cos(theta) + y sin(theta)
    # y' = -x sin(theta) + y cos(theta)
    x_rot = dx * cos_pa + dy * sin_pa
    y_rot = -dx * sin_pa + dy * cos_pa
    
    # Elliptical Gaussian
    # I = I0 * exp( -0.5 * (x'^2/sigma_major^2 + y'^2/sigma_minor^2) )
    exponent = -0.5 * (
        (x_rot ** 2) / (sigma_major ** 2) + 
        (y_rot ** 2) / (sigma_minor ** 2)
    )
    
    # Normalize to total flux
    # Integral of Gaussian = I0 * 2 * pi * sigma_major * sigma_minor
    # I0 = Flux / (2 * pi * sigma_major * sigma_minor)
    normalization = 2 * np.pi * sigma_major * sigma_minor
    image = (flux / normalization) * np.exp(exponent)
    
    # Add minor random asymmetry (low amplitude) to make it realistic
    # but not enough to dominate the ground truth
    noise_asym = rng.normal(0, 0.005, shape) # 0.5% noise
    image = image + noise_asym
    image = np.maximum(image, 0) # Ensure non-negative
    
    return image

def calculate_true_ellipticity(
    major_axis: float,
    minor_axis: float
) -> float:
    """
    Calculate ellipticity from axis lengths.
    
    Ellipticity e = 1 - (b/a) where a is major axis, b is minor axis.
    
    Args:
        major_axis: Length of major axis.
        minor_axis: Length of minor axis.
    
    Returns:
        Ellipticity value between 0.0 and 1.0.
    """
    if major_axis <= 0:
        return 0.0
    return 1.0 - (minor_axis / major_axis)

def calculate_true_asymmetry(
    image: np.ndarray,
    center: Tuple[float, float],
    seed: int
) -> float:
    """
    Calculate true asymmetry index for the generated image.
    
    Uses the Conselice (2003) definition: A = sum(|I - I_180|) / sum(I)
    The center is rotated 180 degrees around the specified center point.
    
    Args:
        image: 2D numpy array of the image.
        center: Center point (x, y) for rotation.
        seed: Seed for deterministic calculation if needed (though calculation is deterministic).
    
    Returns:
        Asymmetry index (float).
    """
    # Create 180 degree rotated image
    # We rotate the image 180 degrees around the center
    # I_180(x, y) = I(2*cx - x, 2*cy - y)
    
    h, w = image.shape
    cx, cy = center
    
    # Create grid of indices
    y_idx, x_idx = np.indices((h, w))
    
    # Calculate rotated coordinates
    # x_rot = 2*cx - x
    # y_rot = 2*cy - y
    x_rot = 2 * cx - x_idx
    y_rot = 2 * cy - y_idx
    
    # Clip to image bounds (edges will be zero-padded effectively)
    x_rot = np.clip(x_rot, 0, w - 1)
    y_rot = np.clip(y_rot, 0, h - 1)
    
    # Get rotated image values
    # Using integer indexing for exact 180 rotation
    image_180 = image[y_rot.astype(int), x_rot.astype(int)]
    
    # Calculate asymmetry
    numerator = np.sum(np.abs(image - image_180))
    denominator = np.sum(image)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def generate_synthetic_nebula(
    image_id: int,
    shape: Tuple[int, int],
    seed: int,
    ellipticity_range: Tuple[float, float] = (0.1, 0.6),
    asymmetry_range: Tuple[float, float] = (0.05, 0.3)
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a single synthetic planetary nebula with ground truth.
    
    Args:
        image_id: Unique identifier for the image.
        shape: Image shape (height, width).
        seed: Random seed for this specific image.
        ellipticity_range: Range (min, max) for ellipticity.
        asymmetry_range: Range (min, max) for asymmetry target (used to guide generation).
    
    Returns:
        Tuple of (image_array, ground_truth_dict).
    """
    rng = np.random.default_rng(seed)
    
    # Generate random parameters
    ellipticity = rng.uniform(*ellipticity_range)
    position_angle = rng.uniform(0, np.pi)
    center_x = rng.uniform(shape[1] * 0.2, shape[1] * 0.8)
    center_y = rng.uniform(shape[0] * 0.2, shape[0] * 0.8)
    flux = rng.uniform(1000, 5000)
    
    # Generate base image
    image = generate_nebula_base(
        shape=shape,
        center=(center_x, center_y),
        ellipticity=ellipticity,
        position_angle=position_angle,
        flux=flux,
        seed=seed + 1
    )
    
    # Calculate true asymmetry
    true_asymmetry = calculate_true_asymmetry(image, (center_x, center_y), seed)
    
    # Ensure asymmetry is within a reasonable low-to-moderate interval
    # If the generated asymmetry is too high, we might need to adjust,
    # but for this task we accept the calculated value as ground truth.
    # The generation process naturally produces low-to-moderate asymmetry
    # due to the Gaussian nature + small noise.
    
    gt = {
        "image_id": f"{image_id:03d}",
        "filename": f"synth_{image_id:03d}.fits",
        "ellipticity": float(ellipticity),
        "asymmetry": float(true_asymmetry),
        "center_x": float(center_x),
        "center_y": float(center_y),
        "position_angle": float(position_angle),
        "flux": float(flux),
        "checksum": "" # To be filled after file writing
    }
    
    return image, gt

def generate_gt_metadata(
    metadata_list: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save ground truth metadata to a JSON file.
    
    Args:
        metadata_list: List of ground truth dictionaries.
        output_path: Path to the output JSON file.
    """
    save_metadata_json(metadata_list, output_path)
    logger.info(f"Ground truth metadata saved to {output_path}")

def main(
    n_images: int = DEFAULT_N_IMAGES,
    output_dir: str = str(DATA_SYNTHETIC),
    seed: int = GENERATOR_SEED
) -> None:
    """
    Main function to generate synthetic planetary nebulae.
    
    Args:
        n_images: Number of images to generate.
        output_dir: Directory to save generated images and metadata.
        seed: Global random seed.
    """
    logger.info(f"Starting synthetic nebula generation: {n_images} images")
    
    root = get_project_root()
    output_path = root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    metadata_list = []
    
    rng = np.random.default_rng(seed)
    
    for i in range(n_images):
        # Generate a unique seed for this image
        image_seed = rng.integers(0, 2**32)
        
        image, gt = generate_synthetic_nebula(
            image_id=i,
            shape=IMAGE_SIZE,
            seed=int(image_seed)
        )
        
        # Save image
        filename = gt["filename"]
        filepath = output_path / filename
        
        # Create FITS file with WCS
        hdu = fits.PrimaryHDU(image.astype(np.float32))
        
        # Create a simple WCS
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [IMAGE_SIZE[1]/2, IMAGE_SIZE[0]/2]
        wcs.wcs.cdelt = [1.0, 1.0] # 1 pixel per unit
        wcs.wcs.crval = [0.0, 0.0]
        wcs.wcs.ctype = ["X", "Y"]
        
        hdu.header.update(wcs.to_header())
        hdu.header['BUNIT'] = 'ADU'
        
        hdu.writeto(filepath, overwrite=True)
        
        # Compute checksum
        checksum = compute_file_checksum(filepath)
        gt["checksum"] = checksum
        metadata_list.append(gt)
        
        logger.debug(f"Generated {filename} (ellipticity={gt['ellipticity']:.3f}, asymmetry={gt['asymmetry']:.3f})")
    
    # Save ground truth metadata
    gt_filepath = output_path / GT_METADATA_FILE
    generate_gt_metadata(metadata_list, gt_filepath)
    
    logger.info(f"Synthetic data generation complete. {n_images} images saved.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
