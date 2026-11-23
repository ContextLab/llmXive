"""
code/data/generator.py

Generates the Synthetic SpatialClaw Proxy dataset.
This module implements the logic for creating 3D primitives (cubes/spheres),
positioning them, and defining tasks (occlusion, depth, relative) based on
geometric constraints.

It satisfies T006a (Pilot) and T006b (Full Generation) requirements.
"""

import json
import os
import random
import uuid
import logging
import math
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple

# Configure logging for the generator
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Point3D:
    x: float
    y: float
    z: float

@dataclass
class Object3D:
    obj_id: str
    obj_type: str  # 'cube' or 'sphere'
    center: Point3D
    dimension: float  # side length for cube, diameter for sphere
    color: str = "white"

@dataclass
class GroundTruth3DParams:
    task_id: str
    seed: int
    objects: List[Dict[str, Any]]
    task_type: str
    # Derived ground truth for evaluation
    gt_3d_is_occluded: bool
    depth_variance: float
    # For relative tasks
    relative_order: Optional[List[str]] = None

@dataclass
class TaskInstance:
    task_id: str
    seed: int
    task_type: str
    ground_truth_3d_params: Dict[str, Any]
    # Metadata for reproducibility
    generation_timestamp: str = ""

def generate_scene_id() -> str:
    return str(uuid.uuid4())

def generate_object_id() -> str:
    return str(uuid.uuid4())

def random_float(min_val: float, max_val: float) -> float:
    return random.uniform(min_val, max_val)

def generate_point3d(min_coord: float = -10.0, max_coord: float = 10.0) -> Point3D:
    return Point3D(
        x=random_float(min_coord, max_coord),
        y=random_float(min_coord, max_coord),
        z=random_float(0.0, max_coord) # Z is depth/height, usually positive
    )

def generate_object(obj_type: str, seed: Optional[int] = None) -> Object3D:
    if seed is not None:
        # We don't re-seed here, we rely on the global seed set in main
        pass
    
    center = generate_point3d(min_coord=-5.0, max_coord=5.0)
    # Dimension between 1.0m and 5.0m
    dimension = random_float(1.0, 5.0)
    
    return Object3D(
        obj_id=generate_object_id(),
        obj_type=obj_type,
        center=center,
        dimension=dimension
    )

def calculate_2d_overlap_ratio(obj1: Object3D, obj2: Object3D) -> float:
    """
    Calculates the overlap ratio of 2D bounding boxes projected onto the XY plane.
    This simulates the "information loss" where 3D separation might look like 2D overlap.
    """
    # Project to 2D (ignore Z)
    # For a cube: bounding box is [x - dim/2, x + dim/2]
    # For a sphere: bounding box is [x - r, x + r]
    
    def get_2d_bounds(obj: Object3D) -> Tuple[float, float, float, float]:
        r = obj.dimension / 2.0
        x_min = obj.center.x - r
        x_max = obj.center.x + r
        y_min = obj.center.y - r
        y_max = obj.center.y + r
        return x_min, x_max, y_min, y_max

    b1 = get_2d_bounds(obj1)
    b2 = get_2d_bounds(obj2)

    # Intersection
    x_min_i = max(b1[0], b2[0])
    x_max_i = min(b1[1], b2[1])
    y_min_i = max(b1[2], b2[2])
    y_max_i = min(b1[3], b2[3])

    if x_min_i >= x_max_i or y_min_i >= y_max_i:
        return 0.0

    area_i = (x_max_i - x_min_i) * (y_max_i - y_min_i)
    area_1 = (b1[1] - b1[0]) * (b1[3] - b1[2])
    area_2 = (b2[1] - b2[0]) * (b2[3] - b2[2])
    area_union = area_1 + area_2 - area_i

    if area_union == 0:
        return 0.0
    return area_i / area_union

def calculate_depth_diff(obj1: Object3D, obj2: Object3D) -> float:
    """Calculates the absolute difference in Z (depth) between two objects."""
    return abs(obj1.center.z - obj2.center.z)

def calculate_3d_depth_variance(objects: List[Object3D]) -> float:
    """Calculates the variance of Z coordinates for a list of objects."""
    if len(objects) < 2:
        return 0.0
    zs = [obj.center.z for obj in objects]
    mean_z = sum(zs) / len(zs)
    variance = sum((z - mean_z) ** 2 for z in zs) / len(zs)
    return math.sqrt(variance) # Return std dev as a proxy for variance magnitude

