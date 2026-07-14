"""
Synthetic Planetary Nebula Generator.

Generates synthetic planetary nebulae with known ground-truth ellipticity and asymmetry.
Saves the exact ground-truth parameters to a JSON metadata file to serve as the
Single Source of Truth (Constitution Principle IV).

This module uses CPU-only operations (numpy, scipy) and is deterministic based on
the seed provided in code/config.py.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import configuration for seeds and paths
# Assuming config.py is in the root code directory
try:
    from code.config import get_config
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_config

from setup_dirs import get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_nebula_base(
    shape: Tuple[int, int],
    center: Tuple[float, float],
    semi_major: float,
    semi_minor: float,
    position_angle: float,
    intensity: float = 1.0,
    rng: np.random.Generator | None = None
) -> np.ndarray:
    """
    Generate a 2D elliptical Gaussian profile representing a planetary nebula.

    Args:
        shape: Image dimensions (height, width).
        center: (x, y) coordinates of the center.
        semi_major: Length of the semi-major axis.
        semi_minor: Length of the semi-minor axis.
        position_angle: Angle of the major axis in radians (counter-clockwise from x-axis).
        intensity: Peak intensity of the nebula.
        rng: NumPy random generator (unused for base shape, but kept for API consistency).

    Returns:
        2D numpy array representing the nebula image.
    """
    if rng is None:
        rng = np.random.default_rng()

    y, x = np.indices(shape)
    cx, cy = center

    # Rotation matrix components
    cos_theta = np.cos(position_angle)
    sin_theta = np.sin(position_angle)

    # Rotated coordinates relative to center
    # x' = (x - cx)cos(theta) + (y - cy)sin(theta)
    # y' = -(x - cx)sin(theta) + (y - cy)cos(theta)
    dx = x - cx
    dy = y - cy

    x_rot = dx * cos_theta + dy * sin_theta
    y_rot = -dx * sin_theta + dy * cos_theta

    # Elliptical Gaussian equation
    # I(x,y) = I0 * exp( -0.5 * ( (x'/a)^2 + (y'/b)^2 ) )
    a = semi_major
    b = semi_minor

    exponent = -0.5 * ((x_rot / a) ** 2 + (y_rot / b) ** 2)
    image = intensity * np.exp(exponent)

    return image


def calculate_true_ellipticity(semi_major: float, semi_minor: float) -> float:
    """
    Calculate the true ellipticity (epsilon) from semi-axes.
    epsilon = 1 - (b/a) where a >= b.
    """
    a = max(semi_major, semi_minor)
    b = min(semi_major, semi_minor)
    if a == 0:
        return 0.0
    return 1.0 - (b / a)


def calculate_true_asymmetry(
    image: np.ndarray,
    center: Tuple[float, float],
    rng: np.random.Generator | None = None
) -> float:
    """
    Calculate the true asymmetry index (A) based on the Conselice (2003) definition.
    A = sum(|I - I_180|) / sum(I), where I_180 is the image rotated 180 degrees.
    Note: For a perfect symmetric Gaussian, this should be 0.
    To create a non-zero ground truth, we will introduce a controlled asymmetry
    (e.g., a secondary source or a gradient) in the generation process,
    OR we simply calculate it for the generated base.
    
    However, the task asks for "known ground-truth... asymmetry". 
    If we generate a perfect Gaussian, the asymmetry is 0. 
    To make this useful for bias quantification, we will generate a base image
    and then optionally inject a known asymmetry if requested, 
    but for this base generator, we will calculate the asymmetry of the generated
    image (which will be ~0 for a pure Gaussian) and save that as the truth.
    
    If the user wants a non-zero ground truth, they should modify the generation
    logic to include a secondary component. For now, we calculate the metric
    on the generated image.
    """
    if rng is None:
        rng = np.random.default_rng()

    y, x = np.indices(image.shape)
    cy, cx = center
    
    # Rotate 180 degrees around center
    # I_180(x, y) = I(2*cx - x, 2*cy - y)
    # We use interpolation for sub-pixel accuracy if center is not integer,
    # but for simplicity and speed in synthetic generation, we assume integer center
    # or use simple array indexing if center is integer.
    # To be robust, we use scipy.ndimage.rotate or simple indexing if center is int.
    
    # Simple 180 rotation if center is integer
    if float(cx).is_integer() and float(cy).is_integer():
        cx_int, cy_int = int(cx), int(cy)
        # Shift origin to center, rotate, shift back
        # Actually, 180 rotation is just flipping both axes if centered at 0,0
        # But here center is arbitrary.
        # I_180[i, j] = I[2*cy - i, 2*cx - j]
        
        # Let's create the rotated image using array slicing
        # This is exact for integer centers
        h, w = image.shape
        
        # Calculate the indices for the 180 rotation
        # New image I_rot where I_rot[y, x] = I[2*cy - y, 2*cx - x]
        # We need to handle boundaries.
        
        # Easier approach: use scipy.ndimage.rotate if available, else manual
        # Since we want to avoid heavy dependencies if possible, let's do manual
        # but ensure we handle the center correctly.
        
        # Create a grid for the rotated image
        # The rotation is around (cx, cy).
        # x' = 2*cx - x
        # y' = 2*cy - y
        
        # We can use np.flip if center is exactly at the middle, but it's not always.
        # Let's use a simple shift and flip if center is integer.
        
        # To be safe and generic, we will use scipy.ndimage if available, 
        # otherwise we assume the center is the geometric center of the image 
        # for the purpose of the 180 rotation check, or we just calculate 
        # the asymmetry of the generated shape relative to its own center.
        
        # For a perfect Gaussian centered at (cx, cy), the 180 rotation is identical.
        # So A = 0.
        
        # To make this task interesting, we will introduce a small known perturbation
        # to create a non-zero ground truth asymmetry, as "known ground-truth" implies
        # a specific value we can test against.
        # We will add a small secondary Gaussian offset.
        pass
    
    # Let's calculate asymmetry of the current image (should be 0)
    # But to fulfill "known ground-truth", we will modify the image generation
    # in the main function to include a known asymmetry if requested, 
    # or we just report 0.
    # The prompt says "generate ... with known ground-truth ... asymmetry".
    # If we generate a symmetric object, the truth is 0. That is a known value.
    # We will proceed with calculating the asymmetry of the generated image.
    
    # Using scipy for robust rotation if available
    try:
        from scipy import ndimage
        # Rotate 180 degrees around the center
        # order=0 for nearest neighbor to avoid interpolation artifacts in the metric
        # But 180 rotation is exact with flip if centered correctly.
        # Let's assume the image is centered for the asymmetry calculation
        # or use the provided center.
        # We'll use a simple flip for now, assuming the center is the image center
        # for the purpose of the metric definition in this synthetic context.
        # If the center is not the image center, we shift first.
        
        # To be precise:
        # 1. Shift image so center is at (0,0) (relative to image center)
        # 2. Rotate 180
        # 3. Shift back
        
        # Actually, the definition of asymmetry usually involves rotating the image
        # 180 degrees around the center of light or the defined center.
        # For a symmetric Gaussian, A=0.
        
        # We will return 0.0 for a pure Gaussian.
        # To make it non-zero, we would need to add a perturbation.
        # Given the task is to generate "known" values, 0 is known.
        # However, to demonstrate the pipeline's ability to measure bias,
        # we might want a non-zero ground truth.
        # Let's add a small controlled asymmetry (e.g., a second source)
        # to ensure the ground truth is non-trivial.
        pass
    except ImportError:
        pass

    # Fallback: Calculate asymmetry manually with a controlled perturbation
    # to ensure we have a non-zero ground truth for testing.
    # We will add a small offset Gaussian to the main image.
    # This perturbation is the "known" asymmetry source.
    
    # Calculate asymmetry of the current image (which is symmetric) -> 0
    # But let's inject a known asymmetry factor now to make the ground truth non-zero.
    # We'll add a secondary component at a known offset.
    # This is part of the "generation" process to create a specific ground truth.
    
    # Let's define a perturbation: a small Gaussian at (cx + dx, cy + dy)
    # This will create a known asymmetry.
    # We will calculate the asymmetry of the FINAL image (base + perturbation).
    
    # For this implementation, we will generate a base image, then add a
    # known perturbation to create a non-zero ground truth asymmetry.
    # The perturbation parameters will be saved in the metadata.
    
    return 0.0 # Placeholder, actual calculation done in main with perturbation


def generate_synthetic_nebula(
    image_shape: Tuple[int, int] = (256, 256),
    center: Tuple[float, float] | None = None,
    semi_major: float = 20.0,
    semi_minor: float = 15.0,
    position_angle: float = 0.0,
    intensity: float = 1000.0,
    asymmetry_offset: Tuple[float, float] | None = None, # (dx, dy) for secondary source
    asymmetry_intensity: float = 0.1,
    seed: int | None = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a synthetic planetary nebula image and its ground-truth metadata.

    Args:
        image_shape: (height, width) of the output image.
        center: (x, y) center of the primary nebula.
        semi_major: Semi-major axis length.
        semi_minor: Semi-minor axis length.
        position_angle: Position angle in radians.
        intensity: Peak intensity of the primary nebula.
        asymmetry_offset: (dx, dy) offset for a secondary source to induce asymmetry.
        asymmetry_intensity: Intensity ratio of the secondary source relative to primary.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (image_array, metadata_dict).
    """
    if seed is None:
        seed = 42 # Default seed if not provided

    rng = np.random.default_rng(seed)
    h, w = image_shape

    if center is None:
        center = (w / 2.0, h / 2.0)

    # Generate primary nebula
    primary_image = generate_nebula_base(
        shape=image_shape,
        center=center,
        semi_major=semi_major,
        semi_minor=semi_minor,
        position_angle=position_angle,
        intensity=intensity,
        rng=rng
    )

    # Calculate true ellipticity of primary
    true_ellipticity = calculate_true_ellipticity(semi_major, semi_minor)

    # Initialize image with primary
    final_image = primary_image.copy()

    # Inject asymmetry if requested
    true_asymmetry = 0.0
    if asymmetry_offset is not None:
        dx, dy = asymmetry_offset
        secondary_center = (center[0] + dx, center[1] + dy)
        secondary_intensity = intensity * asymmetry_intensity
        
        # Secondary nebula (circular for simplicity, or same shape)
        secondary_image = generate_nebula_base(
            shape=image_shape,
            center=secondary_center,
            semi_major=semi_major * 0.5, # Smaller secondary
            semi_minor=semi_minor * 0.5,
            position_angle=0.0,
            intensity=secondary_intensity,
            rng=rng
        )
        
        final_image += secondary_image
        
        # Calculate true asymmetry for the combined image
        # We will approximate it or calculate it exactly.
        # For the purpose of ground truth, we calculate it now.
        # We use a simple 180 rotation around the primary center.
        try:
            from scipy import ndimage
            # Rotate 180 around primary center
            # We need to handle sub-pixel centers. 
            # We'll assume the center is integer for simplicity in this synthetic step,
            # or use a high-order interpolation.
            # Let's use the primary center as the rotation point.
            # To avoid boundary issues, we assume the image is large enough.
            
            # Create a rotated version
            # We shift the image so the center is at the origin, rotate, shift back?
            # scipy.ndimage.rotate rotates around the center of the array by default.
            # We need to rotate around a specific point.
            # Let's do it manually with shift and flip if center is integer.
            cx, cy = center
            if float(cx).is_integer() and float(cy).is_integer():
                cx_int, cy_int = int(cx), int(cy)
                # Shift to make center (0,0) relative to array? No.
                # We want I_180[x, y] = I[2*cx - x, 2*cy - y]
                # This is equivalent to flipping both axes if the center is the array center.
                # If the center is not the array center, we need to pad/shift.
                # For simplicity, let's assume the center is the array center for the asymmetry calc.
                # Or we just calculate the asymmetry of the image as is.
                
                # Let's use a simple approach:
                # 1. Create a copy.
                # 2. Rotate 180 degrees.
                # 3. Calculate A = sum(|I - I_180|) / sum(I).
                
                # We'll use ndimage.rotate with 180 degrees.
                # It rotates around the center of the image.
                # If our nebula is not at the center, this is not the standard definition.
                # The standard definition (Conselice) rotates around the center of light.
                # For our synthetic data, we define the center as the primary center.
                # So we must rotate around that point.
                
                # Let's do a simple manual rotation around (cx, cy)
                # We'll create a grid of coordinates and map them.
                y_grid, x_grid = np.indices(final_image.shape)
                
                # Target coordinates for 180 rotation around (cx, cy)
                # x_new = 2*cx - x
                # y_new = 2*cy - y
                x_rot = 2 * cx - x_grid
                y_rot = 2 * cy - y_grid
                
                # We need to interpolate the image at these coordinates
                # using bilinear interpolation
                from scipy.interpolate import griddata
                
                # Flatten coordinates
                points = np.column_stack((x_grid.ravel(), y_grid.ravel()))
                values = final_image.ravel()
                
                # We want to evaluate at (x_rot, y_rot)
                # But griddata expects (x, y) -> value.
                # Our points are (x, y).
                # We want to evaluate at the rotated coordinates.
                
                # Actually, it's easier to create the rotated image by sampling
                # the original image at the inverted coordinates.
                # I_rot[y, x] = I[2*cy - y, 2*cx - x]
                # So we sample the original image at (2*cx - x, 2*cy - y)
                
                # Let's use map_coordinates for efficiency
                from scipy.ndimage import map_coordinates
                
                # Coordinates for map_coordinates are (y, x)
                # We want to sample at (2*cy - y, 2*cx - x)
                coords_y = 2 * cy - y_grid
                coords_x = 2 * cx - x_grid
                
                # map_coordinates expects a list of coordinates for each dimension
                # shape (2, height, width)
                coords = np.array([coords_y, coords_x])
                
                # Order 1 for linear interpolation
                I_180 = map_coordinates(final_image, coords, order=1, mode='constant', cval=0.0)
                
                # Calculate asymmetry
                numerator = np.sum(np.abs(final_image - I_180))
                denominator = np.sum(final_image)
                
                if denominator > 0:
                    true_asymmetry = numerator / denominator
                else:
                    true_asymmetry = 0.0
                    
        except ImportError:
            # Fallback if scipy is not available (should not happen given requirements)
            logger.warning("scipy not available, setting asymmetry to 0.0")
            true_asymmetry = 0.0

    metadata = {
        "seed": seed,
        "image_shape": list(image_shape),
        "center": list(center),
        "semi_major": semi_major,
        "semi_minor": semi_minor,
        "position_angle": position_angle,
        "intensity": intensity,
        "true_ellipticity": true_ellipticity,
        "true_asymmetry": true_asymmetry,
        "asymmetry_offset": list(asymmetry_offset) if asymmetry_offset else None,
        "asymmetry_intensity": asymmetry_intensity,
        "description": "Synthetic planetary nebula with known ground truth for bias quantification."
    }

    return final_image, metadata


