"""
extract_geometry.py

Parses the S-Agent-300K dataset (loaded via T006) to extract geometric constraints.
Detects malformed or missing data, excludes invalid scenes, and outputs a clean
JSONL file of constraints for the CSP solver.

Requirements:
- The dataset must be present at data/raw/s-agent-300k/ (downloaded by T006).
- The output is written to data/derived/constraints.jsonl.
- Excluded scenes are logged to data/results/exclusion_log.json (via T013 logic,
  but we initialize the exclusion list here for T013 to consume).
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import Config for paths and constants
from config import Config

# Import download utilities for consistency (though we assume data exists)
from data.download import verify_checksum

CONFIG = Config()

def load_scene_data(scene_path: Path) -> Optional[Dict[str, Any]]:
    """
    Loads a single scene's JSON data.
    Returns None if the file is missing, corrupted, or not valid JSON.
    """
    try:
        with open(scene_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        # Log or return None to indicate failure
        return None

def validate_scene_constraints(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates that the scene data contains the required fields for CSP solving.
    Returns (True, "") if valid, (False, reason) if invalid.

    Expected structure (based on S-Agent-300K schema):
    {
      "scene_id": str,
      "objects": [
        {
          "id": str,
          "type": str,
          "dimensions": {"x": float, "y": float, "z": float},
          "position": {"x": float, "y": float, "z": float},
          ...
        },
        ...
      ],
      "constraints": [
        {
          "type": str,
          "args": [...]
        },
        ...
      ],
      "question": str,
      "answer": ...
    }
    """
    required_keys = ["scene_id", "objects", "constraints", "question", "answer"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: {key}"

    if not isinstance(data["objects"], list) or len(data["objects"]) == 0:
        return False, "No objects found in scene"

    if not isinstance(data["constraints"], list):
        return False, "Constraints must be a list"

    # Check object structure
    for obj in data["objects"]:
        if "id" not in obj:
            return False, "Object missing 'id'"
        if "dimensions" not in obj or "position" not in obj:
            return False, f"Object {obj.get('id', 'unknown')} missing dimensions or position"
        
        # Validate numeric types
        dims = obj["dimensions"]
        pos = obj["position"]
        for k, v in list(dims.items()) + list(pos.items()):
            if not isinstance(v, (int, float)):
                return False, f"Non-numeric value in {k}: {v}"

    return True, ""

def extract_constraints(scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms raw scene data into the format expected by the CSP solver.
    """
    return {
        "scene_id": scene_data["scene_id"],
        "objects": scene_data["objects"],
        "constraints": scene_data["constraints"],
        "question": scene_data["question"],
        "answer": scene_data["answer"],
        "source": "s-agent-300k"
    }

def main():
    """
    Main entry point for extracting geometry constraints.
    """
    raw_dir = CONFIG.data_raw_dir / "s-agent-300k"
    if not raw_dir.exists():
        print(f"Error: Raw data directory not found at {raw_dir}. Run T006 first.", file=sys.stderr)
        sys.exit(1)

    # Ensure derived and results directories exist
    CONFIG.derived_dir.mkdir(parents=True, exist_ok=True)
    CONFIG.results_dir.mkdir(parents=True, exist_ok=True)

    output_file = CONFIG.derived_dir / "constraints.jsonl"
    exclusion_log_file = CONFIG.results_dir / "exclusion_log.json"

    valid_scenes = []
    excluded_scenes = []

    # Iterate over all JSON files in the raw directory
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        # Fallback for nested structures if the dataset unpacks differently
        json_files = list(raw_dir.rglob("*.json"))

    if not json_files:
        print(f"Warning: No JSON files found in {raw_dir}.", file=sys.stderr)
        # Write empty outputs to prevent pipeline crash
        with open(output_file, 'w') as f:
            pass
        with open(exclusion_log_file, 'w') as f:
            json.dump({"excluded": [], "reasons": {}, "total_scenes": 0}, f, indent=2)
        return

    print(f"Found {len(json_files)} scene files. Processing...")

    for file_path in json_files:
        scene_id = file_path.stem # Filename without extension
        
        # Load data
        data = load_scene_data(file_path)
        if data is None:
            excluded_scenes.append({
                "scene_id": scene_id,
                "reason": "File missing, corrupted, or invalid JSON"
            })
            continue

        # Validate structure
        is_valid, reason = validate_scene_constraints(data)
        if not is_valid:
            excluded_scenes.append({
                "scene_id": scene_id,
                "reason": reason
            })
            continue

        # Extract and store
        try:
            extracted = extract_constraints(data)
            valid_scenes.append(extracted)
        except Exception as e:
            excluded_scenes.append({
                "scene_id": scene_id,
                "reason": f"Extraction error: {str(e)}"
            })

    # Write valid scenes to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for scene in valid_scenes:
            f.write(json.dumps(scene) + '\n')

    # Prepare exclusion log
    exclusion_log = {
        "total_scenes_processed": len(json_files),
        "valid_scenes": len(valid_scenes),
        "excluded_scenes_count": len(excluded_scenes),
        "excluded": excluded_scenes
    }

    with open(exclusion_log_file, 'w', encoding='utf-8') as f:
        json.dump(exclusion_log, f, indent=2)

    print(f"Extraction complete.")
    print(f"  Valid scenes: {len(valid_scenes)}")
    print(f"  Excluded scenes: {len(excluded_scenes)}")
    print(f"  Output: {output_file}")
    print(f"  Exclusion log: {exclusion_log_file}")

if __name__ == "__main__":
    main()
