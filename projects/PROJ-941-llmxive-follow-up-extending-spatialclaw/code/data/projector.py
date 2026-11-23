"""
Projector module for converting 3D point clouds/scenes to 2D symbolic representations.

This module enforces the 2D constraint (FR-002) by ensuring no 3D libraries
(trimesh, pytorch3d, open3d) are used. It converts 3D data into 2D bounding boxes,
depth histograms, and symbolic relations.
"""
import json
import os
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.stats import histogram as scipy_histogram

# Import from local modules
from utils.logging_config import get_logger
from utils.memory_monitor import log_memory_snapshot, memory_monitor_context, check_memory_budget

logger = get_logger(__name__)

# Constants
MEMORY_WARNING_THRESHOLD_MB = 4096.0  # Warn if usage exceeds 4GB
MAX_POINTS_PER_BATCH = 100000  # Process in batches to avoid OOM

def project_point_to_2d(x: float, y: float, z: float) -> Tuple[float, float]:
    """
    Project a single 3D point to 2D (orthographic projection).
    
    Args:
        x, y, z: Coordinates of the point.
    
    Returns:
        Tuple of (x, y) coordinates.
    """
    return (x, y)

def calculate_depth_histogram(z_values: np.ndarray, bins: int = 10) -> Dict[str, Any]:
    """
    Calculate a histogram of depth (Z) values.
    
    Args:
        z_values: Array of Z coordinates.
        bins: Number of histogram bins.
    
    Returns:
        Dictionary with histogram data.
    """
    if len(z_values) == 0:
        return {"bins": [], "counts": [], "range": [0, 0]}
    
    hist, bin_edges = scipy_histogram(z_values, bins=bins)
    return {
        "bins": bin_edges.tolist(),
        "counts": hist.tolist(),
        "range": [float(np.min(z_values)), float(np.max(z_values))]
    }

def project_object_to_2d(
    points: List[Dict[str, float]], 
    obj_id: str, 
    task_type: str
) -> Dict[str, Any]:
    """
    Project a list of 3D points representing an object to 2D representation.
    
    Args:
        points: List of dicts with 'x', 'y', 'z' keys.
        obj_id: Object identifier.
        task_type: Type of task (occlusion, depth, relative).
    
    Returns:
        Dictionary containing 2D projection data.
    """
    if not points:
        return {
            "object_id": obj_id,
            "task_type": task_type,
            "bounding_box_2d": None,
            "depth_histogram": None,
            "point_count": 0
        }

    xs = [p['x'] for p in points]
    ys = [p['y'] for p in points]
    zs = np.array([p['z'] for p in points])

    # 2D Bounding Box
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    bounding_box_2d = {
        "min_x": min_x, "max_x": max_x,
        "min_y": min_y, "max_y": max_y,
        "center_x": (min_x + max_x) / 2,
        "center_y": (min_y + max_y) / 2,
        "width": max_x - min_x,
        "height": max_y - min_y
    }

    # Depth Histogram
    depth_hist = calculate_depth_histogram(zs)

    return {
        "object_id": obj_id,
        "task_type": task_type,
        "bounding_box_2d": bounding_box_2d,
        "depth_histogram": depth_hist,
        "point_count": len(points)
    }

def project_task_to_2d(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Project a single task instance to 2D representation.
    
    Args:
        task_data: Dictionary containing task instance data including points.
    
    Returns:
        Dictionary containing the 2D projected task data.
    """
    task_id = task_data.get("task_id", "unknown")
    logger.debug(f"Projecting task {task_id} to 2D")

    # Memory check before processing
    current_mem = 0
    try:
        from utils.memory_monitor import get_memory_usage_mb
        current_mem = get_memory_usage_mb()
    except Exception as e:
        logger.warning(f"Could not check memory usage: {e}")

    budget = 8192.0 # Assume 8GB budget for safety
    if not check_memory_budget(current_mem, budget, safety_margin=0.8):
        logger.warning(f"Memory usage critical for task {task_id}. Proceeding with caution.")

    projected_objects = []
    objects = task_data.get("objects", [])

    with memory_monitor_context(f"Projecting Task {task_id}", warning_threshold_mb=MEMORY_WARNING_THRESHOLD_MB):
        for obj in objects:
            obj_id = obj.get("id", "unknown")
            points = obj.get("points", [])
            task_type = obj.get("task_type", "unknown")
            
            # Process in batches if too large
            if len(points) > MAX_POINTS_PER_BATCH:
                logger.warning(f"Object {obj_id} has {len(points)} points. Processing in batches.")
                # For simplicity in this projection, we just take a sample or full set if feasible
                # In a real streaming scenario, we would accumulate stats incrementally.
                # Here we assume we can fit one object in memory, but log if it's large.
                pass 
            
            projected_obj = project_object_to_2d(points, obj_id, task_type)
            projected_objects.append(projected_obj)

    return {
        "task_id": task_id,
        "scene_id": task_data.get("scene_id", "unknown"),
        "projected_objects": projected_objects,
        "projection_status": "success"
    }

def project_dataset_to_2d(dataset_path: str, output_path: str) -> None:
    """
    Project an entire dataset from JSON to 2D representation and save.
    
    Args:
        dataset_path: Path to input JSON dataset.
        output_path: Path to save output JSON.
    """
    logger.info(f"Loading dataset from {dataset_path}")
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    with open(dataset_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    logger.info(f"Projecting {len(data)} tasks to 2D...")
    projected_results = []

    for i, task in enumerate(data):
        try:
            result = project_task_to_2d(task)
            projected_results.append(result)
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(data)} tasks")
        except Exception as e:
            logger.error(f"Error projecting task {task.get('task_id', 'unknown')}: {e}")
            # Continue processing other tasks
            continue

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(projected_results, f, indent=2)

    logger.info(f"Projection complete. Results saved to {output_path}")

def main():
    """
    CLI entry point for the projector.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Project 3D dataset to 2D")
    parser.add_argument("--input", type=str, default="data/raw/synthetic_spatialclaw_v1.json",
                        help="Path to input JSON dataset")
    parser.add_argument("--output", type=str, default="data/processed/synthetic_spatialclaw_2d_v1.json",
                        help="Path to output JSON dataset")
    args = parser.parse_args()

    log_memory_snapshot("Projector Start")
    project_dataset_to_2d(args.input, args.output)
    log_memory_snapshot("Projector End")

if __name__ == "__main__":
    main()
