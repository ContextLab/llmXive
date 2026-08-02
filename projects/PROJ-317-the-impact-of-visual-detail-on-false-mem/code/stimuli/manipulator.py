import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageFilter, ImageDraw
import numpy as np

from config import get_stimuli_dir, get_data_dir, get_logs_dir, Config
from utils.logging import get_logger, log_manipulation_error, ensure_error_log_directory
from data.image import Image as ImageEntity

# Constants
MIN_DENSITY_THRESHOLD = 0.2
BLUR_RADIUS = 5
WINDOW_SIZE = 32  # Sliding window size for density calculation

logger = get_logger(__name__)

def calculate_local_density(image_array: np.ndarray, x: int, y: int, window_size: int = WINDOW_SIZE) -> float:
    """
    Calculate local object density in a specific region of the image.
    Uses edge detection (Sobel) and color variance as a proxy for object density.
    
    Args:
        image_array: Numpy array of the image (H, W, C)
        x, y: Center coordinates of the region
        window_size: Size of the sliding window (square)
    
    Returns:
        float: Density score between 0.0 and 1.0
    """
    h, w, _ = image_array.shape
    half_w = window_size // 2
    
    # Define window bounds
    x1 = max(0, x - half_w)
    y1 = max(0, y - half_w)
    x2 = min(w, x + half_w)
    y2 = min(h, y + half_w)
    
    region = image_array[y1:y2, x1:x2]
    
    if region.size == 0:
        return 0.0
    
    # Calculate variance in each channel as a proxy for detail/objects
    variances = [np.var(region[:, :, i]) for i in range(region.shape[2])]
    avg_variance = np.mean(variances)
    
    # Normalize variance to a 0-1 range (heuristic scaling)
    # Typical image variance is often < 10000 for 8-bit images
    density = min(1.0, avg_variance / 5000.0)
    
    return density

def remove_minor_elements(image_path: Path, output_path: Path, seed: Optional[int] = None) -> bool:
    """
    Implement reduced detail manipulation by blurring low-density regions.
    
    Algorithm:
    1. Load baseline image.
    2. Identify Minor Elements: Use a sliding window to calculate local object density.
    3. Create Mask: Generate a binary mask for regions where density < 0.2.
    4. Blur: Apply GaussianBlur(radius=5) to the masked regions.
    5. Save output.
    
    Args:
        image_path: Path to the baseline image
        output_path: Path to save the reduced detail image
        seed: Optional random seed for reproducibility (not strictly needed for deterministic blur, but kept for consistency)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if seed is not None:
        random.seed(seed)
    
    try:
        # Load image
        logger.info(f"Loading baseline image: {image_path}")
        base_img = Image.open(image_path).convert("RGBA")
        image_array = np.array(base_img)
        
        h, w = base_img.size
        
        # Step 2 & 3: Identify low-density regions and create mask
        logger.info(f"Calculating density map for {w}x{h} image...")
        mask = Image.new("L", (w, h), 255) # Default to white (no blur)
        mask_draw = ImageDraw.Draw(mask)
        
        # Create a binary mask where low density regions are black (0) and high density are white (255)
        # We want to blur LOW density regions, so those will be 0 in the mask (if we interpret 0 as mask area)
        # Actually, let's make the mask: 0 = blur this area, 255 = keep this area
        # So low density -> 0, high density -> 255
        
        density_map = np.zeros((h, w))
        
        for y in range(0, h, 8): # Sample with stride for performance
            for x in range(0, w, 8):
                density = calculate_local_density(image_array, x, y, WINDOW_SIZE)
                density_map[y, x] = density
                density_map[y:y+8, x:x+8] = density # Fill the stride area
        
        # Create the mask based on threshold
        # If density < MIN_DENSITY_THRESHOLD, mark for blur (0)
        # Else keep (255)
        for y in range(h):
            for x in range(w):
                if density_map[y, x] < MIN_DENSITY_THRESHOLD:
                    mask_draw.point((x, y), fill=0) # Blur region
                else:
                    mask_draw.point((x, y), fill=255) # Keep region
        
        # Step 4: Apply Gaussian Blur to the masked regions
        logger.info(f"Applying Gaussian Blur (radius={BLUR_RADIUS}) to low-density regions...")
        blurred_img = base_img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
        
        # Composite: Use the mask to blend original and blurred
        # Where mask is 0 -> use blurred, where mask is 255 -> use original
        result_img = Image.composite(blurred_img, base_img, mask)
        
        # Step 5: Save output
        logger.info(f"Saving reduced detail image to: {output_path}")
        result_img.save(output_path)
        
        logger.info(f"Successfully created reduced detail image: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error during reduced detail manipulation for {image_path}: {e}", exc_info=True)
        return False

def process_single_image(image_path: Path, output_dir: Path, seed: Optional[int] = None) -> bool:
    """
    Process a single image to create the reduced detail version.
    
    Args:
        image_path: Path to the baseline image
        output_dir: Directory to save the output
        seed: Random seed
    
    Returns:
        bool: True if successful
    """
    if seed is not None:
        random.seed(seed)
    
    try:
        # Determine output filename
        stem = image_path.stem
        output_filename = f"reduced_{stem}.png"
        output_path = output_dir / output_filename
        
        success = remove_minor_elements(image_path, output_path, seed)
        return success
        
    except Exception as e:
        logger.error(f"Failed to process single image {image_path}: {e}", exc_info=True)
        return False

def process_directory(input_dir: Path, output_dir: Path, seed: Optional[int] = None) -> int:
    """
    Process all images in a directory to create reduced detail versions.
    Implements error handling: skips failed images, logs errors, continues.
    
    Args:
        input_dir: Directory containing baseline images
        output_dir: Directory to save reduced detail images
        seed: Random seed
    
    Returns:
        int: Number of successfully processed images
    """
    if seed is not None:
        random.seed(seed)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure error log directory exists
    ensure_error_log_directory()
    
    # Find all image files
    image_files = list(input_dir.glob("*.png")) + list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.jpeg"))
    
    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return 0
    
    logger.info(f"Found {len(image_files)} images to process in {input_dir}")
    
    success_count = 0
    fail_count = 0
    
    for img_path in image_files:
        logger.info(f"Processing: {img_path.name}")
        try:
            success = process_single_image(img_path, output_dir, seed)
            if success:
                success_count += 1
            else:
                fail_count += 1
                log_manipulation_error(f"Reduced detail manipulation failed for {img_path.name}", "reduced_detail")
        except Exception as e:
            fail_count += 1
            log_manipulation_error(f"Unexpected error processing {img_path.name}: {e}", "reduced_detail")
            logger.error(f"Unexpected error for {img_path.name}: {e}", exc_info=True)
    
    logger.info(f"Processing complete. Success: {success_count}, Failed: {fail_count}")
    return success_count

def main():
    """
    CLI entry point for reduced detail manipulation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate reduced detail versions of stimuli images.")
    parser.add_argument("--input-dir", type=str, help="Input directory containing baseline images")
    parser.add_argument("--output-dir", type=str, help="Output directory for reduced detail images")
    parser.add_argument("--seed", type=int, default=Config.SEED, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir) if args.input_dir else get_stimuli_dir() / "raw"
    output_dir = Path(args.output_dir) if args.output_dir else get_stimuli_dir()
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    logger.info(f"Starting reduced detail manipulation pipeline.")
    logger.info(f"Input: {input_dir}, Output: {output_dir}, Seed: {args.seed}")
    
    count = process_directory(input_dir, output_dir, args.seed)
    logger.info(f"Pipeline finished. Processed {count} images successfully.")

if __name__ == "__main__":
    main()
