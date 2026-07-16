import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

from config import get_data_dir, get_stimuli_dir, get_stimuli_metadata_dir, get_logs_dir
from utils.logging import get_logger, get_manipulation_error_log_path, sanitize_message
from data.image import Image as ImageEntity

# Initialize logger
logger = get_logger(__name__)

# Constants for manipulation
MINOR_OBJECT_SIZES = [(10, 10), (15, 15), (20, 20)]
MINOR_OBJECT_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
BLUR_RADIUS = 5
MINOR_OBJECT_COUNT = 5

def add_minor_objects(image: Image.Image, count: int = MINOR_OBJECT_COUNT) -> Image.Image:
    """
    Overlay a small number of minor object shapes (rectangles/circles) onto the image
    to simulate increased visual detail.
    """
    width, height = image.size
    draw = ImageDraw.Draw(image)

    for _ in range(count):
        # Random size
        size = random.choice(MINOR_OBJECT_SIZES)
        # Random position ensuring it stays within bounds
        x = random.randint(0, width - size[0])
        y = random.randint(0, height - size[1])
        # Random color
        color = random.choice(MINOR_OBJECT_COLORS)

        # Draw a simple shape (rectangle) to represent a minor object
        draw.rectangle([x, y, x + size[0], y + size[1]], fill=color)

    return image

def remove_minor_elements(image: Image.Image) -> Image.Image:
    """
    Apply Gaussian blur and/or masking to remove minor elements from the image.
    """
    # Apply Gaussian blur to smooth out minor details
    blurred = image.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    return blurred

def calculate_complexity_score(image: Image.Image) -> float:
    """
    Calculate a simple complexity score based on pixel variance and edge density.
    """
    img_array = np.array(image.convert('L'))
    variance = np.var(img_array)
    # Normalize variance to a 0-1 range (assuming typical 0-255 range)
    score = min(1.0, variance / (255 ** 2))
    return score

def process_single_image(
    input_path: Path,
    output_dir: Path,
    image_id: str,
    enhance: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Process a single image: load, manipulate, and save.
    Returns metadata dict on success, None on failure.
    """
    try:
        # Load image
        img = Image.open(input_path).convert('RGB')
        original_size = img.size
        original_complexity = calculate_complexity_score(img)

        # Apply manipulation
        if enhance:
            manipulated_img = add_minor_objects(img.copy())
            manipulation_type = "enhanced"
        else:
            manipulated_img = remove_minor_elements(img.copy())
            manipulation_type = "reduced"

        # Save manipulated image
        output_filename = f"{image_id}_{manipulation_type}.png"
        output_path = output_dir / output_filename
        manipulated_img.save(output_path)

        # Calculate new complexity
        new_complexity = calculate_complexity_score(manipulated_img)

        metadata = {
            "id": image_id,
            "original_path": str(input_path),
            "manipulated_path": str(output_path),
            "manipulation_type": manipulation_type,
            "original_size": original_size,
            "original_complexity": original_complexity,
            "new_complexity": new_complexity,
            "timestamp": time.time()
        }

        logger.info(f"Successfully processed image {image_id} ({manipulation_type})")
        return metadata

    except Exception as e:
        # CRITICAL: Log the error and return None to trigger skip logic
        error_msg = sanitize_message(f"Failed to process image {image_id} from {input_path}: {str(e)}")
        logger.error(error_msg)
        
        # Write to the specific manipulation error log file
        log_path = get_manipulation_error_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp_str}] ERROR: {error_msg}\n")
        
        return None

def process_directory(
    input_dir: Path,
    output_dir: Path,
    metadata_output_dir: Path,
    enhance: bool = True
) -> List[Dict[str, Any]]:
    """
    Process all images in the input directory.
    Implements 'skip and log' logic: if an image fails, it is skipped entirely.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    metadata_output_dir = Path(metadata_output_dir)

    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_output_dir.mkdir(parents=True, exist_ok=True)

    all_metadata = []
    processed_count = 0
    skipped_count = 0

    # Get list of image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in image_extensions]

    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return all_metadata

    for image_file in image_files:
        image_id = image_file.stem
        
        # Attempt processing
        result = process_single_image(image_file, output_dir, image_id, enhance)
        
        if result is None:
            # Skip logic: do not attempt metadata generation, just increment counter
            skipped_count += 1
            logger.warning(f"Skipping image {image_id} due to processing failure.")
        else:
            all_metadata.append(result)
            processed_count += 1

    logger.info(f"Processing complete. Success: {processed_count}, Skipped: {skipped_count}")
    return all_metadata

def main():
    """
    CLI entry point for running the manipulation pipeline.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manipulate stimuli images")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing baseline images")
    parser.add_argument("--output", type=str, required=True, help="Output directory for manipulated images")
    parser.add_argument("--metadata-output", type=str, required=True, help="Output directory for metadata files")
    parser.add_argument("--enhance", action="store_true", default=False, help="If set, enhance detail; otherwise reduce detail")
    
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    metadata_output_dir = Path(args.metadata_output)

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1

    # Setup logging
    setup_logging()

    # Run processing
    metadata_list = process_directory(input_dir, output_dir, metadata_output_dir, enhance=args.enhance)

    # Note: Metadata generation is handled separately by metadata.py task (T017)
    # This task focuses strictly on the manipulation and error handling logic.

    return 0

if __name__ == "__main__":
    exit(main())