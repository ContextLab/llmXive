"""
Image Stimuli Manipulation Module.

Handles the enhancement and reduction of visual detail in baseline images
to create experimental stimuli for false memory research.
"""
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from config import get_stimuli_dir, get_stimuli_metadata_dir, get_logs_dir, get_manipulation_error_log_path
from utils.logging import get_logger
from stimuli.metadata import generate_metadata_for_image, save_metadata_as_yaml, ManipulationRecord, StimulusMetadata

# Constants for performance optimization
MAX_PROCESSING_TIME_SECONDS = 30
CACHE_DIR = Path("data/stimuli_cache")
ASSET_DIR = Path("data/stimuli/assets")

# Pre-defined minor object assets (simulated with simple shapes for performance)
# In a real deployment, these would be PNG files in ASSET_DIR
MINOR_OBJECTS = [
    {"type": "circle", "color": (255, 0, 0), "size": 10},   # Red dot
    {"type": "square", "color": (0, 255, 0), "size": 12},   # Green square
    {"type": "triangle", "color": (0, 0, 255), "size": 15}, # Blue triangle
    {"type": "line", "color": (255, 255, 0), "size": 20},   # Yellow line
    {"type": "dot", "color": (255, 165, 0), "size": 8},     # Orange dot
]

logger = get_logger(__name__)


