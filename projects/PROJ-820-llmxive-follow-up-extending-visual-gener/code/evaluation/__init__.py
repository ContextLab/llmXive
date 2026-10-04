"""
Evaluation module for llmXive research pipeline.

This module contains utilities for evaluating generated images against
physics constraints and performing statistical analysis.
"""

__version__ = "0.1.0"

# Public API exports
from .detector import (
    ObjectDetectionError,
    PhysicsViolationError,
    load_yolo_model,
    detect_objects,
    extract_bounding_boxes,
    calculate_iou,
    check_physics_violations,
    run_evaluation,
    main
)

__all__ = [
    'ObjectDetectionError',
    'PhysicsViolationError',
    'load_yolo_model',
    'detect_objects',
    'extract_bounding_boxes',
    'calculate_iou',
    'check_physics_violations',
    'run_evaluation',
    'main'
]
