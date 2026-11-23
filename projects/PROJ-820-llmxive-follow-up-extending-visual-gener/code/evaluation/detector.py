"""
Object detection and physics violation checker for llmXive pipeline.

This module implements YOLOv8n-based object detection to extract bounding boxes
from generated images and compare them against physics constraint ground truth.

Key functions:
- load_yolo_model: Load YOLOv8n model (CPU-only)
- detect_objects: Run inference on an image
- extract_bounding_boxes: Parse detection results
- calculate_iou: Compute Intersection over Union
- check_physics_violations: Compare detected boxes against physics constraints
- run_evaluation: Main evaluation pipeline for a scene
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import ultralytics - this is a required dependency
try:
    from ultralytics import YOLO
except ImportError:
    logger.error("ultralytics not installed. Please install with: pip install ultralytics")
    raise

# Constants
DEFAULT_IMAGE_SIZE = (512, 512)
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
DEFAULT_IOU_THRESHOLD = 0.5
DEFAULT_Y_OFFSET_THRESHOLD = 5  # pixels


class ObjectDetectionError(Exception):
    """Custom exception for object detection failures."""
    pass


class PhysicsViolationError(Exception):
    """Custom exception for physics violation detection issues."""
    pass


def load_yolo_model(model_path: str = "yolov8n.pt") -> YOLO:
    """
    Load YOLOv8n model for object detection.
    
    Args:
        model_path: Path to YOLO model weights (default: yolov8n.pt)
        
    Returns:
        Loaded YOLO model instance
        
    Raises:
        ObjectDetectionError: If model loading fails
    """
    try:
        logger.info(f"Loading YOLO model from: {model_path}")
        model = YOLO(model_path)
        # Ensure CPU-only usage
        model.to('cpu')
        logger.info("YOLO model loaded successfully on CPU")
        return model
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        raise ObjectDetectionError(f"Model loading failed: {e}")


def detect_objects(
    model: YOLO,
    image_path: str,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Run object detection on an image.
    
    Args:
        model: Loaded YOLO model
        image_path: Path to the image file
        confidence_threshold: Minimum confidence for detections
        
    Returns:
        List of detection dictionaries with keys:
            - class_id: int
            - class_name: str
            - confidence: float
            - bbox: [x1, y1, x2, y2]
            - center: (cx, cy)
            
    Raises:
        ObjectDetectionError: If detection fails
    """
    try:
        if not os.path.exists(image_path):
            raise ObjectDetectionError(f"Image not found: {image_path}")
        
        logger.info(f"Running detection on: {image_path}")
        results = model(image_path, conf=confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for i in range(len(boxes)):
                box = boxes[i]
                class_id = int(box.cls[0].item())
                class_name = model.names[class_id]
                confidence = float(box.conf[0].item())
                
                # Get bounding box: [x1, y1, x2, y2]
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = xyxy
                
                # Calculate center
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'center': (cx, cy),
                    'area': (x2 - x1) * (y2 - y1)
                })
        
        logger.info(f"Detected {len(detections)} objects")
        return detections
        
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise ObjectDetectionError(f"Object detection failed: {e}")


