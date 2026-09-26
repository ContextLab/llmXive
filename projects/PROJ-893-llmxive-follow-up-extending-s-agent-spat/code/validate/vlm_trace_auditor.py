"""
VLM Trace Auditor for T027.

Validates that no VLM traces (keys: 'tool_call_history', 'vlm_prediction')
are present in the extracted constraints file (data/derived/constraints.jsonl).
This enforces Constitution Principle VII: The symbolic path must be pure.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set

# Import Config from the project's config module
# Note: We assume Config is available as per the API surface
try:
    from config import Config
except ImportError:
    # Fallback for direct execution without package structure
    class Config:
        DATA_DERIVED = "data/derived"
        DATA_RESULTS = "data/results"
        CONSTRAINTS_FILE = "constraints.jsonl"
        AUDIT_OUTPUT = "vlm_trace_audit.json"

# Define the forbidden keys that indicate VLM contamination
FORBIDDEN_KEYS = {'tool_call_history', 'vlm_prediction', 'vlm_trace', 'tool_calls'}

def check_dry_run_status() -> bool:
    """
    Verifies that the dry-run validation (T029) passed successfully.
    Returns True if dry_run_status.json indicates 'pass', False otherwise.
    """
    dry_run_path = Path(Config.DATA_RESULTS) / "dry_run_status.json"
    
    if not dry_run_path.exists():
        print(f"ERROR: Dry-run status file not found at {dry_run_path}. "
              "T029 must be executed before T027.")
        return False
    
    try:
        with open(dry_run_path, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
        
        if status_data.get('status') != 'pass':
            print(f"ERROR: Dry-run status is '{status_data.get('status')}'. "
                  "T027 requires T029 to pass.")
            return False
        
        return True
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: Failed to parse dry-run status: {e}")
        return False

def audit_vlm_traces(input_path: Path, forbidden_keys: Set[str]) -> Dict[str, Any]:
    """
    Scans the constraints JSONL file for forbidden VLM trace keys.
    
    Args:
        input_path: Path to the constraints.jsonl file.
        forbidden_keys: Set of keys that indicate VLM contamination.
        
    Returns:
        A dictionary with the audit result.
    """
    trace_keys_found = set()
    total_scenes = 0
    scanned_scenes = 0
    first_violation_scene_id = None
    
    if not input_path.exists():
        return {
            "status": "fail",
            "error": f"Input file not found: {input_path}",
            "trace_keys_found": [],
            "total_scenes": 0,
            "scanned_scenes": 0
        }
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    scene_data = json.loads(line)
                    total_scenes += 1
                    
                    # Check top-level keys
                    if isinstance(scene_data, dict):
                        for key in scene_data.keys():
                            if key in forbidden_keys:
                                trace_keys_found.add(key)
                                if first_violation_scene_id is None:
                                    first_violation_scene_id = scene_data.get('scene_id', 'unknown')
                
                except json.JSONDecodeError as e:
                    # Log malformed lines but continue scanning
                    print(f"WARNING: Malformed JSON at line {line_num}: {e}")
                    continue
                
                scanned_scenes += 1
                
                # Stop early if traces are found to prevent unnecessary processing
                if trace_keys_found:
                    break
    
    except Exception as e:
        return {
            "status": "fail",
            "error": f"Failed to read input file: {e}",
            "trace_keys_found": [],
            "total_scenes": total_scenes,
            "scanned_scenes": scanned_scenes
        }
    
    if trace_keys_found:
        return {
            "status": "fail",
            "trace_keys_found": sorted(list(trace_keys_found)),
            "total_scenes": total_scenes,
            "scanned_scenes": scanned_scenes,
            "first_violation_scene_id": first_violation_scene_id,
            "message": f"VIOLATION: VLM traces detected in constraint data. Aborting."
        }
    else:
        return {
            "status": "pass",
            "trace_keys_found": [],
            "total_scenes": total_scenes,
            "scanned_scenes": scanned_scenes,
            "message": "Audit passed: No VLM traces detected."
        }

def main():
    """
    Main entry point for the VLM Trace Auditor.
    """
    parser = argparse.ArgumentParser(
        description="Audit constraints.jsonl for VLM traces (T027)."
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help="Path to constraints.jsonl. Defaults to Config.DATA_DERIVED/constraints.jsonl"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Path to output audit JSON. Defaults to Config.DATA_RESULTS/vlm_trace_audit.json"
    )
    
    args = parser.parse_args()
    
    # Determine input path
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = Path(Config.DATA_DERIVED) / Config.CONSTRAINTS_FILE
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(Config.DATA_RESULTS) / Config.AUDIT_OUTPUT
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting VLM Trace Audit for: {input_path}")
    
    # Step 1: Check Dry-Run Status
    if not check_dry_run_status():
        print("ABORTING: Dry-run validation failed or missing.")
        sys.exit(1)
    
    # Step 2: Perform Audit
    result = audit_vlm_traces(input_path, FORBIDDEN_KEYS)
    
    # Step 3: Write Output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Audit result written to: {output_path}")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'fail':
        print(f"ERROR: {result.get('message', 'Unknown error')}")
        if 'trace_keys_found' in result:
            print(f"Found keys: {result['trace_keys_found']}")
        if 'first_violation_scene_id' in result:
            print(f"First violation in scene: {result['first_violation_scene_id']}")
        sys.exit(1)
    else:
        print("SUCCESS: No VLM traces found. Pipeline can proceed.")
        sys.exit(0)

if __name__ == '__main__':
    main()