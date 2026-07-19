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
    Returns a value between 0 (circular) and 1 (highly elliptical).
    """
    # Compute second-order moments
    y, x = np.indices(image.shape)
    
    # Calculate total flux
    total_flux = np.sum(image)
    if total_flux == 0:
        return 0.0
    
    # Calculate centroid
    x_c = np.sum(x * image) / total_flux
    y_c = np.sum(y * image) / total_flux
    
    # Calculate centered coordinates
    x_centered = x - x_c
    y_centered = y - y_c
    
    # Calculate second moments
    m00 = np.sum(image)
    m11 = np.sum((x_centered**2) * image) / m00
    m22 = np.sum((y_centered**2) * image) / m00
    m12 = np.sum(x_centered * y_centered * image) / m00
    
    # Calculate ellipticity using the standard formula
    # e = (m11 - m22) / (m11 + m22) for the major axis difference
    # We use a simplified form for circularly symmetric base
    # Ellipticity = 1 - (b/a) where b/a is the axis ratio
    # For a Gaussian, we can estimate from moments
    
    # Use the eigenvalues of the moment matrix
    trace = m11 + m22
    det = m11 * m22 - m12**2
    
    if trace <= 0 or det < 0:
        return 0.0
    
    # Axis ratio approximation
    axis_ratio = np.sqrt(det) / (trace / 2) if trace > 0 else 1.0
    axis_ratio = np.clip(axis_ratio, 0.0, 1.0)
    
    ellipticity = 1.0 - axis_ratio
    return max(0.0, min(1.0, ellipticity))

def calculate_true_asymmetry(image: np.ndarray) -> float:
    """
    Calculate true asymmetry from image using Conselice (2003) definition.
    A = sum |I(x,y) - I_180(x,y)| / sum |I(x,y)|
    """
    # Calculate center
    y, x = np.indices(image.shape)
    total_flux = np.sum(image)
    if total_flux == 0:
        return 0.0
    
    x_c = np.sum(x * image) / total_flux
    y_c = np.sum(y * image) / total_flux
    
    # Create 180-degree rotated image
    # Rotate around the centroid
    x_rot = 2 * x_c - x
    y_rot = 2 * y_c - y
    
    # Interpolate rotated image
    from scipy.ndimage import map_coordinates
    
    # Create coordinate arrays for interpolation
    coords_x = np.array([x.flatten(), y.flatten()])
    coords_rot_x = np.array([x_rot.flatten(), y_rot.flatten()])
    
    # Use nearest neighbor for simplicity in this synthetic case
    # Actually, let's use a simpler approach: just rotate the array
    rotated_image = np.rot90(image, k=2)  # 180 degree rotation
    
    # Calculate asymmetry
    numerator = np.sum(np.abs(image - rotated_image))
    denominator = np.sum(np.abs(image))
    
    if denominator == 0:
        return 0.0
    
    asymmetry = numerator / denominator
    return max(0.0, asymmetry)

def generate_synthetic_nebula(n_images: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate synthetic planetary nebulae with known ground truth.
    Creates N images with varying ellipticity and asymmetry parameters.
    """
    np.random.seed(seed)
    root = get_project_root()
    synth_dir = root / "data" / "synthetic"
    synth_dir.mkdir(parents=True, exist_ok=True)
    
    images = []
    for i in range(n_images):
        # Generate base nebula profile
        base = generate_nebula_base()
        
        # Apply controlled ellipticity (stretch along one axis)
        ellipticity_target = np.random.uniform(0.0, 0.3)
        # Stretch factor: a/b = 1/(1-e)
        stretch_factor = 1.0 / (1.0 - ellipticity_target) if ellipticity_target < 1.0 else 2.0
        
        # Apply asymmetry (introduce small irregularities)
        asymmetry_target = np.random.uniform(0.0, 0.2)
        
        # Create elliptical version by scaling coordinates
        y, x = np.indices(base.shape)
        center_y, center_x = base.shape[0] // 2, base.shape[1] // 2
        
        # Stretch along x-axis
        x_stretched = (x - center_x) * stretch_factor + center_x
        x_stretched = np.clip(x_stretched, 0, base.shape[1] - 1)
        
        # Interpolate to create elliptical shape
        from scipy.ndimage import map_coordinates
        coords = np.array([y.flatten(), x_stretched.flatten()])
        elliptical_base = map_coordinates(base, coords, order=1).reshape(base.shape)
        
        # Add asymmetry by introducing small random perturbations
        asymmetry_noise = np.random.normal(0, asymmetry_target * np.mean(elliptical_base), base.shape)
        elliptical_base = np.maximum(elliptical_base + asymmetry_noise, 0)
        
        # Add minimal baseline noise (will be replaced by artifact injection later)
        noise = np.random.normal(0, 0.001, base.shape)
        image = elliptical_base + noise
        image = np.maximum(image, 0)  # Ensure non-negative
        
        # Calculate actual ground truth values from the generated image
        actual_ellipticity = calculate_true_ellipticity(image)
        actual_asymmetry = calculate_true_asymmetry(image)
        
        # Save image
        filename = f"synth_{i:03d}.fits"
        path = synth_dir / filename
        header = {
            "ELLiptICITY": actual_ellipticity,
            "ASYMMETRY": actual_asymmetry,
            "SEED": seed,
            "N_IMAGES": n_images,
            "IMAGE_ID": i
        }
        save_fits_image(image, header, path)
        
        images.append({
            "image_id": f"{i:03d}",
            "filename": filename,
            "ellipticity": float(actual_ellipticity),
            "asymmetry": float(actual_asymmetry),
            "checksum": compute_file_checksum(path)
        })
        
        logger.info(f"Generated image {i}: ellipticity={actual_ellipticity:.4f}, asymmetry={actual_asymmetry:.4f}")
    
    return images

def generate_gt_metadata(images: List[Dict[str, Any]]):
    """
    Save ground truth metadata to JSON file.
    Schema: { "image_id": str, "filename": str, "ellipticity": float, "asymmetry": float, "checksum": str }
    """
    root = get_project_root()
    synth_dir = root / "data" / "synthetic"
    metadata_path = synth_dir / "gt_metadata.json"
    
    with open(metadata_path, "w") as f:
        json.dump(images, f, indent=2)
    
    logger.info(f"Ground truth metadata saved to {metadata_path} with {len(images)} entries")
    return metadata_path

def main():
    """
    Main entry point for synthetic data generation.
    Generates N synthetic planetary nebulae and saves ground truth metadata.
    """
    from code.config import GENERATOR_SEED
    
    # Use configured number of images
    from code.config import get_project_root
    import json
    
    # Default parameters from config (can be overridden)
    n_images = 50
    seed = GENERATOR_SEED
    
    logger.info(f"Starting synthetic data generation: {n_images} images, seed={seed}")
    
    images = generate_synthetic_nebula(n_images=n_images, seed=seed)
    generate_gt_metadata(images)
    
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()