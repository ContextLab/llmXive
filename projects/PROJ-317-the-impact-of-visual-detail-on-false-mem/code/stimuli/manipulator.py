"""
Image Manipulation Module for Visual Detail False Memory Study.

This module implements the core logic for enhancing and reducing visual detail
in baseline images to create experimental stimuli.
"""
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageDraw, ImageFilter
import yaml

from config import get_stimuli_dir, get_data_dir, get_logs_dir
from utils.logging import get_logger, log_manipulation_error, get_manipulation_error_log_path

# Constants
ASSET_DIR = "data/assets/minor_objects"
MIN_ASSETS_REQUIRED = 20
TARGET_ASSETS_PER_IMAGE = 5  # "Small number" as per task description
MANIPULATION_ERROR_LOG = "data/logs/manipulation_errors.log"

logger = get_logger(__name__)


def _validate_asset_directory() -> List[Path]:
    """
    Verify that the minor object assets directory exists and contains exactly 20 PNG files.
    
    Returns:
        List[Path]: List of valid asset paths.
        
    Raises:
        SystemExit: If the asset directory is missing or does not contain exactly 20 PNGs.
    """
    project_root = get_data_dir()
    asset_path = project_root / ASSET_DIR
    
    if not asset_path.exists():
        logger.error(f"Asset directory not found: {asset_path}")
        raise SystemExit(f"CRITICAL: Asset directory missing at {asset_path}. "
                         "Run T015.1-Run to generate assets first.")
    
    png_files = list(asset_path.glob("*.png"))
    
    if len(png_files) != MIN_ASSETS_REQUIRED:
        logger.error(f"Asset count mismatch: Found {len(png_files)}, expected {MIN_ASSETS_REQUIRED}")
        raise SystemExit(f"CRITICAL: Expected exactly {MIN_ASSETS_REQUIRED} PNG assets in {asset_path}, "
                         f"but found {len(png_files)}. Run T015.1-Run to regenerate assets.")
    
    logger.info(f"Validated {len(png_files)} minor object assets in {asset_path}")
    return png_files


def add_minor_objects(
    base_image: Image.Image, 
    assets: List[Path], 
    num_objects: int = TARGET_ASSETS_PER_IMAGE,
    seed: Optional[int] = None
) -> Image.Image:
    """
    Overlay a random selection of minor object PNG assets onto the base image.
    
    Args:
        base_image: The PIL Image to enhance.
        assets: List of paths to minor object PNG assets.
        num_objects: Number of objects to overlay (default: 5).
        seed: Optional random seed for reproducibility.
        
    Returns:
        Image.Image: The enhanced image with added objects.
        
    Raises:
        ValueError: If num_objects exceeds available assets.
    """
    if num_objects > len(assets):
        raise ValueError(f"Cannot select {num_objects} objects from {len(assets)} available assets.")
    
    if seed is not None:
        random.seed(seed)
        
    # Select random assets
    selected_assets = random.sample(assets, num_objects)
    
    # Convert base image to RGBA to support transparency
    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')
        
    # Create a copy to draw on
    enhanced_image = base_image.copy()
    
    # Image dimensions for positioning
    img_width, img_height = enhanced_image.size
    
    for asset_path in selected_assets:
        try:
            # Load asset
            asset = Image.open(asset_path).convert('RGBA')
            
            # Random position (keeping within bounds, with some margin)
            margin = 50
            max_x = img_width - asset.width - margin
            max_y = img_height - asset.height - margin
            
            if max_x <= margin or max_y <= margin:
                # Fallback: center the object if image is too small
                x = (img_width - asset.width) // 2
                y = (img_height - asset.height) // 2
            else:
                x = random.randint(margin, max_x)
                y = random.randint(margin, max_y)
            
            # Create a mask for the asset (using alpha channel)
            # Paste the asset onto the enhanced image using the alpha channel as mask
            enhanced_image.paste(asset, (x, y), asset)
            
        except Exception as e:
            logger.warning(f"Failed to paste asset {asset_path}: {e}")
            continue
            
    return enhanced_image


def remove_minor_elements(
    base_image: Image.Image, 
    blur_radius: int = 5
) -> Image.Image:
    """
    Apply Gaussian blur to reduce visual detail in the image.
    
    This implements the "reduced detail" manipulation by blurring the entire image,
    effectively smoothing out minor elements and fine textures.
    
    Args:
        base_image: The PIL Image to reduce detail in.
        blur_radius: Radius for Gaussian blur (default: 5).
        
    Returns:
        Image.Image: The reduced detail image.
    """
    # Ensure image is in a mode that supports the operation
    if base_image.mode in ('RGBA', 'LA'):
        # Handle transparency by splitting, blurring, and merging
        r, g, b, a = base_image.split()
        r = r.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        g = g.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        b = b.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        reduced_image = Image.merge('RGBA', (r, g, b, a))
    else:
        reduced_image = base_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
    return reduced_image


