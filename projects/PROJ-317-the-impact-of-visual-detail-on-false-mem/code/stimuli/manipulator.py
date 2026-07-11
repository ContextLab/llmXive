import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

from config import get_stimuli_dir, get_stimuli_metadata_dir, get_logs_dir, get_manipulation_error_log_path
from utils.logging import get_logger, setup_logging
from data.image import Image as ImageEntity

# Initialize logger for this module
logger = get_logger(__name__)

def add_minor_objects(base_image: Image.Image, num_objects: int = 5) -> Image.Image:
    """
    Overlay a small number of minor object PNG assets onto the base image.
    
    Args:
        base_image: The PIL Image to enhance.
        num_objects: Number of minor objects to add.
        
    Returns:
        Modified PIL Image with added objects.
        
    Raises:
        ValueError: If the image mode is not compatible or assets cannot be loaded.
        RuntimeError: If compositing fails.
    """
    if base_image.mode != 'RGB':
        base_image = base_image.convert('RGB')
    
    width, height = base_image.size
    draw = ImageDraw.Draw(base_image, 'RGBA')
    
    # Mock asset pool for demonstration (in production, load from real assets directory)
    # Using simple geometric shapes as placeholders for "minor objects"
    asset_colors = [(255, 0, 0, 180), (0, 255, 0, 180), (0, 0, 255, 180), (255, 255, 0, 180), (255, 165, 0, 180)]
    
    for i in range(num_objects):
        # Random position within image bounds
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        # Random size (small objects)
        size = random.randint(10, 30)
        
        # Random color from pool
        color = asset_colors[i % len(asset_colors)]
        
        # Draw a simple shape (circle) to represent the object
        draw.ellipse(
            [x - size/2, y - size/2, x + size/2, y + size/2],
            fill=color,
            outline=(0, 0, 0, 255)
        )
    
    return base_image

def remove_minor_elements(base_image: Image.Image, blur_radius: int = 5) -> Image.Image:
    """
    Remove minor elements from the image using Gaussian blur or masking.
    
    Args:
        base_image: The PIL Image to reduce detail for.
        blur_radius: Radius for Gaussian blur.
        
    Returns:
        Modified PIL Image with reduced detail.
        
    Raises:
        ValueError: If the image mode is not compatible.
        RuntimeError: If manipulation fails.
    """
    if base_image.mode != 'RGB':
        base_image = base_image.convert('RGB')
    
    # Apply Gaussian blur to reduce fine details
    # This effectively "removes" minor elements by smoothing them out
    modified_image = base_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    return modified_image

