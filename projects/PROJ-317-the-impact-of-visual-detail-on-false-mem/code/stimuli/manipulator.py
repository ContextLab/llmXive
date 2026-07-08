import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import yaml

from config import get_stimuli_dir, get_stimuli_metadata_dir, get_project_root
from data.image import Image as ImageEntity
from data.metadata import save_metadata_as_yaml # Assuming metadata module exists or we define it here if missing
# Note: The API surface says 'from stimuli.metadata import ...' so we assume that module exists.
# If not, we might need to create it, but the task T013 implies we are testing the pipeline,
# so we assume the dependencies (manipulator, metadata) are present or created in other tasks.
# However, looking at the API surface provided:
# code/stimuli/metadata.py exists: from stimuli.metadata import ...
# So we import from there.

from stimuli.metadata import generate_metadata_for_image, save_metadata_as_yaml

logger = logging.getLogger(__name__)

def add_minor_objects(img: Image.Image, object_count: int = 5) -> Tuple[Image.Image, int]:
    """
    Overlay minor objects onto the image to enhance detail.
    
    Args:
        img: Input PIL Image.
        object_count: Number of minor objects to add.
        
    Returns:
        Tuple of (modified_image, actual_object_count_added).
    """
    draw = ImageDraw.Draw(img)
    width, height = img.size
    added_count = 0
    
    for _ in range(object_count):
        # Random position and size
        x1 = random.randint(0, width - 20)
        y1 = random.randint(0, height - 20)
        x2 = x1 + random.randint(5, 20)
        y2 = y1 + random.randint(5, 20)
        
        # Random color
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Draw a small shape (rectangle or ellipse)
        if random.random() > 0.5:
            draw.ellipse([x1, y1, x2, y2], fill=color)
        else:
            draw.rectangle([x1, y1, x2, y2], fill=color)
        
        added_count += 1
        
    return img, added_count

def remove_minor_elements(img: Image.Image, mask_area: float = 0.1) -> Image.Image:
    """
    Remove minor elements by blurring or masking a portion of the image.
    
    Args:
        img: Input PIL Image.
        mask_area: Fraction of the image to blur (approximate).
        
    Returns:
        Modified PIL Image with reduced detail.
    """
    width, height = img.size
    # Create a mask for the area to blur
    # We'll simply blur a random region to simulate removal of minor elements
    # Or apply a global mild blur which is safer for synthetic data
    
    # Strategy: Apply Gaussian blur to the whole image with a radius that reduces high-frequency detail
    # but keeps the main structure. Radius=5 as per task description.
    blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
    
    return blurred

def calculate_complexity_score(img: Image.Image) -> float:
    """
    Calculate a complexity score for an image.
    
    Args:
        img: Input PIL Image.
        
    Returns:
        Complexity score between 0 and 1.
    """
    # Convert to numpy array
    arr = np.array(img)
    
    # Use variance of colors as a proxy for complexity
    variance = np.var(arr)
    
    # Normalize to 0-1 range (assuming variance is roughly 0-255^2)
    # This is a heuristic.
    score = min(1.0, variance / (255.0 ** 2 * 3))
    return score

def process_single_image(input_path: Path, output_dir: Path, metadata_dir: Path) -> Optional[ImageEntity]:
    """
    Process a single image: generate enhanced and reduced versions, and metadata.
    
    Args:
        input_path: Path to the input image.
        output_dir: Directory to save manipulated images.
        metadata_dir: Directory to save metadata.
        
    Returns:
        ImageEntity if successful, None otherwise.
    """
    import random
    try:
        img = Image.open(input_path)
        img_id = input_path.stem
        
        # 1. Enhanced Detail
        enhanced_img, added_count = add_minor_objects(img.copy(), object_count=5)
        enhanced_path = output_dir / f"{img_id}_enhanced.png"
        enhanced_img.save(enhanced_path)
        
        # 2. Reduced Detail
        reduced_img = remove_minor_elements(img.copy())
        reduced_path = output_dir / f"{img_id}_reduced.png"
        reduced_img.save(reduced_path)
        
        # 3. Calculate Complexity Scores
        base_score = calculate_complexity_score(img)
        enhanced_score = calculate_complexity_score(enhanced_img)
        reduced_score = calculate_complexity_score(reduced_img)
        
        # 4. Generate Metadata
        metadata = generate_metadata_for_image(
            image_id=img_id,
            original_path=str(input_path),
            enhanced_path=str(enhanced_path),
            reduced_path=str(reduced_path),
            original_score=base_score,
            enhanced_score=enhanced_score,
            reduced_score=reduced_score,
            manipulation_details={
                "enhanced": {"objects_added": added_count},
                "reduced": {"blur_radius": 5}
            }
        )
        
        metadata_path = metadata_dir / f"{img_id}.yaml"
        save_metadata_as_yaml(metadata, metadata_path)
        
        logger.info(f"Processed {img_id}: Enhanced={enhanced_path}, Reduced={reduced_path}, Metadata={metadata_path}")
        
        return ImageEntity(
            id=img_id,
            path=str(input_path),
            complexity_score=base_score,
            metadata_path=str(metadata_path)
        )
        
    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}")
        # Log to error log file as per T018
        error_log_path = Path(get_project_root()) / "data" / "logs" / "manipulation_errors.log"
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log_path, 'a') as f:
            f.write(f"{time.time()}: Failed to process {input_path}: {e}\n")
        return None

def process_directory(input_dir: str, output_dir: str, metadata_dir: str):
    """
    Process all images in a directory.
    
    Args:
        input_dir: Directory containing input images.
        output_dir: Directory to save manipulated images.
        metadata_dir: Directory to save metadata.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    metadata_path = Path(metadata_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    metadata_path.mkdir(parents=True, exist_ok=True)
    
    images = list(input_path.glob("*.png")) + list(input_path.glob("*.jpg"))
    
    if not images:
        logger.warning(f"No images found in {input_dir}")
        return
    
    logger.info(f"Processing {len(images)} images...")
    
    for img_path in images:
        process_single_image(img_path, output_path, metadata_path)
        
    logger.info("Processing complete.")

def main():
    """Main entry point for the manipulator."""
    logging.basicConfig(level=logging.INFO)
    input_dir = str(get_stimuli_dir())
    output_dir = str(get_stimuli_dir() / "manipulated")
    metadata_dir = str(get_stimuli_metadata_dir())
    
    process_directory(input_dir, output_dir, metadata_dir)

if __name__ == "__main__":
    main()
