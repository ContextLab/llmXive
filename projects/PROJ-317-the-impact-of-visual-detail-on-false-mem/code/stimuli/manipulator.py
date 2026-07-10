"""
Stimulus manipulation module for enhancing and reducing visual detail.

Implements compositing of minor object PNG assets onto baseline images
to simulate enhanced visual detail, and Gaussian blur/masking for reduced detail.
"""
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from config import get_stimuli_dir, get_stimuli_metadata_dir, get_project_root
from utils.logging import get_logger, get_manipulation_error_log_path

# Configure logger for this module
logger = get_logger(__name__)

# Minor object asset pool (relative paths to assets in data/stimuli/assets/)
# These are small PNGs representing minor details (e.g., leaves, small objects)
MINOR_OBJECT_ASSETS = [
    "leaf_small.png",
    "stone_small.png",
    "flower_small.png",
    "twig_small.png",
    "pebble_small.png",
]

def _load_asset(asset_name: str) -> Optional[Image.Image]:
    """Load a minor object asset from the assets directory."""
    asset_path = get_project_root() / "data" / "stimuli" / "assets" / asset_name
    if not asset_path.exists():
        logger.warning(f"Asset not found: {asset_path}. Skipping.")
        return None
    try:
        img = Image.open(asset_path).convert("RGBA")
        return img
    except Exception as e:
        logger.error(f"Failed to load asset {asset_path}: {e}")
        return None

def add_minor_objects(
    input_image: Image.Image,
    num_objects: int = 5,
    asset_pool: Optional[List[str]] = None,
    max_scale: float = 0.15,
    min_scale: float = 0.05,
) -> Tuple[Image.Image, int]:
    """
    Overlay a small number of minor object PNG assets onto the input image.
    
    Args:
        input_image: PIL Image to modify (must be RGBA or converted).
        num_objects: Number of minor objects to overlay.
        asset_pool: List of asset filenames to choose from. Defaults to MINOR_OBJECT_ASSETS.
        max_scale: Maximum scale factor relative to image width.
        min_scale: Minimum scale factor relative to image width.
    
    Returns:
        Tuple of (modified_image, object_count).
    """
    if asset_pool is None:
        asset_pool = MINOR_OBJECT_ASSETS
    
    # Ensure image is RGBA for alpha compositing
    if input_image.mode != "RGBA":
        base = input_image.convert("RGBA")
    else:
        base = input_image
    
    width, height = base.size
    objects_added = 0
    
    for _ in range(num_objects):
        # Select a random asset
        asset_name = random.choice(asset_pool)
        asset_img = _load_asset(asset_name)
        if asset_img is None:
            continue
        
        # Randomize scale
        scale = random.uniform(min_scale, max_scale)
        new_width = int(width * scale)
        new_height = int(asset_img.size[1] * (new_width / asset_img.size[0]))
        asset_resized = asset_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Random position (ensure within bounds)
        x = random.randint(0, width - new_width)
        y = random.randint(0, height - new_height)
        
        # Create a layer for this object and paste with alpha
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(asset_resized, (x, y), asset_resized)
        base = Image.alpha_composite(base, layer)
        objects_added += 1
    
    return base, objects_added