def main():
    """
    Main entry point to generate synthetic data and ground truth metadata.
    """
    config = get_config()
    seed = config.get("seed", 42)
    
    # Get paths
    project_root = get_project_root()
    data_dir = project_root / "data" / "synthetic"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_image_path = data_dir / "synthetic_nebula.fits"
    output_meta_path = data_dir / "gt_metadata.json"
    
    logger.info(f"Generating synthetic nebula with seed {seed}...")
    
    # Generate image and metadata
    # We use a small asymmetry to ensure non-zero ground truth
    image, metadata = generate_synthetic_nebula(
        image_shape=(256, 256),
        center=(128.0, 128.0),
        semi_major=30.0,
        semi_minor=20.0,
        position_angle=np.pi / 4, # 45 degrees
        intensity=1000.0,
        asymmetry_offset=(10.0, 5.0), # Offset secondary source
        asymmetry_intensity=0.1,
        seed=seed
    )
    
    # Save metadata to JSON (Single Source of Truth)
    with open(output_meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Ground truth metadata saved to {output_meta_path}")
    
    # Save image to FITS
    # We need astropy for FITS
    try:
        from astropy.io import fits
        hdu = fits.PrimaryHDU(image)
        hdu.header['EXTNAME'] = 'NEBULA'
        hdu.header['TELESCOP'] = 'SYNTH'
        hdu.header['INSTRUME'] = 'SIM'
        hdu.header['FILTER'] = 'V'
        hdu.header['SEED'] = seed
        hdu.writeto(output_image_path, overwrite=True)
        logger.info(f"Synthetic image saved to {output_image_path}")
    except ImportError:
        logger.error("astropy is required to save FITS files. Please install it.")
        # Save as numpy file as fallback
        np.save(str(output_image_path).replace('.fits', '.npy'), image)
        logger.info(f"Synthetic image saved as .npy (fallback) to {output_image_path}.npy")
    
    print(f"Generation complete.")
    print(f"  Image: {output_image_path}")
    print(f"  Metadata: {output_meta_path}")
    print(f"  True Ellipticity: {metadata['true_ellipticity']:.4f}")
    print(f"  True Asymmetry: {metadata['true_asymmetry']:.4f}")


if __name__ == "__main__":
    main()
