import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import config

def load_scene_data(input_dir: Path) -> List[Dict[str, Any]]:
    """Load scene data from raw directory."""
    scenes = []
    # Assuming JSONL format in raw directory
    raw_file = input_dir / "s_agent_k_subset.jsonl"
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}")
    
    with open(raw_file, 'r') as f:
        for line in f:
            if line.strip():
                scenes.append(json.loads(line))
    return scenes

def validate_scene_constraints(scene: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate scene constraints.
    Returns (is_valid, error_message).
    """
    if 'scene_id' not in scene:
        return False, "Missing scene_id"
    if 'geometry' not in scene:
        return False, "Missing geometry"
    if 'label' not in scene:
        return False, "Missing label"
    return True, None

def extract_constraints(scenes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract constraints from valid scenes.
    Returns (valid_constraints, excluded_scenes).
    """
    valid_constraints = []
    excluded_scenes = []

    for scene in scenes:
        is_valid, error_msg = validate_scene_constraints(scene)
        if is_valid:
            valid_constraints.append({
                "scene_id": scene['scene_id'],
                "constraints": scene['geometry'],
                "label": scene['label']
            })
        else:
            excluded_scenes.append({
                "scene_id": scene.get('scene_id', 'unknown'),
                "reason": error_msg
            })

    return valid_constraints, excluded_scenes

def main():
    """Main entry point for geometry extraction."""
    import argparse
    parser = argparse.ArgumentParser(description="Extract geometry constraints")
    parser.add_argument("--input", type=str, required=True, help="Input raw directory")
    parser.add_argument("--output", type=str, required=True, help="Output constraints JSONL")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    # Load scenes
    scenes = load_scene_data(input_dir)
    
    # Extract constraints
    valid_constraints, excluded_scenes = extract_constraints(scenes)
    
    # Write valid constraints
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for constraint in valid_constraints:
            f.write(json.dumps(constraint) + '\n')
    
    # Write exclusion log
    exclusion_log_path = config.DATA_RESULTS / "exclusion_log.json"
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(exclusion_log_path, 'w') as f:
        json.dump({
            "excluded_count": len(excluded_scenes),
            "excluded_scenes": excluded_scenes
        }, f, indent=2)
    
    print(f"Extracted {len(valid_constraints)} valid constraints. Excluded {len(excluded_scenes)} scenes.")

if __name__ == "__main__":
    main()