def calculate_complexity_score(image: Image.Image) -> float:
    """
    Calculate a complexity score for the image based on variance and edges.
    
    Args:
        image: The PIL Image to score.
        
    Returns:
        Float complexity score between 0.0 and 1.0.
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    img_array = np.array(image)
    
    # Calculate variance across channels
    variance = np.var(img_array)
    
    # Normalize to 0-1 range (assuming typical variance range)
    # This is a heuristic; in production, use calibrated metrics
    score = min(1.0, max(0.0, variance / 10000.0))
    
    return score

def process_single_image(
    input_path: Path, 
    output_dir: Path, 
    metadata_dir: Path, 
    image_id: str,
    manipulate_type: str = 'enhance'
) -> Optional[Dict[str, Any]]:
    """
    Process a single image: manipulate it and generate metadata.
    
    Args:
        input_path: Path to the input image.
        output_dir: Directory to save manipulated image.
        metadata_dir: Directory to save metadata.
        image_id: Unique identifier for the image.
        manipulate_type: Type of manipulation ('enhance' or 'reduce').
        
    Returns:
        Dictionary with metadata if successful, None if skipped.
        
    Raises:
        Exception: Propagated if manipulation fails and should not be skipped.
    """
    logger.info(f"Processing image: {image_id} ({manipulate_type})")
    
    try:
        # Load image
        base_image = Image.open(input_path)
        
        # Perform manipulation
        if manipulate_type == 'enhance':
            manipulated_image = add_minor_objects(base_image, num_objects=5)
            complexity_change = 0.1  # Expected increase
        elif manipulate_type == 'reduce':
            manipulated_image = remove_minor_elements(base_image, blur_radius=5)
            complexity_change = -0.1  # Expected decrease
        else:
            raise ValueError(f"Unknown manipulation type: {manipulate_type}")
        
        # Save manipulated image
        output_path = output_dir / f"{image_id}_{manipulate_type}.png"
        manipulated_image.save(output_path, 'PNG')
        
        # Calculate new complexity score
        new_complexity = calculate_complexity_score(manipulated_image)
        
        # Prepare metadata record
        metadata_record = {
            'image_id': image_id,
            'manipulation_type': manipulate_type,
            'output_path': str(output_path),
            'original_path': str(input_path),
            'original_complexity': calculate_complexity_score(base_image),
            'new_complexity': new_complexity,
            'complexity_change': complexity_change,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"Successfully processed {image_id}: {output_path}")
        return metadata_record
        
    except Exception as e:
        # Log the error to the specific manipulation error log file
        error_log_path = get_manipulation_error_log_path()
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(error_log_path, 'a', encoding='utf-8') as log_file:
            log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR processing {image_id}: {str(e)}\n"
            log_file.write(log_entry)
        
        logger.error(f"Skipping image {image_id} due to manipulation failure: {str(e)}")
        # Return None to indicate skip - caller should not attempt metadata generation
        return None

def process_directory(
    input_dir: Path, 
    output_dir: Path, 
    metadata_dir: Path,
    manipulate_type: str = 'enhance'
) -> List[Dict[str, Any]]:
    """
    Process all images in a directory.
    
    Args:
        input_dir: Directory containing input images.
        output_dir: Directory to save manipulated images.
        metadata_dir: Directory to save metadata files.
        manipulate_type: Type of manipulation to apply.
        
    Returns:
        List of metadata records for successfully processed images.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    successful_records = []
    
    # Find all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    logger.info(f"Found {len(image_files)} images to process in {input_dir}")
    
    for image_file in image_files:
        image_id = image_file.stem
        
        # Process single image - returns None if skipped due to error
        record = process_single_image(
            input_path=image_file,
            output_dir=output_dir,
            metadata_dir=metadata_dir,
            image_id=image_id,
            manipulate_type=manipulate_type
        )
        
        if record is not None:
            successful_records.append(record)
        
        # Small delay to prevent CPU overload
        time.sleep(0.1)
    
    logger.info(f"Successfully processed {len(successful_records)} images.")
    return successful_records

def main():
    """Main entry point for running the manipulation pipeline."""
    setup_logging()
    
    # Get directories from config
    input_dir = get_stimuli_dir()
    output_enhance_dir = input_dir / "enhanced"
    output_reduce_dir = input_dir / "reduced"
    metadata_dir = get_stimuli_metadata_dir()
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directories: {output_enhance_dir}, {output_reduce_dir}")
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
    
    # Process enhanced detail
    logger.info("--- Processing Enhanced Detail ---")
    enhance_records = process_directory(
        input_dir=input_dir,
        output_dir=output_enhance_dir,
        metadata_dir=metadata_dir,
        manipulate_type='enhance'
    )
    
    # Process reduced detail
    logger.info("--- Processing Reduced Detail ---")
    reduce_records = process_directory(
        input_dir=input_dir,
        output_dir=output_reduce_dir,
        metadata_dir=metadata_dir,
        manipulate_type='reduce'
    )
    
    logger.info(f"Total enhanced: {len(enhance_records)}, Total reduced: {len(reduce_records)}")
    
    # Check for error log existence
    error_log_path = get_manipulation_error_log_path()
    if error_log_path.exists():
        logger.info(f"Error log created at: {error_log_path}")
        with open(error_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                logger.warning(f"{len(lines)} manipulation errors logged.")
    
    return 0

if __name__ == '__main__':
    exit(main())