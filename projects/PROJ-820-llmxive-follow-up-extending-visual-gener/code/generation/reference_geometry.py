"""
Reference geometry rendering for T022-fallback.
Projects pymunk JSON bounding boxes onto a virtual canvas.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReferenceGeometryRenderError(Exception):
    """Base exception for reference geometry rendering errors."""
    pass

def load_physics_constraint(json_path: str) -> Dict:
    """Load physics constraint JSON file."""
    path = Path(json_path)
    if not path.exists():
        raise ReferenceGeometryRenderError(f"Constraint file not found: {json_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_bounding_boxes(constraints: Dict) -> List[Dict]:
    """Extract bounding boxes from physics constraints."""
    if 'bounding_boxes' not in constraints:
        return []
    return constraints['bounding_boxes']

def render_reference_geometry(
    bounding_boxes: List[Dict], 
    output_path: str, 
    canvas_size: Tuple[int, int] = (512, 512)
):
    """
    Render reference geometry by projecting bounding boxes onto a virtual canvas.
    Creates a simple visualization of object positions.
    """
    try:
        from PIL import Image, ImageDraw
        
        # Create blank canvas
        canvas = Image.new('RGB', canvas_size, color='white')
        draw = ImageDraw.Draw(canvas)
        
        # Draw bounding boxes
        for i, box in enumerate(bounding_boxes):
            x = box.get('x', 0)
            y = box.get('y', 0)
            w = box.get('width', 50)
            h = box.get('height', 50)
            
            # Convert to canvas coordinates (if needed)
            # Assuming coordinates are already in canvas space
            x1, y1 = int(x), int(y)
            x2, y2 = int(x + w), int(y + h)
            
            # Draw rectangle with different color per object
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
            color = colors[i % len(colors)]
            
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            # Add label
            label = box.get('name', f'obj{i}')
            draw.text((x1, y1 - 15), label, fill='black')
        
        # Save image
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path)
        logger.info(f"Reference geometry saved to {output_path}")
        
    except ImportError:
        raise ReferenceGeometryRenderError("PIL not available for rendering")
    except Exception as e:
        raise ReferenceGeometryRenderError(f"Rendering failed: {e}")

def run_reference_geometry_generation(
    constraints_dir: str, 
    output_dir: str, 
    canvas_size: Tuple[int, int] = (512, 512)
):
    """Generate reference geometry for all scenes."""
    constraints_path = Path(constraints_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for json_file in constraints_path.glob('*.json'):
        if 'contradiction' in json_file.name:
            continue  # Skip log files
        
        scene_id = json_file.stem
        constraints = load_physics_constraint(str(json_file))
        boxes = extract_bounding_boxes(constraints)
        
        if not boxes:
            logger.warning(f"No bounding boxes for {scene_id}")
            continue
        
        out_file = output_path / f"{scene_id}_reference.png"
        render_reference_geometry(boxes, str(out_file), canvas_size)
    
    logger.info(f"Reference geometry generation complete for {len(list(constraints_path.glob('*.json')))} scenes")

def main():
    """Entry point for reference geometry generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate reference geometry images")
    parser.add_argument('--constraints-dir', required=True, help='Directory with physics constraints JSON')
    parser.add_argument('--output-dir', required=True, help='Directory to save reference images')
    parser.add_argument('--width', type=int, default=512, help='Canvas width')
    parser.add_argument('--height', type=int, default=512, help='Canvas height')
    
    args = parser.parse_args()
    
    run_reference_geometry_generation(
        constraints_dir=args.constraints_dir,
        output_dir=args.output_dir,
        canvas_size=(args.width, args.height)
    )

if __name__ == '__main__':
    main()