def remove_minor_elements(
    input_image: Image.Image,
    blur_radius: int = 5,
    mask_percentage: float = 0.1,
) -> Image.Image:
    """
    Apply Gaussian blur to simulate removal of minor elements.
    
    Args:
        input_image: PIL Image to modify.
        blur_radius: Radius for Gaussian blur.
        mask_percentage: Percentage of image area to blur (random regions).
    
    Returns:
        Modified PIL Image with reduced detail.
    """
    if input_image.mode != "RGBA":
        base = input_image.convert("RGBA")
    else:
        base = input_image
    
    width, height = base.size
    total_area = width * height
    blur_area = int(total_area * mask_percentage)
    
    # Create a copy to apply blur
    result = base.copy()
    
    # Apply blur to random rectangular regions until target area is covered
    current_blur_area = 0
    while current_blur_area < blur_area:
        # Random region size
        region_w = random.randint(width // 10, width // 4)
        region_h = random.randint(height // 10, height // 4)
        x = random.randint(0, max(0, width - region_w))
        y = random.randint(0, max(0, height - region_h))
        
        region_area = region_w * region_h
        if current_blur_area + region_area > blur_area:
            break
        
        # Extract region, blur, and paste back
        region = result.crop((x, y, x + region_w, y + region_h))
        blurred_region = region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        result.paste(blurred_region, (x, y), blurred_region)
        current_blur_area += region_area
    
    return result

def calculate_complexity_score(image: Image.Image) -> float:
    """
    Calculate a simple complexity score based on texture variance.
    
    Args:
        image: PIL Image to analyze.
    
    Returns:
        Float complexity score (normalized 0-1).
    """
    # Convert to grayscale and compute variance
    gray = image.convert("L")
    arr = np.array(gray)
    variance = np.var(arr)
    
    # Normalize variance to 0-1 range (assuming 0-255 input)
    max_variance = (255 ** 2) / 4  # Max variance for uniform distribution
    score = min(1.0, variance / max_variance)
    return score

def process_single_image(
    input_path: Path,
    output_dir: Path,
    enhance: bool = True,
    reduce: bool = True,
) -> Dict[str, Any]:
    """
    Process a single image: generate enhanced and/or reduced detail versions.
    
    Args:
        input_path: Path to input image.
        output_dir: Directory to save output images.
        enhance: Whether to generate enhanced version.
        reduce: Whether to generate reduced version.
    
    Returns:
        Dict with output paths and metadata.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        input_img = Image.open(input_path)
        if input_img.mode != "RGBA":
            input_img = input_img.convert("RGBA")
        
        result = {
            "input_path": str(input_path),
            "enhanced_path": None,
            "reduced_path": None,
            "original_complexity": calculate_complexity_score(input_img),
            "objects_added": 0,
        }
        
        if enhance:
            enhanced_img, objects_added = add_minor_objects(input_img)
            enhanced_path = output_dir / f"{input_path.stem}_enhanced.png"
            enhanced_img.save(enhanced_path)
            result["enhanced_path"] = str(enhanced_path)
            result["objects_added"] = objects_added
            result["enhanced_complexity"] = calculate_complexity_score(enhanced_img)
        
        if reduce:
            reduced_img = remove_minor_elements(input_img)
            reduced_path = output_dir / f"{input_path.stem}_reduced.png"
            reduced_img.save(reduced_path)
            result["reduced_path"] = str(reduced_path)
            result["reduced_complexity"] = calculate_complexity_score(reduced_img)
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}")
        # Log to error file
        error_log_path = get_manipulation_error_log_path()
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | ERROR | {input_path} | {str(e)}\n")
        return {"input_path": str(input_path), "error": str(e)}

def process_directory(
    input_dir: Path,
    output_dir: Path,
    enhance: bool = True,
    reduce: bool = True,
) -> List[Dict[str, Any]]:
    """
    Process all images in a directory.
    
    Args:
        input_dir: Directory containing input images.
        output_dir: Directory to save output images.
        enhance: Whether to generate enhanced versions.
        reduce: Whether to generate reduced versions.
    
    Returns:
        List of result dicts for each processed image.
    """
    results = []
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    
    input_files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    logger.info(f"Processing {len(input_files)} images from {input_dir}")
    
    for img_path in input_files:
        logger.info(f"Processing {img_path.name}")
        result = process_single_image(img_path, output_dir, enhance, reduce)
        results.append(result)
    
    return results

def main():
    """CLI entry point for running the manipulation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stimulus manipulation pipeline")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=get_stimuli_dir(),
        help="Input directory containing baseline images",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=get_stimuli_dir() / "manipulated",
        help="Output directory for manipulated images",
    )
    parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Skip enhanced detail generation",
    )
    parser.add_argument(
        "--no-reduce",
        action="store_true",
        help="Skip reduced detail generation",
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return 1
    
    results = process_directory(
        args.input_dir,
        args.output_dir,
        enhance=not args.no_enhance,
        reduce=not args.no_reduce,
    )
    
    success_count = sum(1 for r in results if "error" not in r)
    logger.info(f"Completed: {success_count}/{len(results)} images processed successfully")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    exit(main())
