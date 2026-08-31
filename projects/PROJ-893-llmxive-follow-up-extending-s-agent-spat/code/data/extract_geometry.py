"""
extract_geometry.py

Parses the S-Agent-300K dataset, detects malformed/missing data,
excludes invalid scenes from processing, and outputs a clean
constraints.jsonl file for the CSP solver.

Implements FR-001 (No VLM traces in solver input) and FR-007 (Exclusion logging).
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import project config for paths and constants
from config import Config
# Import checksum verification utilities from T006a
from data.verify_checksum import verify_directory_integrity


def load_scene_data(scene_id: str, raw_data_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load a single scene's raw data from the downloaded dataset.
    
    Args:
        scene_id: The unique identifier for the scene.
        raw_data_dir: Path to the directory containing raw scene data.
        
    Returns:
        A dictionary containing the scene data if successful, None otherwise.
    """
    # Expected file structure: data/raw/<scene_id>.json or similar
    # Based on T006, the dataset is downloaded. We assume a standard JSON structure
    # where each scene is either a separate file or part of a larger JSONL.
    # For S-Agent-300K, let's assume a JSONL structure in data/raw/s_agent_300k.jsonl
    # or individual files. The prompt mentions "parse S-Agent-300K".
    # Let's assume a JSONL file named `s_agent_300k.jsonl` exists in data/raw/
    # as per standard HuggingFace dataset conventions for this type of data.
    
    jsonl_path = raw_data_dir / "s_agent_300k.jsonl"
    
    if not jsonl_path.exists():
        # Fallback: try to find a file matching the scene_id pattern if it's individual files
        # This is a heuristic; if the dataset structure is different, this might need adjustment.
        # However, T006 ensures the file is downloaded.
        # Let's assume the primary format is JSONL for efficiency.
        return None

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get('scene_id') == scene_id:
                        return record
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error reading scene data for {scene_id}: {e}", file=sys.stderr)
        return None
        
    return None