def calculate_occlusion_in_3d(obj_front: Object3D, obj_back: Object3D) -> bool:
    """
    Determines if obj_front actually occludes obj_back in 3D.
    Simple check: same XY bounds AND obj_front.z < obj_back.z (assuming camera at z=-inf looking +z)
    Or if camera is at +inf looking -z (standard depth map), front has higher Z.
    Let's assume standard: Camera at Z = +infinity looking towards -Z.
    Closer objects have higher Z.
    """
    # Check 2D overlap first
    if calculate_2d_overlap_ratio(obj_front, obj_back) == 0:
        return False
    
    # Check depth order
    # If obj_front is "in front" (closer to camera), it has higher Z
    return obj_front.center.z > obj_back.center.z

def generate_occlusion_task(seed: int) -> TaskInstance:
    """
    Generates an occlusion task.
    Invariant: Ensure projected 2D bounding boxes overlap.
    Invariant: Ensure 3D occlusion actually happens (or intentionally doesn't for negative examples).
    """
    random.seed(seed)
    
    # Generate two objects
    # We need them to overlap in 2D
    # Strategy: Generate obj1, then place obj2 such that its center is close to obj1's center
    obj1 = generate_object(random.choice(['cube', 'sphere']))
    
    # Place obj2 very close in XY
    offset_x = random_float(-obj1.dimension/2, obj1.dimension/2)
    offset_y = random_float(-obj1.dimension/2, obj1.dimension/2)
    
    obj2_center = Point3D(
        x=obj1.center.x + offset_x,
        y=obj1.center.y + offset_y,
        z=random_float(0.0, 10.0)
    )
    
    obj2 = Object3D(
        obj_id=generate_object_id(),
        obj_type=random.choice(['cube', 'sphere']),
        center=obj2_center,
        dimension=random_float(1.0, 5.0)
    )
    
    # Ensure 2D overlap is significant (> 0.1)
    overlap = calculate_2d_overlap_ratio(obj1, obj2)
    attempts = 0
    while overlap < 0.1 and attempts < 100:
        obj2 = generate_object(random.choice(['cube', 'sphere']))
        # Force XY proximity
        obj2.center.x = obj1.center.x + random_float(-1.0, 1.0)
        obj2.center.y = obj1.center.y + random_float(-1.0, 1.0)
        overlap = calculate_2d_overlap_ratio(obj1, obj2)
        attempts += 1
    
    if attempts == 100:
        logger.warning("Failed to generate sufficient 2D overlap for occlusion task.")

    # Determine occlusion status
    # We want a mix: sometimes true occlusion, sometimes false (2D overlap but 3D separation)
    # Let's force a specific scenario for the "task"
    # Task: "Is object A occluded by object B?"
    # We'll just store the scene and the ground truth of the relationship.
    
    objects = [obj1, obj2]
    
    # Ground truth: Is there ANY occlusion in this pair?
    # Check both directions
    occluded_1_by_2 = calculate_occlusion_in_3d(obj2, obj1) # obj2 in front of obj1
    occluded_2_by_1 = calculate_occlusion_in_3d(obj1, obj2) # obj1 in front of obj2
    
    is_occluded = occluded_1_by_2 or occluded_2_by_1
    
    depth_var = calculate_3d_depth_variance(objects)
    
    params = GroundTruth3DParams(
        task_id=generate_scene_id(),
        seed=seed,
        objects=[asdict(o) for o in objects],
        task_type="occlusion",
        gt_3d_is_occluded=is_occluded,
        depth_variance=depth_var
    )
    
    return TaskInstance(
        task_id=params.task_id,
        seed=seed,
        task_type="occlusion",
        ground_truth_3d_params=asdict(params),
        generation_timestamp=""
    )

