import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config import config
from data.verify_checksum import verify_directory_integrity

def load_scene_data(input_dir: Path) -> List[Dict[str, Any]]:
    """Load scene data from JSONL file."""
    scene_file = input_dir / "s-agent-300k.jsonl"
    if not scene_file.exists():
        raise FileNotFoundError(f"Scene file not found: {scene_file}")
    
    scenes = []
    with open(scene_file, 'r') as f:
        for line in f:
            if line.strip():
              scenes.append(json.loads(line))
    return scenes

def validate_scene_constraints(scene: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate scene constraints.
    Returns (is_valid, error_reason).
    """
    if 'constraints' not in scene:
        return False, "Missing constraints"
    if not isinstance(scene['constraints'], list):
        return False, "Constraints must be a list"
    if len(scene['constraints']) == 0:
        return False, "Empty constraints"
    return True, None

def extract_constraints(scenes: List[Dict[str, Any]], output_path: Path, exclusion_log_path: Path) -> List[Dict[str, Any]]:
    """
    Extract valid constraints and write to output.
    Logs excluded scenes to exclusion_log.
    """
    valid_scenes = []
    excluded_scenes = []

    for scene in scenes:
        scene_id = scene.get('scene_id', 'unknown')
        is_valid, reason = validate_scene_constraints(scene)
        
        if is_valid:
            valid_scenes.append({
                "scene_id": scene_id,
                "constraints": scene['constraints'],
                "metadata": scene.get('metadata', {})
            })
        else:
            excluded_scenes.append({
                "scene_id": scene_id,
                "reason": reason
            })

    # Write valid constraints
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for scene in valid_scenes:
            f.write(json.dumps(scene) + '\n')

    # Write exclusion log
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_data = {
        "total_scenes": len(scenes),
        "valid_scenes": len(valid_scenes),
        "excluded_scenes": len(excluded_scenes),
        "exclusions": excluded_scenes
    }
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)

    print(f"Extracted {len(valid_scenes)} valid scenes. Excluded {len(excluded_scenes)} scenes.")
    return valid_scenes

def main():
    parser = argparse.ArgumentParser(description="Extract geometry constraints")
    parser.add_argument("--input", type=str, default=str(config.DATA_RAW), help="Input directory")
    parser.add_argument("--output", type=str, default=str(config.DATA_DERIVED / "constraints.jsonl"), help="Output file")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)
    exclusion_log_path = config.DATA_RESULTS / "exclusion_log.json"

    # Verify integrity before extraction
    if not verify_directory_integrity(input_dir):
        print("Integrity check failed. Aborting extraction.")
        sys.exit(1)

    scenes = load_scene_data(input_dir)
    extract_constraints(scenes, output_path, exclusion_log_path)

if __name__ == "__main__":
    main()
