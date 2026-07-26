"""
Serialization module for the synthetic data pipeline.
Saves generated images and their corresponding JSON annotation files
(including derived geometric relations) to the data/synthetic/ directory.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from PIL import Image

from config import get_data_path, ensure_directories
from synthetic.validator import validate_synthetic_image_file


def save_image(image_array: np.ndarray, output_path: Path) -> None:
    """
    Saves a numpy array as a PNG image.

    Args:
        image_array: A numpy array of shape (H, W, C) or (H, W).
        output_path: The full path where the image should be saved.
    """
    if image_array.dtype != np.uint8:
        # Normalize float arrays to 0-255 range if necessary
        if image_array.max() <= 1.0:
            image_array = (image_array * 255).astype(np.uint8)
        else:
            image_array = image_array.astype(np.uint8)

    img = Image.fromarray(image_array)
    img.save(output_path)


def save_annotations(
    annotations: List[Dict[str, Any]],
    image_path: Path,
    output_path: Path
) -> None:
    """
    Saves a list of annotation dictionaries to a JSON file.
    The JSON structure includes bounding boxes and derived geometric relations.

    Args:
        annotations: List of dicts containing box data and derived relations.
        image_path: Path to the associated image (stored in JSON for reference).
        output_path: The full path where the JSON file should be saved.
    """
    # Ensure the image path is relative or stored consistently
    relative_image_path = str(image_path.relative_to(Path(get_data_path("synthetic"))))

    record = {
        "image_file": relative_image_path,
        "annotations": annotations
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2)


def serialize_synthetic_sample(
    image_array: np.ndarray,
    annotations: List[Dict[str, Any]],
    region_count: int,
    source_id: str,
    output_dir: Optional[Path] = None
) -> tuple[Path, Path]:
    """
    Orchestrates the saving of a single synthetic sample (image + JSON).

    Args:
        image_array: The generated image as a numpy array.
        annotations: List of annotation dicts (boxes + derived relations).
        region_count: Number of regions in the image (used for naming).
        source_id: Unique identifier for the source image (used for naming).
        output_dir: Optional override for the output directory. Defaults to data/synthetic/.

    Returns:
        A tuple of (image_path, json_path).

    Raises:
        ValueError: If validation of the generated JSON structure fails.
        IOError: If file writing fails.
    """
    if output_dir is None:
        output_dir = Path(get_data_path("synthetic"))

    ensure_directories([output_dir])

    # Generate unique filenames
    # Sanitize source_id to be filesystem safe
    safe_source_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(source_id))
    image_filename = f"sample_{safe_source_id}_n{region_count}.png"
    json_filename = f"sample_{safe_source_id}_n{region_count}.json"

    image_path = output_dir / image_filename
    json_path = output_dir / json_filename

    # Save image
    save_image(image_array, image_path)

    # Save annotations
    save_annotations(annotations, image_path, json_path)

    # Validate the saved JSON file against the schema
    # Note: validate_synthetic_image_file expects a path to the JSON file
    if not validate_synthetic_image_file(json_path):
        raise ValueError(f"Validation failed for generated annotations at {json_path}")

    return image_path, json_path


def main():
    """
    Entry point for standalone testing of the serializer.
    Generates dummy data to verify the save/load cycle.
    """
    import tempfile
    import shutil

    print("Running serializer self-test...")

    # Create a temporary directory for testing
    test_dir = Path(tempfile.mkdtemp())
    try:
        # Mock data
        dummy_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        dummy_annotations = [
            {
                "box": [10, 10, 50, 50],
                "label": "object_1",
                "relations": [{"relation": "left_of", "target": "object_2"}]
            },
            {
                "box": [60, 10, 90, 50],
                "label": "object_2",
                "relations": [{"relation": "right_of", "target": "object_1"}]
            }
        ]

        img_path, json_path = serialize_synthetic_sample(
            image_array=dummy_image,
            annotations=dummy_annotations,
            region_count=2,
            source_id="test_001",
            output_dir=test_dir
        )

        print(f"Image saved to: {img_path}")
        print(f"JSON saved to: {json_path}")

        # Verify files exist
        assert img_path.exists(), "Image file not found"
        assert json_path.exists(), "JSON file not found"

        # Verify JSON content
        with open(json_path, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data["image_file"].endswith(".png"), "Image path mismatch"
        assert len(loaded_data["annotations"]) == 2, "Annotation count mismatch"

        print("Self-test passed successfully.")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    main()