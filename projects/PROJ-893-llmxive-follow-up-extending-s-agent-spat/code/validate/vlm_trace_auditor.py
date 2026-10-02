import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set

# Import Config to ensure paths are resolved correctly
try:
    from config import Config
except ImportError:
    # Fallback if running as script directly without package context
    Config = type('Config', (), {
        'DATA_RAW': Path('data/raw'),
        'DATA_RESULTS': Path('data/results'),
        'DATA_DERIVED': Path('data/derived')
    })

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num} in {file_path}: {e}")
    return records

def load_json(file_path: Path) -> Any:
    """Load a standard JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_dry_run_status(dry_run_path: Path) -> bool:
    """
    Check if the dry-run status indicates 'pass'.
    Returns True if pass, False otherwise.
    """
    if not dry_run_path.exists():
        return False
    
    try:
        data = load_json(dry_run_path)
        return data.get('status') == 'pass'
    except (json.JSONDecodeError, KeyError, TypeError):
        return False

def audit_vlm_traces(
    sampled_scenes_path: Path,
    vlm_baseline_path: Path,
    constraints_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Perform the VLM trace audit.
    
    Checks:
    1. VLM baseline data corresponds to exact scene IDs in sampled_scenes.jsonl.
    2. No tool-call traces are leaked into the symbolic input (constraints).
    
    Returns a result dictionary with 'status' and 'discrepancies'.
    """
    discrepancies = []
    status = "pass"

    # 1. Load sampled scenes to get the list of expected IDs
    try:
        sampled_scenes = load_jsonl(sampled_scenes_path)
        expected_ids = {scene['scene_id'] for scene in sampled_scenes}
    except FileNotFoundError:
        return {
            "status": "fail",
            "error": f"Sampled scenes file not found: {sampled_scenes_path}",
            "discrepancies": []
        }
    except (KeyError, TypeError) as e:
        return {
            "status": "fail",
            "error": f"Invalid format in sampled scenes: {e}",
            "discrepancies": []
        }

    # 2. Load VLM baseline to check ID correspondence
    try:
        vlm_baseline = load_jsonl(vlm_baseline_path)
        vlm_ids = {entry['scene_id'] for entry in vlm_baseline}
    except FileNotFoundError:
        return {
            "status": "fail",
            "error": f"VLM baseline file not found: {vlm_baseline_path}",
            "discrepancies": []
        }

    # Check for missing or extra IDs
    missing_in_vlm = expected_ids - vlm_ids
    extra_in_vlm = vlm_ids - expected_ids

    if missing_in_vlm:
        discrepancies.append({
            "type": "missing_vlm_baseline",
            "count": len(missing_in_vlm),
            "sample_ids": list(missing_in_vlm)[:5]  # Limit sample for brevity
        })
        status = "fail"

    if extra_in_vlm:
        discrepancies.append({
            "type": "extra_vlm_baseline",
            "count": len(extra_in_vlm),
            "sample_ids": list(extra_in_vlm)[:5]
        })
        status = "fail"

    # 3. Check for tool-call trace leakage in constraints
    # We inspect the constraints.jsonl for any keys that look like tool traces
    # (e.g., 'tool_call', 'function_call', 'thought_trace', 'raw_response')
    tool_trace_indicators = {
        'tool_call', 'tool_calls', 'function_call', 'thought_trace', 
        'raw_response', 'model_trace', 'intermediate_steps'
    }
    
    try:
        constraints_data = load_jsonl(constraints_path)
        leak_detected = False
        leaked_scenes = []
        
        for scene in constraints_data:
            scene_id = scene.get('scene_id', 'unknown')
            # Check top-level keys and nested 'constraints' list keys
            for key in scene.keys():
                if key.lower() in tool_trace_indicators:
                    leak_detected = True
                    leaked_scenes.append(scene_id)
                    break
            if leak_detected:
                # If we found a leak in this scene, check nested constraints list too
                if 'constraints' in scene and isinstance(scene['constraints'], list):
                    for constraint in scene['constraints']:
                        if isinstance(constraint, dict):
                            for c_key in constraint.keys():
                                if c_key.lower() in tool_trace_indicators:
                                    leak_detected = True
                                    if scene_id not in leaked_scenes:
                                        leaked_scenes.append(scene_id)
                                    break
                            if leak_detected:
                                break
                if leak_detected:
                    break # Stop after finding first few or just flagging
        
        if leak_detected:
            discrepancies.append({
                "type": "tool_trace_leak",
                "count": len(leaked_scenes),
                "sample_ids": leaked_scenes[:5]
            })
            status = "fail"

    except FileNotFoundError:
        # If constraints file is missing, we can't check for leaks, 
        # but this might be a failure condition itself depending on pipeline stage.
        # For this audit, we assume constraints should exist if we are checking VLM purity.
        discrepancies.append({
            "type": "missing_constraints_file",
            "error": f"Constraints file not found: {constraints_path}"
        })
        status = "fail"

    result = {
        "status": status,
        "discrepancies": discrepancies,
        "checked_scenes_count": len(expected_ids),
        "checked_at": "runtime" # Placeholder for timestamp if needed
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    return result

def main():
    parser = argparse.ArgumentParser(description="Audit VLM baseline integrity and trace purity.")
    parser.add_argument(
        "--sampled-scenes",
        type=str,
        default=str(Config.DATA_RAW / "sampled_scenes.jsonl"),
        help="Path to the sampled scenes JSONL file."
    )
    parser.add_argument(
        "--vlm-baseline",
        type=str,
        default=str(Config.DATA_RAW / "vlm_baseline.jsonl"),
        help="Path to the VLM baseline predictions file."
    )
    parser.add_argument(
        "--constraints",
        type=str,
        default=str(Config.DATA_DERIVED / "constraints.jsonl"),
        help="Path to the extracted constraints JSONL file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Config.DATA_RESULTS / "vlm_trace_audit.json"),
        help="Path for the audit result JSON."
    )

    args = parser.parse_args()

    sampled_path = Path(args.sampled_scenes)
    vlm_path = Path(args.vlm_baseline)
    constraints_path = Path(args.constraints)
    output_path = Path(args.output)

    print(f"Starting VLM Trace Audit...")
    print(f"  Sampled Scenes: {sampled_path}")
    print(f"  VLM Baseline: {vlm_path}")
    print(f"  Constraints: {constraints_path}")
    print(f"  Output: {output_path}")

    try:
        result = audit_vlm_traces(sampled_path, vlm_path, constraints_path, output_path)
        
        print(f"Audit Complete. Status: {result['status']}")
        
        if result['discrepancies']:
            for disc in result['discrepancies']:
                print(f"  - Discrepancy: {disc['type']} (Count: {disc.get('count', 'N/A')})")
        
        if result['status'] == 'fail':
            print("CRITICAL: VLM Audit Failed. Pipeline should halt.")
            sys.exit(1)
        else:
            print("VLM Audit Passed.")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during audit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
