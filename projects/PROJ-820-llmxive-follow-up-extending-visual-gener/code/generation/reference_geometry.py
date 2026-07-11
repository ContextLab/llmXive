"""
Reference Geometry Renderer for Visual Generation Study.

This module renders a "reference geometry" image by projecting bounding boxes
derived from Pymunk physics simulation JSON files onto a virtual 512x512 canvas.
This image serves as the ground truth for calculating SSIM similarity scores
against generated diffusion images in T022b.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Attempt to import PIL; if missing, this script cannot run image generation
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow (PIL) is required for reference geometry rendering.", file=sys.stderr)
    print("Install it via: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Project root configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_PHYSICS = PROJECT_ROOT / "data" / "derived" / "physics_constraints"
DATA_DERIVED_REF_GEOM = PROJECT_ROOT / "data" / "derived" / "reference_geometry"
CANVAS_SIZE = (512, 512)
DEFAULT_BACKGROUND_COLOR = (255, 255, 255)  # White
BOX_COLOR = (0, 0, 255)  # Blue for bounding boxes
BOX_WIDTH = 2


class ReferenceGeometryRenderError(Exception):
    """Custom exception for errors during reference geometry rendering."""
    pass


def load_physics_constraint(scene_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the physics constraint JSON for a specific scene ID.

    Args:
        scene_id: The unique identifier for the scene (e.g., 'scene_001').

    Returns:
        A dictionary containing the physics constraints, or None if the file
        or scene_id is not found.
    """
    file_path = DATA_DERIVED_PHYSICS / f"{scene_id}.json"
    
    if not file_path.exists():
        print(f"Warning: Physics constraint file not found for {scene_id} at {file_path}", file=sys.stderr)
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise ReferenceGeometryRenderError(f"Failed to parse JSON for {scene_id}: {e}")
    except Exception as e:
        raise ReferenceGeometryRenderError(f"Failed to load physics constraint for {scene_id}: {e}")


def extract_bounding_boxes(physics_data: Dict[str, Any]) -> List[Tuple[str, int, int, int, int]]:
    """
    Extract bounding box information from the physics constraint JSON.
    
    The JSON structure is expected to contain a list of objects under a key
    like 'objects' or 'entities', each having 'id', 'x', 'y', 'width', 'height'.
    Coordinates are assumed to be normalized (0.0 to 1.0) or pixel values relative
    to a 512x512 canvas. If normalized, they are scaled to 512.

    Returns:
        A list of tuples: (object_id, x, y, width, height).
    """
    objects = physics_data.get("objects", [])
    if not objects:
        # Some schemas might use 'entities'
        objects = physics_data.get("entities", [])
    
    if not objects:
        return []

    boxes = []
    for obj in objects:
        obj_id = obj.get("id", "unknown")
        
        # Handle both normalized (0-1) and pixel coordinates
        x = obj.get("x", 0)
        y = obj.get("y", 0)
        width = obj.get("width", 0)
        height = obj.get("height", 0)

        # If values are <= 1.0, assume normalized and scale to 512
        if width <= 1.0 and height <= 1.0:
            x = int(x * CANVAS_SIZE[0])
            y = int(y * CANVAS_SIZE[1])
            width = int(width * CANVAS_SIZE[0])
            height = int(height * CANVAS_SIZE[1])
        
        # Clamp values to canvas bounds
        x = max(0, min(x, CANVAS_SIZE[0] - 1))
        y = max(0, min(y, CANVAS_SIZE[1] - 1))
        width = max(1, min(width, CANVAS_SIZE[0] - x))
        height = max(1, min(height, CANVAS_SIZE[1] - y))

        boxes.append((obj_id, x, y, width, height))

    return boxes


def render_reference_geometry(
    scene_id: str, 
    output_dir: Optional[Path] = None
) -> Path:
    """
    Render a reference geometry image for a given scene ID.

    Args:
        scene_id: The scene identifier.
        output_dir: Optional directory to save the image. Defaults to 
                    data/derived/reference_geometry.

    Returns:
        The Path to the generated PNG file.
    
    Raises:
        ReferenceGeometryRenderError: If the physics data cannot be loaded or
                                      rendering fails.
    """
    if output_dir is None:
        output_dir = DATA_DERIVED_REF_GEOM
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{scene_id}.png"

    # Load physics data
    physics_data = load_physics_constraint(scene_id)
    if physics_data is None:
        raise ReferenceGeometryRenderError(f"No physics data found for scene {scene_id}.")

    # Extract boxes
    boxes = extract_bounding_boxes(physics_data)

    # Create canvas
    image = Image.new('RGB', CANVAS_SIZE, color=DEFAULT_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Draw bounding boxes
    for obj_id, x, y, w, h in boxes:
        # Draw rectangle outline
        draw.rectangle([x, y, x + w, y + h], outline=BOX_COLOR, width=BOX_WIDTH)
        
        # Optional: Draw a small label or just the box
        # For simplicity and clean SSIM comparison, we stick to clean boxes.
        # If text is needed, we would need a font object.

    # Save image
    try:
        image.save(output_path, "PNG")
    except Exception as e:
        raise ReferenceGeometryRenderError(f"Failed to save image to {output_path}: {e}")

    return output_path


def run_reference_geometry_generation(
    scene_ids: Optional[List[str]] = None
) -> Dict[str, Path]:
    """
    Generate reference geometry images for a list of scene IDs.

    Args:
        scene_ids: A list of scene IDs to process. If None, attempts to scan
                   the physics_constraints directory for all available JSON files.

    Returns:
        A dictionary mapping scene_id to the generated PNG path.
    """
    results = {}
    
    if scene_ids is None:
        # Scan directory for existing physics constraints
        if not DATA_DERIVED_PHYSICS.exists():
            raise ReferenceGeometryRenderError(f"Physics constraints directory not found: {DATA_DERIVED_PHYSICS}")
        
        json_files = list(DATA_DERIVED_PHYSICS.glob("*.json"))
        scene_ids = [f.stem for f in json_files]

    if not scene_ids:
        print("No scene IDs provided or found to process.")
        return results

    for scene_id in scene_ids:
        try:
            print(f"Generating reference geometry for {scene_id}...", end=" ")
            path = render_reference_geometry(scene_id)
            results[scene_id] = path
            print(f"Saved to {path}")
        except ReferenceGeometryRenderError as e:
            print(f"FAILED: {e}", file=sys.stderr)
        except Exception as e:
            print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)

    return results


def main():
    """
    Entry point for the script.
    Usage: python -m code.generation.reference_geometry [scene_id1 scene_id2 ...]
    If no arguments, processes all available physics constraints.
    """
    args = sys.argv[1:]
    scene_ids = args if args else None

    print(f"Starting Reference Geometry Generation for {len(scene_ids) if scene_ids else 'all'} scenes.")
    print(f"Output directory: {DATA_DERIVED_REF_GEOM}")
    
    results = run_reference_geometry_generation(scene_ids)
    
    if results:
        print(f"\nSuccessfully generated {len(results)} reference geometry images.")
    else:
        print("\nNo images were generated.")

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())