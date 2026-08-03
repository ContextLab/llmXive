"""
code/data/generator.py

Implements the "Synthetic SpatialClaw Proxy" with procedural generation logic.
Preserves 3D invariants (occlusion, depth variance) without using blocked 3D libraries.

Generates a JSON dataset at `data/raw/synthetic_spatialclaw_v1.json` containing:
- task_id
- ground_truth_3d_params (dict)
- task_type (occlusion/depth/relative)
- scene_id
"""
import json
import os
import random
import uuid
import logging
from dataclasses import asdict, dataclass, field
from typing import List, Dict, Any, Optional

# Ensure output directory exists
OUTPUT_PATH = "data/raw/synthetic_spatialclaw_v1.json"
DEFAULT_N_TASKS = 100
SEED = 42

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
    center: Point3D
    dimensions: Dict[str, float]  # width, height, depth
    rotation: Dict[str, float]     # roll, pitch, yaw
    is_visible: bool = True

@dataclass
class GroundTruth3DParams:
    occlusion_ratio: float
    depth_variance: float
    relative_position: Dict[str, float]  # dx, dy, dz between objects
    scene_complexity: float

@dataclass
class TaskInstance:
    task_id: str
    scene_id: str
    task_type: str  # 'occlusion', 'depth', 'relative'
    object_a_id: str
    object_b_id: str
    ground_truth_3d_params: Dict[str, Any]
    query_params: Dict[str, Any]

def generate_scene_id() -> str:
    return str(uuid.uuid4())[:8]

def generate_object_id() -> str:
    return str(uuid.uuid4())[:8]

def random_float(min_val: float, max_val: float) -> float:
    return random.uniform(min_val, max_val)

def generate_point3d(x_range: tuple = (-10, 10), y_range: tuple = (-10, 10), z_range: tuple = (0, 10)) -> Point3D:
    return Point3D(
        x=random_float(*x_range),
        y=random_float(*y_range),
        z=random_float(*z_range)
    )

def generate_object(scene_id: str, x_range: tuple = (-5, 5), y_range: tuple = (-5, 5), z_range: tuple = (0, 5)) -> Object3D:
    center = generate_point3d(x_range, y_range, z_range)
    return Object3D(
        obj_id=generate_object_id(),
        center=center,
        dimensions={
            "width": random_float(0.1, 1.0),
            "height": random_float(0.1, 1.0),
            "depth": random_float(0.1, 1.0)
        },
        rotation={
            "roll": random_float(0, 2 * 3.14159),
            "pitch": random_float(0, 2 * 3.14159),
            "yaw": random_float(0, 2 * 3.14159)
        },
        is_visible=True
    )

def calculate_depth_diff(obj_a: Object3D, obj_b: Object3D) -> float:
    """Calculate Euclidean depth difference (Z-axis primarily) between two objects."""
    return abs(obj_a.center.z - obj_b.center.z)

def calculate_occlusion_ratio(obj_a: Object3D, obj_b: Object3D) -> float:
    """
    Simulate a simple occlusion ratio based on spatial overlap in X-Y plane
    and relative depth. This is a proxy for 3D occlusion without using 3D libraries.
    Returns a value between 0.0 (no occlusion) and 1.0 (full occlusion).
    """
    # Simple 2D projection overlap check
    overlap_x = max(0, min(obj_a.center.x + obj_a.dimensions["width"]/2, obj_b.center.x + obj_b.dimensions["width"]/2) -
                        max(obj_a.center.x - obj_a.dimensions["width"]/2, obj_b.center.x - obj_b.dimensions["width"]/2))
    overlap_y = max(0, min(obj_a.center.y + obj_a.dimensions["height"]/2, obj_b.center.y + obj_b.dimensions["height"]/2) -
                        max(obj_a.center.y - obj_a.dimensions["height"]/2, obj_b.center.y - obj_b.dimensions["height"]/2))
    
    area_overlap = overlap_x * overlap_y
    area_a = obj_a.dimensions["width"] * obj_a.dimensions["height"]
    area_b = obj_b.dimensions["width"] * obj_b.dimensions["height"]
    
    if area_a == 0 or area_b == 0:
        return 0.0
    
    # Normalize by the smaller object's area to get a ratio
    min_area = min(area_a, area_b)
    ratio = area_overlap / min_area if min_area > 0 else 0.0
    
    # Modulate by depth difference: if one is far behind the other, occlusion is less likely
    depth_diff = abs(obj_a.center.z - obj_b.center.z)
    depth_factor = max(0, 1.0 - (depth_diff / 5.0)) # Assume 5m is max effective occlusion range
    
    return min(1.0, ratio * depth_factor)

def generate_occlusion_task(scene_id: str) -> TaskInstance:
    obj_a = generate_object(scene_id)
    obj_b = generate_object(scene_id)
    
    # Force some overlap for interesting occlusion
    while calculate_occlusion_ratio(obj_a, obj_b) < 0.1:
        obj_b = generate_object(scene_id)
    
    occlusion_ratio = calculate_occlusion_ratio(obj_a, obj_b)
    
    return TaskInstance(
        task_id=str(uuid.uuid4()),
        scene_id=scene_id,
        task_type="occlusion",
        object_a_id=obj_a.obj_id,
        object_b_id=obj_b.obj_id,
        ground_truth_3d_params={
            "occlusion_ratio": occlusion_ratio,
            "depth_variance": calculate_depth_diff(obj_a, obj_b),
            "relative_position": {
                "dx": obj_b.center.x - obj_a.center.x,
                "dy": obj_b.center.y - obj_a.center.y,
                "dz": obj_b.center.z - obj_a.center.z
            },
            "scene_complexity": random_float(0.1, 1.0)
        },
        query_params={
            "query": f"Is object {obj_b.obj_id} occluded by object {obj_a.obj_id}?",
            "threshold": 0.5
        }
    )

