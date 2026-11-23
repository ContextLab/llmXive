"""
Prompt-to-Scene Translation Module for PyBullet Physics Filtering.

This module maps natural language prompts (from RobotBench) to:
1. PyBullet asset paths (URDFs for robots, objects).
2. Initial pose configurations (position, orientation) for simulation setup.

It acts as the bridge between the text generation phase (T012) and the
canonical simulation phase (T015).
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

# Import existing project utilities
from src.utils.logging import get_logger
from src.utils.io_utils import ensure_dirs

# Constants for asset resolution
# In a real deployment, these would point to the actual PyBullet data directory
# or a local cache of RobotBench assets.
DEFAULT_ASSET_ROOT = Path(__file__).parent.parent.parent / "data" / "assets"
ROBOTBENCH_ASSETS_URL = "https://huggingface.co/datasets/robotbench/assets/resolve/main"

logger = get_logger(__name__)

# Standard PyBullet asset mappings
# Maps generic object/robot names to URDF file names found in standard PyBullet data
# or RobotBench specific assets.
ASSET_MAPPING = {
    # Robots
    "panda": "franka_panda/panda.urdf",
    "kuka": "kuka_iiwa/iiwa14.urdf",
    "ur5": "ur_description/urdf/ur5_robot.urdf",
    "robotiq_2f85": "robotiq_2f85/robots/robotiq_2f85.urdf",
    # Objects (Standard PyBullet shapes or RobotBench objects)
    "cube": "cube.urdf",
    "box": "cube_small.urdf",
    "sphere": "sphere2.urdf",
    "table": "plane.urdf",  # Often used as a table surface
    "floor": "plane.urdf",
    "target": "target.urdf",  # Generic target object
    "block": "cube_small.urdf",
    "can": "can.urdf",
    "bottle": "bottle.urdf",
}

# Default initial poses (x, y, z, qx, qy, qz, qw)
# (0, 0, 0, 0, 0, 0, 1) is identity
DEFAULT_POSES = {
    "table": (0, 0, 0, 0, 0, 0, 1),
    "floor": (0, 0, 0, 0, 0, 0, 1),
    "panda": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0), # Base at origin
    "kuka": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    "ur5": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
}

def parse_prompt_for_objects(prompt: str) -> List[str]:
    """
    Extracts potential object and robot names from a natural language prompt.
    Uses a simple keyword matching approach against known asset names.

    Args:
        prompt: The natural language text description.

    Returns:
        A list of unique object/robot identifiers found in the prompt.
    """
    prompt_lower = prompt.lower()
    found_objects = []

    # Check against known asset keys
    for key in ASSET_MAPPING.keys():
        if key in prompt_lower:
            found_objects.append(key)

    # Remove duplicates while preserving order
    seen = set()
    unique_objects = []
    for obj in found_objects:
        if obj not in seen:
            seen.add(obj)
            unique_objects.append(obj)

    logger.debug(f"Parsed objects from prompt: {unique_objects}")
    return unique_objects

def resolve_asset_path(object_name: str, asset_root: Optional[Path] = None) -> Optional[str]:
    """
    Resolves a logical object name to a file path for the URDF.

    Args:
        object_name: The identifier (e.g., 'panda', 'cube').
        asset_root: Optional override for the asset root directory.

    Returns:
        Absolute path to the URDF file, or None if not found.
    """
    root = asset_root or DEFAULT_ASSET_ROOT
    
    # Check mapping
    if object_name in ASSET_MAPPING:
        relative_path = ASSET_MAPPING[object_name]
        full_path = root / relative_path
        
        # If it exists, return string path
        if full_path.exists():
            return str(full_path)
        
        # Fallback: Check if it's a standard PyBullet path
        # PyBullet data is often installed in site-packages
        import pybullet_data
        try:
            pybullet_path = pybullet_data.getDataPath()
            candidate = Path(pybullet_path) / relative_path
            if candidate.exists():
                logger.info(f"Resolved '{object_name}' via PyBullet data path: {candidate}")
                return str(candidate)
        except Exception as e:
            logger.warning(f"Could not access pybullet_data: {e}")

    logger.warning(f"Asset not found for object: {object_name}. Expected: {root}/{ASSET_MAPPING.get(object_name, 'UNKNOWN')}")
    return None

def parse_initial_pose(prompt: str, object_name: str) -> Tuple[float, float, float, float, float, float, float]:
    """
    Attempts to parse specific coordinates from the prompt.
    Falls back to default pose if parsing fails or no coordinates found.

    Simple heuristic: looks for patterns like "at (x, y, z)" or "x=1.0".
    
    Args:
        prompt: The full prompt text.
        object_name: The object to look for coordinates for.

    Returns:
        A tuple (x, y, z, qx, qy, qz, qw).
    """
    # Default to identity or object-specific default
    if object_name in DEFAULT_POSES:
        return DEFAULT_POSES[object_name]
    
    default = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)

    # Regex to find "at (x, y, z)" or similar
    # Pattern: at\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)
    pattern = r"at\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)"
    match = re.search(pattern, prompt)
    
    if match:
        try:
            x, y, z = map(float, match.groups())
            logger.debug(f"Parsed pose for {object_name}: ({x}, {y}, {z})")
            return (x, y, z, 0.0, 0.0, 0.0, 1.0) # Default orientation
        except ValueError:
            pass

    # Pattern: x=1.0, y=2.0, z=3.0
    x_match = re.search(rf"{object_name}\s*x\s*=\s*([\d.]+)", prompt, re.IGNORECASE)
    y_match = re.search(rf"{object_name}\s*y\s*=\s*([\d.]+)", prompt, re.IGNORECASE)
    z_match = re.search(rf"{object_name}\s*z\s*=\s*([\d.]+)", prompt, re.IGNORECASE)

    if x_match and y_match and z_match:
        try:
            x = float(x_match.group(1))
            y = float(y_match.group(1))
            z = float(z_match.group(1))
            return (x, y, z, 0.0, 0.0, 0.0, 1.0)
        except ValueError:
            pass

    return default

def translate_prompt_to_scene(prompt: str) -> Dict[str, Any]:
    """
    Main entry point for translating a text prompt into a simulation scene configuration.

    This function:
    1. Parses the prompt for object/robot names.
    2. Resolves URDF paths for each object.
    3. Determines initial poses.
    4. Returns a structured dictionary ready for PyBullet loading.

    Args:
        prompt: Natural language description of the scene.

    Returns:
        A dictionary with keys:
          - 'prompt': The original prompt string.
          - 'objects': List of dicts with 'name', 'urdf_path', 'initial_pose'.
          - 'status': 'success' or 'partial' (if some assets missing).
    """
    logger.info(f"Translating prompt to scene: {prompt[:50]}...")
    
    objects_found = parse_prompt_for_objects(prompt)
    scene_config = {
        "prompt": prompt,
        "objects": [],
        "status": "success"
    }

    missing_assets = []

    for obj_name in objects_found:
        urdf_path = resolve_asset_path(obj_name)
        pose = parse_initial_pose(prompt, obj_name)

        if urdf_path:
            scene_config["objects"].append({
                "name": obj_name,
                "urdf_path": urdf_path,
                "initial_pose": list(pose)
            })
        else:
            missing_assets.append(obj_name)
            # We do not fail completely; we log and continue. 
            # The simulation step (T015) will handle missing assets by skipping or erroring.
    
    if missing_assets:
        scene_config["status"] = "partial"
        scene_config["missing_assets"] = missing_assets
        logger.warning(f"Missing assets for prompt: {missing_assets}")

    return scene_config

def save_scene_config(scene_config: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Saves the generated scene configuration to a JSON file.

    Args:
        scene_config: The dictionary returned by translate_prompt_to_scene.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    ensure_dirs(output_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scene_config, f, indent=2)
    
    logger.info(f"Scene config saved to {output_path}")

def main():
    """
    CLI entry point for testing prompt-to-scene translation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Translate text prompts to PyBullet scene configs.")
    parser.add_argument("--prompt", type=str, required=True, help="The text prompt to translate.")
    parser.add_argument("--output", type=str, default="data/curated/scene_config.json", help="Output JSON path.")
    
    args = parser.parse_args()
    
    result = translate_prompt_to_scene(args.prompt)
    save_scene_config(result, args.output)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
