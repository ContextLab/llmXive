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
                try:
                    scenes.append(json.loads(line))
                except json.JSONDecodeError as e:
                    # Log malformed JSON lines as invalid scenes
                    scenes.append({"id": f"malformed_{hashlib.md5(line.encode()).hexdigest()[:8]}", "error": str(e)})
    return scenes

def validate_scene_constraints(scene: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a scene's constraints."""
    if 'error' in scene:
        return False, "Malformed JSON"
    if 'geometry' not in scene:
        return False, "Missing geometry"
    if 'label' not in scene:
        return False, "Missing label"
    if not isinstance(scene.get("geometry"), dict):
        return False, "Invalid geometry format"
    if not isinstance(scene.get("label"), (int, float)):
        return False, "Invalid label format"
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
    # Config might not have a logger attribute if __getattr__ isn't fully implemented yet
    # Use a simple fallback or direct print if needed, but relying on Config's interface
    logger = getattr(config, 'logger', None)
    if not logger:
        class SimpleLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        logger = SimpleLogger()
    
    input_dir = getattr(config, 'DATA_RAW', Path("data/raw"))
    output_file = getattr(config, 'DATA_DERIVED', Path("data/derived")) / "constraints.jsonl"
    exclusion_log_file = getattr(config, 'DATA_RESULTS', Path("data/results")) / "exclusion_log.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    os.makedirs(os.path.dirname(exclusion_log_file), exist_ok=True)
    
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
    
    # Write exclusion log with required schema keys
    exclusion_data = {
        "total_scenes": len(scenes),
        "excluded_count": len(exclusions),
        "excluded_ids": [exc["scene_id"] for exc in exclusions],
        "exclusions": exclusions
    }
    with open(exclusion_log_file, 'w', encoding='utf-8') as f:
        json.dump(exclusion_data, f, indent=2)
    
    logger.info(f"Extracted {len(valid_constraints)} valid constraints.")
    logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_file}")

if __name__ == "__main__":
    main()
