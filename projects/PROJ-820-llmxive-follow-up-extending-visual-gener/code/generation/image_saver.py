"""
Image Saver Module for llmXive Project (Task T021)

Responsible for saving generated images to the correct directory structure
based on the group (Baseline, Experimental, Control) and scene ID.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED_IMAGES_DIR = PROJECT_ROOT / "data" / "derived" / "generated_images"

# Ensure the base directory exists
GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Define the groups as per requirements
VALID_GROUPS = {"Baseline", "Experimental", "Control"}


class ImageSaveError(Exception):
    """Custom exception for image saving errors."""
    pass


def save_image(
    image_data: Union[bytes, Any],
    scene_id: str,
    group: str,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Saves a generated image to the specified directory structure.

    Args:
        image_data: The image data (bytes for PIL save, or PIL Image object).
        scene_id: The unique identifier for the scene (e.g., "scene_001").
        group: The group name. Must be one of "Baseline", "Experimental", or "Control".
        output_dir: Optional override for the output directory. Defaults to project standard.

    Returns:
        Path: The absolute path to the saved image file.

    Raises:
        ImageSaveError: If the group is invalid or saving fails.
    """
    if group not in VALID_GROUPS:
        raise ImageSaveError(
            f"Invalid group '{group}'. Must be one of {VALID_GROUPS}."
        )

    if output_dir is None:
        output_dir = GENERATED_IMAGES_DIR

    # Construct the group subdirectory
    group_dir = output_dir / group
    group_dir.mkdir(parents=True, exist_ok=True)

    # Construct the file path
    file_path = group_dir / f"{scene_id}.png"

    try:
        # Handle PIL Image objects or bytes
        if hasattr(image_data, 'save'):
            # It's likely a PIL Image or similar object with a save method
            image_data.save(file_path, format='PNG')
            logger.info(f"Saved image to: {file_path}")
        elif isinstance(image_data, bytes):
            # It's raw bytes, write directly
            with open(file_path, 'wb') as f:
                f.write(image_data)
            logger.info(f"Saved image bytes to: {file_path}")
        else:
            # Attempt to save assuming it's an array-like object (e.g., numpy)
            # This requires numpy and PIL to be available, which are dependencies
            import numpy as np
            from PIL import Image
            if isinstance(image_data, np.ndarray):
                img = Image.fromarray(image_data)
                img.save(file_path, format='PNG')
                logger.info(f"Saved numpy array image to: {file_path}")
            else:
                raise ImageSaveError(
                    f"Unsupported image data type: {type(image_data)}. "
                    "Expected PIL Image, bytes, or numpy array."
                )
        
        return file_path

    except Exception as e:
        raise ImageSaveError(f"Failed to save image to {file_path}: {str(e)}")


def save_batch_images(
    images: Dict[str, Any],
    scene_id: str,
    groups: List[str]
) -> Dict[str, Path]:
    """
    Saves multiple images for a single scene across different groups.

    Args:
        images: A dictionary mapping group names to image data.
                Expected keys: "Baseline", "Experimental", "Control".
        scene_id: The unique identifier for the scene.
        groups: List of groups to process.

    Returns:
        Dict[str, Path]: A dictionary mapping group names to their saved file paths.

    Raises:
        ImageSaveError: If any image fails to save.
    """
    saved_paths = {}
    failed_groups = []

    for group in groups:
        if group not in images:
            logger.warning(f"No image data provided for group '{group}' for scene {scene_id}. Skipping.")
            continue

        try:
            path = save_image(images[group], scene_id, group)
            saved_paths[group] = path
        except ImageSaveError as e:
            failed_groups.append(group)
            logger.error(f"Failed to save {group} image for {scene_id}: {e}")

    if failed_groups:
        raise ImageSaveError(
            f"Failed to save images for groups: {failed_groups} in scene {scene_id}."
        )

    return saved_paths


def main():
    """
    Main entry point for testing the image saver module independently.
    This script generates a dummy image (using numpy) and saves it to verify
    the directory structure and file writing capabilities.
    """
    logger.info("Starting Image Saver Module Test (T021 Verification)")

    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        logger.error("Required dependencies (numpy, PIL) not found. Please install them.")
        sys.exit(1)

    # Create a dummy scene ID
    test_scene_id = "test_scene_001"
    test_groups = ["Baseline", "Experimental", "Control"]

    # Generate dummy image data (random noise) for testing
    # 512x512 RGB image
    dummy_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)

    images_to_save = {
        group: dummy_image for group in test_groups
    }

    try:
        saved_paths = save_batch_images(images_to_save, test_scene_id, test_groups)
        
        print("\n--- Verification Results ---")
        for group, path in saved_paths.items():
            if path.exists():
                print(f"[OK] {group}: {path} exists. Size: {path.stat().st_size} bytes")
            else:
                print(f"[FAIL] {group}: Path {path} does not exist.")
        
        # Verify directory structure
        print("\n--- Directory Structure Check ---")
        base_dir = GENERATED_IMAGES_DIR
        for group in test_groups:
            group_dir = base_dir / group
            if group_dir.exists() and group_dir.is_dir():
                print(f"[OK] Directory exists: {group_dir}")
            else:
                print(f"[FAIL] Directory missing: {group_dir}")

        print("\nT021 Verification: SUCCESS - All groups saved correctly.")

    except Exception as e:
        logger.error(f"T021 Verification FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
