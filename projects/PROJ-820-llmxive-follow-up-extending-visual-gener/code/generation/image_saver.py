"""
Module for saving generated images to disk in the required directory structure.
Handles directory creation and file I/O for the generation pipeline.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import PIL for image handling
try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow is required. Install with: pip install pillow")

# Import logging configuration from utils if available, otherwise use standard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageSaveError(Exception):
    """Custom exception for image saving errors."""
    pass


def save_image(
    image: Union[Image.Image, Dict[str, Any]],
    output_path: Path,
    group: str,
    scene_id: str
) -> None:
    """
    Save a single generated image to the specified output path.

    Args:
        image: PIL Image object or a dictionary containing image data.
               If dict, expects a 'image' key with the PIL Image.
        output_path: Full path where the image should be saved.
        group: The group name (e.g., 'baseline', 'experimental', 'control').
        scene_id: The unique identifier for the scene.

    Raises:
        ImageSaveError: If the image cannot be saved or path creation fails.
    """
    try:
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle dictionary input
        if isinstance(image, dict):
            if 'image' not in image:
                raise ImageSaveError(f"Dictionary input missing 'image' key for {scene_id} in {group}")
            pil_image = image['image']
        elif isinstance(image, Image.Image):
            pil_image = image
        else:
            raise ImageSaveError(f"Unsupported image type: {type(image)} for {scene_id} in {group}")

        # Ensure the image is in a saveable format (e.g., RGB)
        if pil_image.mode not in ('RGB', 'RGBA', 'L'):
            # Convert to RGB if possible, otherwise keep as is
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            elif pil_image.mode == 'P':
                pil_image = pil_image.convert('RGB')

        # Save the image
        pil_image.save(output_path, format='PNG')
        logger.info(f"Saved image: {output_path} ({pil_image.size})")

    except Exception as e:
        logger.error(f"Failed to save image for {scene_id} in {group}: {str(e)}")
        raise ImageSaveError(f"Failed to save image for {scene_id} in {group}: {str(e)}") from e


def save_batch_images(
    images_data: List[Dict[str, Any]],
    base_output_dir: Path,
    group: str
) -> List[str]:
    """
    Save a batch of generated images to the specified base output directory.

    Args:
        images_data: List of dictionaries, each containing:
            - 'scene_id': Unique scene identifier
            - 'image': PIL Image object or dict with 'image' key
            - (Optional) 'prompt': The prompt used for generation
        base_output_dir: Base directory for this group (e.g., 'data/derived/generated_images/baseline')
        group: The group name (e.g., 'baseline', 'experimental', 'control')

    Returns:
        List of successfully saved file paths.

    Raises:
        ImageSaveError: If any image fails to save.
    """
    saved_paths = []
    failed_scenes = []

    for item in images_data:
        scene_id = item.get('scene_id')
        if not scene_id:
            logger.warning("Skipping item with missing scene_id")
            continue

        image = item.get('image')
        if not image:
            logger.warning(f"Skipping scene {scene_id} in {group}: missing image data")
            continue

        # Construct the full output path
        output_path = base_output_dir / f"{scene_id}.png"

        try:
            save_image(image, output_path, group, scene_id)
            saved_paths.append(str(output_path))
        except ImageSaveError as e:
            failed_scenes.append(scene_id)
            logger.error(f"Failed to save {scene_id}: {str(e)}")
            # Continue with other images instead of failing the whole batch

    if failed_scenes:
        logger.warning(f"Failed to save {len(failed_scenes)} images: {failed_scenes}")
        # Note: We don't raise here to allow partial success, but the calling function
        # should check the returned list against the input list

    return saved_paths


def main() -> None:
    """
    Main entry point for standalone execution of image saving.
    This is useful for testing the image saver module independently.
    """
    logger.info("Image Saver Module - Standalone Execution")
    logger.info("This module is designed to be imported and used by diffusion_runner.py")
    logger.info("For standalone testing, please run the diffusion pipeline instead.")

    # Example usage demonstration (not executed in production)
    if len(sys.argv) > 1:
        logger.info(f"Arguments provided: {sys.argv[1:]}")
        logger.info("Use this module via: from generation.image_saver import save_image, save_batch_images")


if __name__ == "__main__":
    main()
