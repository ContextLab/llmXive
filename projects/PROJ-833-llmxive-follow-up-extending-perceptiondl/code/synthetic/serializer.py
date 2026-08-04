"""
code/synthetic/serializer.py

Handles saving generated images and JSON annotation files.
Includes derived geometric relations as mandated by FR-004.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image

def save_image(image: Any, path: str):
    """
    Save an image to disk.
    Handles PIL Images and numpy arrays.
    """
    if isinstance(image, np.ndarray):
        img = Image.fromarray(image)
    elif isinstance(image, Image.Image):
        img = image
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")
    
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path)

def save_annotations(annotations: Dict[str, Any], path: str):
    """Save annotations to a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(annotations, f, indent=2)

def serialize_synthetic_sample(
    image: Any,
    boxes: List[Dict[str, Any]],
    relations: List[str],
    output_dir: str,
    filename_prefix: str
) -> Tuple[str, str]:
    """
    Full serialization of a synthetic sample.
    Saves the image and a JSON file containing bounding boxes and derived relations.
    
    Args:
        image: PIL Image or numpy array to save.
        boxes: List of bounding box dictionaries (x, y, w, h, id).
        relations: List of derived spatial relation strings (e.g., "left of").
        output_dir: Directory to save files into.
        filename_prefix: Prefix for the output filenames.
        
    Returns:
        Tuple of (image_path, json_path).
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    image_path = os.path.join(output_dir, f"{filename_prefix}.png")
    json_path = os.path.join(output_dir, f"{filename_prefix}.json")

    save_image(image, image_path)

    annotations = {
        "image_path": image_path,
        "bounding_boxes": boxes,
        "derived_relations": relations,
        "metadata": {
            "filename": f"{filename_prefix}",
            "count": len(boxes)
        }
    }
    save_annotations(annotations, json_path)

    return image_path, json_path

def main():
    """Test serializer with a real file write."""
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    boxes = [{'x': 10, 'y': 10, 'w': 20, 'h': 20, 'id': 0}]
    relations = ["test relation"]
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        p1, p2 = serialize_synthetic_sample(img, boxes, relations, tmpdir, "test_serialization")
        print(f"Saved image to: {p1}")
        print(f"Saved annotations to: {p2}")
        
        # Verify files exist
        assert os.path.exists(p1), "Image file was not created"
        assert os.path.exists(p2), "JSON file was not created"
        
        # Verify JSON content
        with open(p2, 'r') as f:
            data = json.load(f)
            assert "derived_relations" in data, "derived_relations missing from JSON"
            assert data["derived_relations"] == relations, "relations mismatch"
            
    print("Serializer test passed.")

if __name__ == "__main__":
    main()