def calculate_iou(bbox1: List[float], bbox2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        bbox1: [x1, y1, x2, y2]
        bbox2: [x1, y1, x2, y2]
        
    Returns:
        IoU value between 0 and 1
    """
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def load_physics_constraints(scene_id: str, constraints_dir: str) -> Dict[str, Any]:
    """
    Load physics constraints for a scene.
    
    Args:
        scene_id: Scene identifier
        constraints_dir: Directory containing constraint JSON files
        
    Returns:
        Physics constraints dictionary
        
    Raises:
        PhysicsViolationError: If constraints file not found or invalid
    """
    constraints_path = Path(constraints_dir) / f"{scene_id}.json"
    
    if not constraints_path.exists():
        raise PhysicsViolationError(f"Constraints not found: {constraints_path}")
    
    try:
        with open(constraints_path, 'r') as f:
            constraints = json.load(f)
        return constraints
    except json.JSONDecodeError as e:
        raise PhysicsViolationError(f"Invalid JSON in constraints file: {e}")

def extract_bounding_boxes_from_constraints(
    constraints: Dict[str, Any],
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE
) -> List[Dict[str, Any]]:
    """
    Extract bounding boxes from physics constraints JSON.
    
    Args:
        constraints: Physics constraints dictionary
        image_size: (width, height) of target image
        
    Returns:
        List of bounding box dictionaries with normalized and pixel coordinates
    """
    boxes = []
    width, height = image_size
    
    # Handle different constraint formats
    if 'objects' in constraints:
        object_list = constraints['objects']
    elif 'bounding_boxes' in constraints:
        object_list = constraints['bounding_boxes']
    else:
        logger.warning("Unknown constraints format, attempting to parse directly")
        object_list = [constraints]
    
    for obj in object_list:
        # Extract coordinates (may be normalized 0-1 or pixel values)
        x1 = obj.get('x1', obj.get('x', 0))
        y1 = obj.get('y1', obj.get('y', 0))
        x2 = obj.get('x2', obj.get('w', 0)) + x1 if 'w' in obj else obj.get('x2', x1)
        y2 = obj.get('y2', obj.get('h', 0)) + y1 if 'h' in obj else obj.get('y2', y1)
        
        # Normalize if values are between 0 and 1
        if x1 <= 1.0 and y1 <= 1.0:
            x1 = x1 * width
            y1 = y1 * height
            x2 = x2 * width
            y2 = y2 * height
        
        boxes.append({
            'class_name': obj.get('class', obj.get('object', 'unknown')),
            'bbox': [x1, y1, x2, y2],
            'center': ((x1 + x2) / 2, (y1 + y2) / 2),
            'relationships': obj.get('relationships', [])
        })
    
    return boxes


def check_physics_violations(
    detected_boxes: List[Dict[str, Any]],
    constraint_boxes: List[Dict[str, Any]],
    iou_threshold: float = DEFAULT_IOU_THRESHOLD,
    y_offset_threshold: float = DEFAULT_Y_OFFSET_THRESHOLD
) -> Dict[str, Any]:
    """
    Compare detected bounding boxes against physics constraints.
    
    Args:
        detected_boxes: Boxes from YOLO detection
        constraint_boxes: Boxes from physics constraints
        iou_threshold: Minimum IoU for matching boxes
        y_offset_threshold: Maximum Y-offset for "above" relationships
        
    Returns:
        Dictionary with violation analysis results
    """
    violations = {
        'floating_objects': [],
        'interpenetrations': [],
        'relationship_violations': [],
        'missing_objects': [],
        'extra_objects': [],
        'confidence_issues': [],
        'summary': {}
    }
    
    matched_constraint_indices = set()
    matched_detection_indices = set()
    
    # Check for floating objects (low confidence or no support)
    for i, det in enumerate(detected_boxes):
        if det['confidence'] < DEFAULT_CONFIDENCE_THRESHOLD:
            violations['confidence_issues'].append({
                'object': det['class_name'],
                'confidence': det['confidence'],
                'bbox': det['bbox']
            })
        
        # Check if this object has support (simplified: check if any object below it)
        has_support = False
        for j, other_det in enumerate(detected_boxes):
            if i == j:
                continue
            # Check if other object is below and overlapping
            if other_det['center'][1] > det['center'][1] + 10:  # Below by at least 10px
                iou = calculate_iou(det['bbox'], other_det['bbox'])
                if iou > 0.1:  # Some overlap
                    has_support = True
                    break
        
        if not has_support and det['confidence'] >= DEFAULT_CONFIDENCE_THRESHOLD:
            # Check if it's supposed to be supported by constraint
            for k, const_box in enumerate(constraint_boxes):
                iou = calculate_iou(det['bbox'], const_box['bbox'])
                if iou > iou_threshold:
                    # This object matches a constraint - check if it should have support
                    relationships = const_box.get('relationships', [])
                    for rel in relationships:
                        if rel.get('type') in ['on', 'above', 'supported_by']:
                            violations['floating_objects'].append({
                                'object': det['class_name'],
                                'bbox': det['bbox'],
                                'expected_support': rel.get('supporter', 'unknown')
                            })
                            break
                    break
    
    # Check for relationship violations
    for const_box in constraint_boxes:
        relationships = const_box.get('relationships', [])
        for rel in relationships:
            rel_type = rel.get('type')
            supporter = rel.get('supporter')
            supported = rel.get('supported')
            
            if rel_type in ['on', 'above', 'supported_by']:
                # Find corresponding detected boxes
                supporter_box = None
                supported_box = None
                
                for det in detected_boxes:
                    if supporter and supporter.lower() in det['class_name'].lower():
                        supporter_box = det
                    if supported and supported.lower() in det['class_name'].lower():
                        supported_box = det
                
                if supporter_box and supported_box:
                    # Check Y relationship
                    if supporter_box['center'][1] < supported_box['center'][1] - y_offset_threshold:
                        # Supporter is above (lower y) - violation for "on" relationship
                        if rel_type in ['on', 'supported_by']:
                            violations['relationship_violations'].append({
                                'type': rel_type,
                                'supporter': supporter,
                                'supported': supported,
                                'expected': f"{supporter} should be below {supported}",
                                'actual': f"{supporter} Y={supporter_box['center'][1]:.1f}, {supported} Y={supported_box['center'][1]:.1f}"
                            })
    
    # Check for missing/extra objects
    detected_classes = {det['class_name'] for det in detected_boxes}
    constraint_classes = {const['class_name'] for const in constraint_boxes}
    
    violations['missing_objects'] = list(constraint_classes - detected_classes)
    violations['extra_objects'] = list(detected_classes - constraint_classes)
    
    # Summary
    total_violations = (
        len(violations['floating_objects']) +
        len(violations['relationship_violations']) +
        len(violations['confidence_issues'])
    )
    
    violations['summary'] = {
        'total_detected': len(detected_boxes),
        'total_constraints': len(constraint_boxes),
        'floating_objects': len(violations['floating_objects']),
        'relationship_violations': len(violations['relationship_violations']),
        'confidence_issues': len(violations['confidence_issues']),
        'missing_objects': len(violations['missing_objects']),
        'extra_objects': len(violations['extra_objects']),
        'total_violations': total_violations,
        'violation_rate': total_violations / max(len(constraint_boxes), 1)
    }
    
    return violations


def run_evaluation(
    scene_id: str,
    image_path: str,
    constraints_dir: str,
    output_dir: str,
    model: Optional[YOLO] = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> Dict[str, Any]:
    """
    Run full evaluation pipeline for a scene.
    
    Args:
        scene_id: Scene identifier
        image_path: Path to generated image
        constraints_dir: Directory with physics constraint JSON files
        output_dir: Directory to save evaluation results
        model: Pre-loaded YOLO model (optional)
        confidence_threshold: Detection confidence threshold
        
    Returns:
        Evaluation results dictionary
    """
    try:
        # Load model if not provided
        if model is None:
            model = load_yolo_model()
        
        # Load constraints
        constraints = load_physics_constraints(scene_id, constraints_dir)
        constraint_boxes = extract_bounding_boxes_from_constraints(constraints)
        
        # Run detection
        detected_boxes = detect_objects(model, image_path, confidence_threshold)
        
        # Check violations
        violations = check_physics_violations(detected_boxes, constraint_boxes)
        
        # Compile results
        results = {
            'scene_id': scene_id,
            'image_path': image_path,
            'detection_results': {
                'objects_detected': len(detected_boxes),
                'detections': detected_boxes
            },
            'constraint_results': {
                'constraints_loaded': len(constraint_boxes),
                'constraints': constraint_boxes
            },
            'violation_analysis': violations,
            'summary': violations['summary']
        }
        
        # Save results
        output_path = Path(output_dir) / f"{scene_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Evaluation results saved to: {output_path}")
        return results
        
    except Exception as e:
        logger.error(f"Evaluation failed for scene {scene_id}: {e}")
        raise


def main():
    """Main entry point for running evaluation from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run object detection and physics violation evaluation')
    parser.add_argument('--scene-id', required=True, help='Scene ID to evaluate')
    parser.add_argument('--image', required=True, help='Path to generated image')
    parser.add_argument('--constraints-dir', default='data/derived/physics_constraints',
                      help='Directory with physics constraint JSON files')
    parser.add_argument('--output-dir', default='data/derived/evaluation_results',
                      help='Directory to save evaluation results')
    parser.add_argument('--confidence-threshold', type=float, default=DEFAULT_CONFIDENCE_THRESHOLD,
                      help='Detection confidence threshold')
    
    args = parser.parse_args()
    
    try:
        results = run_evaluation(
            scene_id=args.scene_id,
            image_path=args.image,
            constraints_dir=args.constraints_dir,
            output_dir=args.output_dir,
            confidence_threshold=args.confidence_threshold
        )
        print(json.dumps(results['summary'], indent=2))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()