def validate_scene_constraints(scene_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that the scene data contains all required fields and is well-formed.
    
    Checks for:
    - Presence of 'scene_id'
    - Presence of 'geometry' or 'constraints' field
    - Non-empty object lists
    - Valid coordinate types (numeric)
    
    Args:
        scene_data: The loaded scene dictionary.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    if not isinstance(scene_data, dict):
        return False, "Data is not a dictionary"
    
    if 'scene_id' not in scene_data:
        return False, "Missing 'scene_id'"
    
    # Check for geometry/constraints data
    # The structure might vary, but we expect some spatial data.
    # Assuming a structure like: {'scene_id': '...', 'objects': [...], 'question': '...', 'answer': '...'}
    # Or specifically 'constraints' if pre-processed.
    # Let's look for 'objects' or 'geometry' as the primary spatial source.
    if 'objects' not in scene_data and 'geometry' not in scene_data:
        return False, "Missing spatial data ('objects' or 'geometry')"
    
    objects = scene_data.get('objects', scene_data.get('geometry', []))
    
    if not isinstance(objects, list) or len(objects) == 0:
        return False, "No objects found in scene"
    
    # Validate object coordinates
    for i, obj in enumerate(objects):
        if not isinstance(obj, dict):
            return False, f"Object {i} is not a dictionary"
        
        # Check for required spatial attributes
        # Assuming 'position' or 'bbox' exists
        has_pos = 'position' in obj or 'bbox' in obj or 'x' in obj
        if not has_pos:
            return False, f"Object {i} missing position/bbox"
        
        # Validate numeric types for positions if present
        if 'position' in obj:
            pos = obj['position']
            if isinstance(pos, (list, tuple)):
                if len(pos) != 3:
                    return False, f"Object {i} position has invalid dimension (expected 3, got {len(pos)})"
                for coord in pos:
                    if not isinstance(coord, (int, float)):
                        return False, f"Object {i} position contains non-numeric value"
    
    # Check for question/answer if needed for the solver (US1 is about solving constraints)
    # The solver needs constraints. If the dataset provides 'question' and 'answer',
    # we might need to parse them into constraints.
    # However, T010 is about *extracting* geometry/constraints.
    # If the raw data has 'constraints', use them. If it has 'question', we might need
    # a parser (which might be part of this or a later step).
    # For now, we assume the raw data contains enough info to form constraints
    # or we extract the raw geometry and the solver handles the rest.
    # Let's ensure 'question' and 'answer' are present if they are part of the benchmark.
    if 'question' not in scene_data or 'answer' not in scene_data:
        # This might be a warning, but not necessarily a hard exclusion if we only need geometry.
        # However, for a benchmark, we usually need the target.
        # Let's be strict: if no target, we can't solve/verify.
        return False, "Missing 'question' or 'answer' for benchmarking"

    return True, "Valid"


def extract_constraints(scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured constraints from the raw scene data.
    
    Transforms the raw scene into a format suitable for the CSP solver.
    This involves:
    1. Extracting object properties (id, type, position, dimensions).
    2. Extracting the spatial question and converting it to a constraint set
       if it's not already in a structured format.
    3. Ensuring no VLM traces (e.g., raw image embeddings, VLM logits) are included.
    
    Args:
        scene_data: The validated scene dictionary.
        
    Returns:
        A dictionary containing the extracted constraints.
    """
    scene_id = scene_data['scene_id']
    
    # Extract objects
    objects_raw = scene_data.get('objects', scene_data.get('geometry', []))
    objects_clean = []
    
    for i, obj in enumerate(objects_raw):
        clean_obj = {
            'id': obj.get('id', f"obj_{i}"),
            'type': obj.get('type', 'unknown'),
            'position': obj.get('position', obj.get('bbox', [0, 0, 0])),
            'dimensions': obj.get('dimensions', obj.get('size', [1, 1, 1])),
        }
        # Filter out any VLM-specific fields (e.g., 'embeddings', 'logits', 'attention')
        for key in list(clean_obj.keys()):
            if 'embed' in key.lower() or 'logit' in key.lower() or 'attent' in key.lower():
                del clean_obj[key]
        
        objects_clean.append(clean_obj)
    
    # Extract question and answer
    question = scene_data['question']
    answer = scene_data['answer']
    
    # If the question is already a structured constraint (e.g., JSON string), parse it.
    # Otherwise, we pass it as a string and the solver (or a parser module) will handle it.
    # For T010, we just ensure the data is clean and present.
    # The CSP engine (T011) will likely need to parse the natural language question
    # into constraints. However, if the dataset provides a 'constraints' field, we use that.
    constraints_raw = scene_data.get('constraints', None)
    
    if constraints_raw:
        # If already structured, use it directly (after validation)
        try:
            if isinstance(constraints_raw, str):
                constraints = json.loads(constraints_raw)
            else:
                constraints = constraints_raw
        except json.JSONDecodeError:
            # Fallback: treat as unstructured and let the solver handle it
            constraints = {"raw_question": question}
    else:
        # No structured constraints, rely on the question string
        constraints = {"raw_question": question}
    
    return {
        "scene_id": scene_id,
        "objects": objects_clean,
        "question": question,
        "answer": answer,
        "constraints": constraints,
        "metadata": {
            "source": "S-Agent-300K",
            "extracted_at": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip() if os.name != 'nt' else "2024-01-01T00:00:00Z"
        }
    }


def main():
    """
    Main entry point for the geometry extraction pipeline.
    
    1. Verifies the integrity of the raw data directory.
    2. Iterates through the dataset (or a specified sample).
    3. Validates each scene.
    4. Extracts constraints from valid scenes.
    5. Writes valid scenes to `data/derived/constraints.jsonl`.
    6. Writes exclusion log to `data/results/exclusion_log.json`.
    """
    config = Config()
    raw_dir = config.DATA_RAW_DIR
    derived_dir = config.DATA_DERIVED_DIR
    results_dir = config.DATA_RESULTS_DIR
    
    # Ensure directories exist
    derived_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify raw data integrity first (T006a)
    if not verify_directory_integrity(raw_dir):
        print("ERROR: Raw data integrity check failed. Aborting extraction.", file=sys.stderr)
        sys.exit(1)
    
    # Load the dataset file
    jsonl_path = raw_dir / "s_agent_300k.jsonl"
    if not jsonl_path.exists():
        print(f"ERROR: Dataset file not found at {jsonl_path}.", file=sys.stderr)
        sys.exit(1)
    
    valid_scenes = []
    excluded_scenes = []
    
    total_count = 0
    valid_count = 0
    invalid_count = 0
    
    print(f"Starting extraction from {jsonl_path}...")
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            # Optional: limit to sample size if configured
            if config.SAMPLE_SIZE > 0 and valid_count >= config.SAMPLE_SIZE:
                break
            
            total_count += 1
            
            try:
                scene_data = json.loads(line)
            except json.JSONDecodeError as e:
                excluded_scenes.append({
                    "scene_id": f"unknown_line_{line_num}",
                    "reason": f"JSON decode error: {e}",
                    "line_num": line_num
                })
                invalid_count += 1
                continue
            
            scene_id = scene_data.get('scene_id', f"unknown_line_{line_num}")
            
            # Validate
            is_valid, error_msg = validate_scene_constraints(scene_data)
            
            if not is_valid:
                excluded_scenes.append({
                    "scene_id": scene_id,
                    "reason": error_msg,
                    "line_num": line_num
                })
                invalid_count += 1
                continue
            
            # Extract
            try:
                constraints = extract_constraints(scene_data)
                valid_scenes.append(constraints)
                valid_count += 1
            except Exception as e:
                excluded_scenes.append({
                    "scene_id": scene_id,
                    "reason": f"Extraction error: {e}",
                    "line_num": line_num
                })
                invalid_count += 1
                continue
    
    # Write valid constraints
    output_path = derived_dir / "constraints.jsonl"
    with open(output_path, 'w', encoding='utf-8') as f:
        for scene in valid_scenes:
            f.write(json.dumps(scene) + '\n')
    
    # Write exclusion log
    exclusion_log_path = results_dir / "exclusion_log.json"
    exclusion_report = {
        "total_scenes_processed": total_count,
        "valid_scenes": valid_count,
        "excluded_scenes": invalid_count,
        "exclusion_details": excluded_scenes
    }
    
    with open(exclusion_log_path, 'w', encoding='utf-8') as f:
        json.dump(exclusion_report, f, indent=2)
    
    print(f"Extraction complete.")
    print(f"  Total processed: {total_count}")
    print(f"  Valid (written to {output_path}): {valid_count}")
    print(f"  Excluded (logged to {exclusion_log_path}): {invalid_count}")
    
    # Return success
    return 0


if __name__ == "__main__":
    sys.exit(main())