def generate_depth_task(scene_id: str) -> TaskInstance:
    obj_a = generate_object(scene_id)
    obj_b = generate_object(scene_id)
    
    # Ensure significant depth difference
    while abs(obj_a.center.z - obj_b.center.z) < 0.5:
        obj_b = generate_object(scene_id)
        
    depth_diff = calculate_depth_diff(obj_a, obj_b)
    
    return TaskInstance(
        task_id=str(uuid.uuid4()),
        scene_id=scene_id,
        task_type="depth",
        object_a_id=obj_a.obj_id,
        object_b_id=obj_b.obj_id,
        ground_truth_3d_params={
            "occlusion_ratio": calculate_occlusion_ratio(obj_a, obj_b),
            "depth_variance": depth_diff,
            "relative_position": {
                "dx": obj_b.center.x - obj_a.center.x,
                "dy": obj_b.center.y - obj_a.center.y,
                "dz": obj_b.center.z - obj_a.center.z
            },
            "scene_complexity": random_float(0.1, 1.0)
        },
        query_params={
            "query": f"Which object is closer to the camera? ({obj_a.obj_id} vs {obj_b.obj_id})",
            "expected_z_diff": depth_diff
        }
    )

def generate_relative_task(scene_id: str) -> TaskInstance:
    obj_a = generate_object(scene_id)
    obj_b = generate_object(scene_id)
    
    return TaskInstance(
        task_id=str(uuid.uuid4()),
        scene_id=scene_id,
        task_type="relative",
        object_a_id=obj_a.obj_id,
        object_b_id=obj_b.obj_id,
        ground_truth_3d_params={
            "occlusion_ratio": calculate_occlusion_ratio(obj_a, obj_b),
            "depth_variance": calculate_depth_diff(obj_a, obj_b),
            "relative_position": {
                "dx": obj_b.center.x - obj_a.center.x,
                "dy": obj_b.center.y - obj_a.center.y,
                "dz": obj_b.center.z - obj_a.center.z
            },
            "scene_complexity": random_float(0.1, 1.0)
        },
        query_params={
            "query": f"What is the relative position of {obj_b.obj_id} with respect to {obj_a.obj_id}?",
            "expected_dx": obj_b.center.x - obj_a.center.x,
            "expected_dy": obj_b.center.y - obj_a.center.y,
            "expected_dz": obj_b.center.z - obj_a.center.z
        }
    )

def generate_dataset(n_tasks: int = DEFAULT_N_TASKS, seed: int = SEED, output_path: str = OUTPUT_PATH) -> List[TaskInstance]:
    """
    Generate a synthetic dataset of spatial reasoning tasks.
    
    Args:
        n_tasks: Number of task instances to generate.
        seed: Random seed for reproducibility.
        output_path: Path to save the JSON output file.
        
    Returns:
        List of generated TaskInstance objects.
    """
    random.seed(seed)
    logger.info(f"Generating {n_tasks} synthetic spatial tasks with seed {seed}...")
    
    tasks = []
    scene_count = 0
    tasks_per_scene = 5
    
    for i in range(n_tasks):
        if i % tasks_per_scene == 0:
            scene_id = generate_scene_id()
            scene_count += 1
        
        task_type_choice = random.choice(["occlusion", "depth", "relative"])
        
        if task_type_choice == "occlusion":
            task = generate_occlusion_task(scene_id)
        elif task_type_choice == "depth":
            task = generate_depth_task(scene_id)
        else:
            task = generate_relative_task(scene_id)
        
        tasks.append(task)
        logger.debug(f"Generated task {task.task_id} (type: {task.task_type})")
    
    # Prepare data for JSON serialization
    serializable_tasks = []
    for task in tasks:
        task_dict = asdict(task)
        # Ensure all nested objects are converted to dicts if necessary
        # Point3D and Object3D are already handled by asdict recursively if they are dataclasses
        # But we need to ensure GroundTruth3DParams is a dict
        if isinstance(task_dict['ground_truth_3d_params'], GroundTruth3DParams):
            task_dict['ground_truth_3d_params'] = asdict(task_dict['ground_truth_3d_params'])
        
        serializable_tasks.append(task_dict)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_tasks, f, indent=2)
    
    logger.info(f"Successfully generated {len(tasks)} tasks and saved to {output_path}")
    return tasks

def main():
    """Entry point for generating the dataset."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Synthetic SpatialClaw Proxy Dataset")
    parser.add_argument("--n", type=int, default=DEFAULT_N_TASKS, help="Number of tasks to generate")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH, help="Output file path")
    
    args = parser.parse_args()
    
    generate_dataset(n_tasks=args.n, seed=args.seed, output_path=args.output)

if __name__ == "__main__":
    main()