def generate_depth_task(seed: int) -> TaskInstance:
    """
    Generates a depth task.
    Invariant: Ensure depth variance > 0.5m.
    """
    random.seed(seed)
    
    obj1 = generate_object(random.choice(['cube', 'sphere']))
    obj2 = generate_object(random.choice(['cube', 'sphere']))
    
    # Force depth separation
    # Place obj2 significantly deeper or shallower
    separation = random_float(0.6, 5.0)
    if random.random() > 0.5:
        obj2.center.z = obj1.center.z + separation
    else:
        obj2.center.z = obj1.center.z - separation
        
    # Ensure Z stays positive
    if obj2.center.z < 0.1:
        obj2.center.z = obj1.center.z + separation

    objects = [obj1, obj2]
    depth_var = calculate_3d_depth_variance(objects)
    
    # Ensure variance constraint
    if depth_var < 0.5:
        # Force it
        obj2.center.z = obj1.center.z + 1.0
        depth_var = calculate_3d_depth_variance(objects)

    is_occluded = calculate_occlusion_in_3d(obj1, obj2) or calculate_occlusion_in_3d(obj2, obj1)

    params = GroundTruth3DParams(
        task_id=generate_scene_id(),
        seed=seed,
        objects=[asdict(o) for o in objects],
        task_type="depth",
        gt_3d_is_occluded=is_occluded,
        depth_variance=depth_var
    )

    return TaskInstance(
        task_id=params.task_id,
        seed=seed,
        task_type="depth",
        ground_truth_3d_params=asdict(params),
        generation_timestamp=""
    )

def generate_relative_task(seed: int) -> TaskInstance:
    """
    Generates a relative position task.
    """
    random.seed(seed)
    
    # Generate 3 objects for relative ordering
    obj1 = generate_object(random.choice(['cube', 'sphere']))
    obj2 = generate_object(random.choice(['cube', 'sphere']))
    obj3 = generate_object(random.choice(['cube', 'sphere']))
    
    # Randomize positions
    objects = [obj1, obj2, obj3]
    
    # Sort by Z to get ground truth order
    sorted_objects = sorted(objects, key=lambda o: o.center.z)
    relative_order = [o.obj_id for o in sorted_objects]
    
    depth_var = calculate_3d_depth_variance(objects)
    is_occluded = False # Relative tasks don't primarily care about occlusion, but we track it
    
    params = GroundTruth3DParams(
        task_id=generate_scene_id(),
        seed=seed,
        objects=[asdict(o) for o in objects],
        task_type="relative",
        gt_3d_is_occluded=is_occluded,
        depth_variance=depth_var,
        relative_order=relative_order
    )

    return TaskInstance(
        task_id=params.task_id,
        seed=seed,
        task_type="relative",
        ground_truth_3d_params=asdict(params),
        generation_timestamp=""
    )

def generate_dataset(n: int, output_path: str, task_types: List[str] = None) -> None:
    """
    Generates N task instances and saves to JSON.
    """
    if task_types is None:
        task_types = ['occlusion', 'depth', 'relative']
    
    logger.info(f"Generating dataset of size {n} to {output_path}")
    
    tasks = []
    for i in range(n):
        seed = i + 1000 # Ensure unique seeds
        task_type = task_types[i % len(task_types)]
        
        if task_type == 'occlusion':
            task = generate_occlusion_task(seed)
        elif task_type == 'depth':
            task = generate_depth_task(seed)
        else:
            task = generate_relative_task(seed)
        
        tasks.append(asdict(task))
        
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i+1}/{n} tasks")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(tasks, f, indent=2)
    
    logger.info(f"Dataset generation complete. Saved to {output_path}")

def main():
    """
    Entry point for T006b: Full Data Generation.
    Reads N from data/power_config.yaml (calculated by T035b) or uses a default if not found,
    but primarily expects the N to be passed or derived from the power analysis.
    For this specific task implementation, we will read the required N from the power analysis output.
    """
    import yaml
    
    # Configuration paths
    power_config_path = "data/power_config.yaml"
    power_result_path = "results/analysis/power_analysis_summary.json"
    output_path = "data/raw/synthetic_spatialclaw_v1.json"
    
    # Determine N
    n = 100 # Default fallback if power analysis not present (should not happen in correct flow)
    
    if os.path.exists(power_result_path):
        try:
            with open(power_result_path, 'r') as f:
                power_data = json.load(f)
                n = power_data.get('n_required', 100)
                logger.info(f"Read required sample size N={n} from power analysis.")
        except Exception as e:
            logger.warning(f"Could not read power analysis result: {e}. Using default N=100.")
    else:
        logger.warning(f"Power analysis result not found at {power_result_path}. Using default N=100.")
    
    # Generate the dataset
    generate_dataset(n, output_path)

if __name__ == "__main__":
    main()