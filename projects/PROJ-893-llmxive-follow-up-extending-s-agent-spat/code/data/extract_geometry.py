"""
Extract geometric constraints from the S-AgentK dataset.
Parses JSONL, validates, and outputs constraints.jsonl.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from config import Config

def load_scene_data(input_dir: Path) -> List[Dict[str, Any]]:
    """Load scene data from a JSONL file."""
    raw_file = input_dir / "s_agent_k_subset.jsonl"
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}")
    
    scenes = []
    with open(raw_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                scenes.append(json.loads(line))
    return scenes

def validate_scene_constraints(scene: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a scene's constraints."""
    if 'geometry' not in scene:
        return False, "Missing geometry"
    if 'label' not in scene:
        return False, "Missing label"
    return True, None

def extract_constraints(scenes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract valid constraints and log exclusions."""
    valid_constraints = []
    exclusions = []
    
    for scene in scenes:
        is_valid, reason = validate_scene_constraints(scene)
        if is_valid:
            valid_constraints.append({
                "scene_id": scene.get("id", "unknown"),
                "geometry": scene.get("geometry"),
                "label": scene.get("label")
            })
        else:
            exclusions.append({
                "scene_id": scene.get("id", "unknown"),
                "reason": reason
            })
    
    return valid_constraints, exclusions

def main():
    config = Config()
    logger = config.logger
    
    input_dir = config.DATA_RAW
    output_file = config.DATA_DERIVED / "constraints.jsonl"
    exclusion_log_file = config.DATA_RESULTS / "exclusion_log.json"
    
    os.makedirs(config.DATA_DERIVED, exist_ok=True)
    os.makedirs(config.DATA_RESULTS, exist_ok=True)
    
    logger.info(f"Loading scene data from {input_dir}...")
    try:
        scenes = load_scene_data(input_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Extracting constraints from {len(scenes)} scenes...")
    valid_constraints, exclusions = extract_constraints(scenes)
    
    # Write valid constraints
    with open(output_file, 'w', encoding='utf-8') as f:
        for constraint in valid_constraints:
            f.write(json.dumps(constraint) + '\n')
    
    # Write exclusion log
    exclusion_data = {
        "total_scenes": len(scenes),
        "excluded_count": len(exclusions),
        "exclusions": exclusions
    }
    with open(exclusion_log_file, 'w', encoding='utf-8') as f:
        json.dump(exclusion_data, f, indent=2)
    
    logger.info(f"Extracted {len(valid_constraints)} valid constraints.")
    logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_file}")

if __name__ == "__main__":
    main()