def calculate_complexity_score(image: Image.Image) -> float:
    """
    Calculate a baseline complexity score based on object density proxy.
    
    Note: This is a simplified proxy. In a full implementation, this would
    use object detection models to count distinct objects.
    
    Args:
        image: The PIL Image to score.
        
    Returns:
        float: Complexity score between 0.0 and 1.0.
    """
    # Convert to grayscale and calculate standard deviation as a proxy for complexity
    gray = image.convert('L')
    pixels = list(gray.getdata())
    
    if not pixels:
        return 0.0
        
    mean = sum(pixels) / len(pixels)
    variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
    std_dev = variance ** 0.5
    
    # Normalize to 0-1 range (assuming max std_dev for 8-bit is ~128)
    score = min(1.0, std_dev / 128.0)
    return score


def process_single_image(
    image_path: Path, 
    output_dir: Path, 
    assets: List[Path],
    mode: str = "both"
) -> Tuple[Optional[Path], Optional[Path], Optional[Dict[str, Any]]]:
    """
    Process a single baseline image to create enhanced and/or reduced detail versions.
    
    Args:
        image_path: Path to the baseline image.
        output_dir: Directory to save processed images.
        assets: List of minor object asset paths.
        mode: "enhanced", "reduced", or "both".
        
    Returns:
        Tuple of (enhanced_path, reduced_path, metadata).
        Returns None for paths if that version was not generated.
        
    Raises:
        Exception: Propagates errors from image processing (caller handles logging).
    """
    try:
        # Load baseline image
        base_image = Image.open(image_path)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        image_id = image_path.stem
        metadata = {}
        
        enhanced_path = None
        reduced_path = None
        
        if mode in ("enhanced", "both"):
            enhanced_img = add_minor_objects(base_image, assets)
            enhanced_filename = f"{image_id}_enhanced.png"
            enhanced_path = output_dir / enhanced_filename
            enhanced_img.save(enhanced_path)
            metadata['enhanced_path'] = str(enhanced_path)
            logger.info(f"Saved enhanced image: {enhanced_path}")
            
        if mode in ("reduced", "both"):
            reduced_img = remove_minor_elements(base_image)
            reduced_filename = f"{image_id}_reduced.png"
            reduced_path = output_dir / reduced_filename
            reduced_img.save(reduced_path)
            metadata['reduced_path'] = str(reduced_path)
            logger.info(f"Saved reduced image: {reduced_path}")
            
        # Store baseline info
        metadata['baseline_path'] = str(image_path)
        metadata['original_size'] = base_image.size
        metadata['complexity_score'] = calculate_complexity_score(base_image)
        
        return enhanced_path, reduced_path, metadata
        
    except Exception as e:
        # Re-raise so the caller can log and handle
        raise e


def process_directory(
    input_dir: Path, 
    output_dir: Path, 
    assets: List[Path],
    mode: str = "both"
) -> Dict[str, Any]:
    """
    Process all images in a directory.
    
    Implements error handling: if an image fails, log the error and continue.
    Does NOT abort the pipeline.
    
    Args:
        input_dir: Directory containing baseline images.
        output_dir: Directory to save processed images.
        assets: List of minor object asset paths.
        mode: "enhanced", "reduced", or "both".
        
    Returns:
        Dict with keys: 'success_count', 'failure_count', 'errors' (list of error dicts).
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of image files
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return {'success_count': 0, 'failure_count': 0, 'errors': []}
        
    logger.info(f"Processing {len(image_files)} images from {input_dir} to {output_dir}")
    
    success_count = 0
    failure_count = 0
    errors = []
    
    for image_path in image_files:
        try:
            process_single_image(image_path, output_dir, assets, mode)
            success_count += 1
        except Exception as e:
            failure_count += 1
            error_msg = f"Failed to process {image_path}: {str(e)}"
            logger.error(error_msg)
            
            # Log to the specific manipulation error log file
            error_log_path = get_manipulation_error_log_path()
            log_manipulation_error(str(image_path), str(e), error_log_path)
            
            errors.append({
                'image': str(image_path),
                'error': str(e)
            })
            
    logger.info(f"Processing complete: {success_count} succeeded, {failure_count} failed")
    
    return {
        'success_count': success_count,
        'failure_count': failure_count,
        'errors': errors
    }


def main():
    """
    CLI entry point for running the manipulation pipeline.
    
    Usage:
        python code/stimuli/manipulator.py --input data/stimuli/raw --output data/stimuli/processed
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process baseline images to create enhanced/reduced detail versions.")
    parser.add_argument('--input', type=str, required=True, help="Input directory containing baseline images.")
    parser.add_argument('--output', type=str, required=True, help="Output directory for processed images.")
    parser.add_argument('--mode', type=str, choices=['enhanced', 'reduced', 'both'], default='both',
                        help="Which manipulation to apply (default: both).")
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Validate assets
    assets = _validate_asset_directory()
    
    # Convert paths
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
        
    # Run processing
    results = process_directory(input_dir, output_dir, assets, args.mode)
    
    # Report results
    print(f"Processing Results:")
    print(f"  Success: {results['success_count']}")
    print(f"  Failure: {results['failure_count']}")
    if results['errors']:
        print(f"  Errors logged to: {get_manipulation_error_log_path()}")
        
    if results['failure_count'] > 0:
        logger.warning(f"{results['failure_count']} images failed to process. Check logs.")
        
    sys.exit(0 if results['failure_count'] == 0 else 1)


if __name__ == "__main__":
    main()