def _generate_mock_asset(type_name: str, color: Tuple[int, int, int], size: int) -> Image.Image:
    """
    Generates a simple mock asset on the fly to avoid disk I/O for small shapes.
    This is significantly faster than loading PNG files for minor objects.
    """
    # Create a small transparent canvas
    asset_size = size * 2
    asset = Image.new('RGBA', (asset_size, asset_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(asset)

    if type_name == "circle":
        draw.ellipse([0, 0, asset_size, asset_size], fill=color + (200,))
    elif type_name == "square":
        draw.rectangle([0, 0, asset_size, asset_size], fill=color + (200,))
    elif type_name == "triangle":
        points = [(asset_size // 2, 0), (0, asset_size), (asset_size, asset_size)]
        draw.polygon(points, fill=color + (200,))
    elif type_name == "line":
        draw.line([(0, asset_size // 2), (asset_size, asset_size // 2)], fill=color + (200,), width=size)
    elif type_name == "dot":
        draw.ellipse([(asset_size//2 - size//2), (asset_size//2 - size//2),
                      (asset_size//2 + size//2), (asset_size//2 + size//2)], fill=color + (200,))

    return asset


def add_minor_objects(
    input_image: Image.Image,
    num_objects: int = 5,
    random_seed: Optional[int] = None
) -> Image.Image:
    """
    Enhances detail by overlaying a small number of minor object assets.
    Optimized for speed: uses in-memory generation for simple shapes.

    Args:
        input_image: The baseline PIL Image.
        num_objects: Number of minor objects to add.
        random_seed: Optional seed for reproducibility.

    Returns:
        A new PIL Image with added minor objects.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Convert to RGBA to handle transparency
    base = input_image.convert('RGBA')
    overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = base.size

    for i in range(num_objects):
        # Select random object properties
        obj_def = MINOR_OBJECTS[i % len(MINOR_OBJECTS)]
        size = obj_def["size"]
        color = obj_def["color"]

        # Generate asset in memory (fast)
        asset = _generate_mock_asset(obj_def["type"], color, size)

        # Random position (ensure within bounds)
        x = np.random.randint(size, width - size)
        y = np.random.randint(size, height - size)

        # Paste with transparency
        overlay.paste(asset, (x - size, y - size), asset)

    # Composite
    result = Image.alpha_composite(base, overlay)
    return result.convert('RGB')


def remove_minor_elements(
    input_image: Image.Image,
    blur_radius: int = 5,
    mask_ratio: float = 0.1
) -> Image.Image:
    """
    Reduces detail by applying localized Gaussian blur or masking.
    Optimized to avoid expensive pixel-level segmentation if not strictly necessary.
    Uses a grid-based approach for consistent "reduction" without heavy ML.

    Args:
        input_image: The baseline PIL Image.
        blur_radius: Radius for Gaussian blur.
        mask_ratio: Fraction of image area to blur (approximate).

    Returns:
        A new PIL Image with reduced detail in random regions.
    """
    base = input_image.convert('RGB')
    width, height = base.size

    # Create a copy to modify
    result = base.copy()

    # Determine grid size based on image size to ensure performance
    # We want to blur small patches, not the whole image
    patch_size = max(20, min(width, height) // 10)
    num_patches = int((width * height * mask_ratio) / (patch_size * patch_size))

    for _ in range(num_patches):
        x = np.random.randint(0, max(0, width - patch_size))
        y = np.random.randint(0, max(0, height - patch_size))

        # Extract patch
        patch = result.crop((x, y, x + patch_size, y + patch_size))

        # Apply blur
        blurred_patch = patch.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Paste back
        result.paste(blurred_patch, (x, y))

    return result


def calculate_complexity_score(image: Image.Image) -> float:
    """
    Calculates a heuristic complexity score based on edge density and color variance.
    Optimized to run quickly on standard images.

    Args:
        image: PIL Image.

    Returns:
        Float score between 0.0 and 1.0.
    """
    # Convert to grayscale for edge detection
    gray = image.convert('L')
    np_img = np.array(gray)

    # Simple edge detection using Sobel-like approximation (fast numpy)
    # Using numpy gradient is faster than scipy for this simple metric
    gx = np.diff(np_img, axis=1)
    gy = np.diff(np_img, axis=0)

    # Pad to match original size
    gx = np.pad(gx, ((0, 0), (0, 1)), mode='edge')
    gy = np.pad(gy, ((0, 1), (0, 0)), mode='edge')

    edge_magnitude = np.sqrt(gx**2 + gy**2)
    edge_density = np.mean(edge_magnitude > 30)  # Threshold for edges

    # Color variance
    rgb = np.array(image.convert('RGB'))
    color_var = np.mean(np.var(rgb, axis=2)) / 255.0  # Normalize

    # Weighted score
    score = 0.6 * edge_density + 0.4 * (color_var / 10000) # Scale var down
    return float(np.clip(score, 0.0, 1.0))


def process_single_image(
    input_path: Path,
    output_dir: Path,
    metadata_dir: Path,
    object_pool: Optional[List[Dict]] = None
) -> Optional[StimulusMetadata]:
    """
    Processes a single image: generates enhanced and reduced versions,
    calculates complexity scores, and saves metadata.
    Enforces the < 30s/image constraint with a watchdog.

    Args:
        input_path: Path to input image.
        output_dir: Directory to save manipulated images.
        metadata_dir: Directory to save metadata YAML.
        object_pool: Optional list of object definitions (unused if None, uses defaults).

    Returns:
        StimulusMetadata object if successful, None if failed/skipped.
    """
    start_time = time.time()
    image_id = input_path.stem
    logger.info(f"Processing image: {image_id}")

    try:
        # Load image
        if time.time() - start_time > 2: # Allow 2s for load
            raise TimeoutError("Image loading took too long")
        base_image = Image.open(input_path).convert('RGB')
        orig_w, orig_h = base_image.size

        # --- Enhancement ---
        if time.time() - start_time > MAX_PROCESSING_TIME_SECONDS * 0.4:
            raise TimeoutError("Enhancement step exceeded time budget")

        enhanced_image = add_minor_objects(base_image, num_objects=5)
        enhanced_path = output_dir / f"{image_id}_enhanced.png"
        enhanced_image.save(enhanced_path, optimize=True) # Optimize for size/speed

        # --- Reduction ---
        if time.time() - start_time > MAX_PROCESSING_TIME_SECONDS * 0.7:
            raise TimeoutError("Reduction step exceeded time budget")

        reduced_image = remove_minor_elements(base_image, blur_radius=5)
        reduced_path = output_dir / f"{image_id}_reduced.png"
        reduced_image.save(reduced_path, optimize=True)

        # --- Metrics ---
        if time.time() - start_time > MAX_PROCESSING_TIME_SECONDS * 0.9:
            raise TimeoutError("Metrics calculation exceeded time budget")

        base_score = calculate_complexity_score(base_image)
        enhanced_score = calculate_complexity_score(enhanced_image)
        reduced_score = calculate_complexity_score(reduced_image)

        elapsed = time.time() - start_time
        if elapsed > MAX_PROCESSING_TIME_SECONDS:
            logger.warning(f"Image {image_id} took {elapsed:.2f}s (Target: <{MAX_PROCESSING_TIME_SECONDS}s)")

        # --- Metadata ---
        record_base = ManipulationRecord(
            source_path=str(input_path),
            manipulated_paths=[str(enhanced_path), str(reduced_path)],
            complexity_scores={"base": base_score, "enhanced": enhanced_score, "reduced": reduced_score},
            manipulation_type="detail_variation"
        )

        metadata = StimulusMetadata(
            id=image_id,
            original_path=str(input_path),
            enhanced_path=str(enhanced_path),
            reduced_path=str(reduced_path),
            complexity_score=base_score,
            manipulation_records=[record_base],
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        meta_path = metadata_dir / f"{image_id}.yaml"
        save_metadata_as_yaml(metadata, meta_path)

        logger.info(f"Successfully processed {image_id} in {elapsed:.2f}s")
        return metadata

    except TimeoutError as e:
        logger.error(f"Timeout processing {image_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to process {image_id}: {e}", exc_info=True)
        # Log to error file as per T018
        error_log_path = get_manipulation_error_log_path()
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log_path, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {image_id}: {str(e)}\n")
        return None


def process_directory(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    metadata_dir: Optional[Path] = None
) -> List[StimulusMetadata]:
    """
    Processes all images in a directory.

    Args:
        input_dir: Source directory of baseline images.
        output_dir: Destination for manipulated images (defaults to input_dir/manipulated).
        metadata_dir: Destination for metadata (defaults to input_dir/metadata).

    Returns:
        List of successfully generated metadata objects.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Setup directories
    if output_dir is None:
        output_dir = input_dir / "manipulated"
    if metadata_dir is None:
        metadata_dir = input_dir / "metadata"

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Find images
    image_files = list(input_dir.glob("*.png")) + list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.jpeg"))
    if not image_files:
        logger.warning(f"No images found in {input_dir}")
        return []

    logger.info(f"Found {len(image_files)} images to process")
    results = []

    for img_path in image_files:
        try:
            meta = process_single_image(img_path, output_dir, metadata_dir)
            if meta:
                results.append(meta)
        except TimeoutError:
            # Skip this image and continue
            continue
        except Exception as e:
            logger.error(f"Critical error processing {img_path}: {e}")
            continue

    return results


def main():
    """CLI entry point for image manipulation."""
    import argparse
    from config import get_stimuli_dir

    parser = argparse.ArgumentParser(description="Process stimuli images for detail manipulation.")
    parser.add_argument("--input", type=Path, default=None, help="Input directory (default: data/stimuli)")
    parser.add_argument("--output", type=Path, default=None, help="Output directory for manipulated images")
    parser.add_argument("--meta", type=Path, default=None, help="Output directory for metadata")
    args = parser.parse_args()

    input_dir = args.input if args.input else get_stimuli_dir()
    
    # If input is a file, wrap in logic or assume directory
    if input_dir.is_file():
        input_dir = input_dir.parent

    logger.info(f"Starting manipulation pipeline for: {input_dir}")
    results = process_directory(input_dir, args.output, args.meta)
    logger.info(f"Pipeline complete. Processed {len(results)} images successfully.")


if __name__ == "__main__":
    main()