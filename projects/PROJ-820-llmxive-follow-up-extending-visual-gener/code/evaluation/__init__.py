"""
Evaluation module for llmXive.
Contains object detection and metric calculation logic.
"""

from .detector import (
    ObjectDetectionError,
    PhysicsViolationError,
    load_yolo_model,
    detect_objects,
    calculate_iou,
    load_physics_constraints,
    extract_bounding_boxes_from_constraints,
    check_physics_violations,
    run_evaluation,
    main
)

__all__ = [
    'ObjectDetectionError',
    'PhysicsViolationError',
    'load_yolo_model',
    'detect_objects',
    'calculate_iou',
    'load_physics_constraints',
    'extract_bounding_boxes_from_constraints',
    'check_physics_violations',
    'run_evaluation',
    'main'
]
