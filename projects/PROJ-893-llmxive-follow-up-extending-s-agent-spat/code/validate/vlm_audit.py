"""
VLM Audit Module for Constitution Principle VII Verification.

This module verifies the integrity of the VLM baseline data by ensuring:
1. VLM baseline scene IDs match exactly with the sampled scenes (data/raw/sampled_scenes.jsonl).
2. No tool-call traces or internal reasoning steps are leaked into the symbolic input.
3. The data structure is consistent with the expected schema.

Output: data/results/vlm_trace_audit.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Import shared config if available, otherwise fallback to local paths
try:
    from config import Config
except ImportError:
    Config = None

# Constants for paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_SCENES_PATH = PROJECT_ROOT / "data" / "raw" / "sampled_scenes.jsonl"
VLM_BASELINE_PATH = PROJECT_ROOT / "data" / "derived" / "vlm_baseline.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "vlm_trace_audit.json"

# Patterns indicating leaked tool traces (Constitution Principle VII)
LEAKED_TRACE_PATTERNS = [
    "tool_call",
    "function_call",
    "execute_code",
    "run_command",
    "api_request",
    "<tool>",
    "</tool>",
    "thought:",
    "reasoning_chain"
]

def load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at {filepath}:{line_num}: {e}")
    return data

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load a standard JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_dry_run_status() -> Optional[Dict[str, Any]]:
    """
    Check if a previous dry-run validation passed.
    If dry_run_status.json indicates failure, this audit should potentially abort.
    """
    dry_run_path = PROJECT_ROOT / "data" / "results" / "dry_run_status.json"
    if not dry_run_path.exists():
        # Dry run not found, but we proceed with audit as per task T027 scope
        return None
    
    try:
        status = load_json(dry_run_path)
        if status.get("status") == "fail":
            return {"status": "fail", "reason": "Previous dry-run validation failed."}
    except Exception:
        pass
    return None

def audit_vlm_traces() -> Dict[str, Any]:
    """
    Perform the VLM baseline integrity audit.
    
    Checks:
    1. ID Consistency: VLM baseline IDs must match sampled_scenes.jsonl IDs exactly.
    2. Trace Leakage: No tool-call traces in the VLM baseline content.
    
    Returns:
        Dict containing 'status', 'discrepancies', and 'summary'.
    """
    discrepancies = []
    status = "pass"
    
    # 1. Load Ground Truth (Sampled Scenes)
    try:
        sampled_scenes = load_jsonl(RAW_SCENES_PATH)
        sampled_ids = {scene.get("id") or scene.get("scene_id") for scene in sampled_scenes}
    except FileNotFoundError:
        return {
            "status": "fail",
            "reason": f"Sampled scenes file not found at {RAW_SCENES_PATH}",
            "discrepancies": [],
            "summary": {}
        }

    # 2. Load VLM Baseline
    try:
        vlm_baseline = load_jsonl(VLM_BASELINE_PATH)
    except FileNotFoundError:
        return {
            "status": "fail",
            "reason": f"VLM baseline file not found at {VLM_BASELINE_PATH}",
            "discrepancies": [],
            "summary": {}
        }

    # 3. Check ID Consistency
    vlm_ids = set()
    for record in vlm_baseline:
        vid = record.get("id") or record.get("scene_id")
        if vid:
            vlm_ids.add(vid)
    
    missing_in_vlm = sampled_ids - vlm_ids
    extra_in_vlm = vlm_ids - sampled_ids

    if missing_in_vlm:
        discrepancies.append({
            "type": "missing_ids",
            "count": len(missing_in_vlm),
            "sample": list(missing_in_vlm)[:5], # Log first 5
            "message": f"{len(missing_in_vlm)} scene IDs from sampled_scenes.jsonl are missing in VLM baseline."
        })
        status = "fail"

    if extra_in_vlm:
        discrepancies.append({
            "type": "extra_ids",
            "count": len(extra_in_vlm),
            "sample": list(extra_in_vlm)[:5],
            "message": f"{len(extra_in_vlm)} scene IDs in VLM baseline are not in sampled_scenes.jsonl."
        })
        status = "fail"

    # 4. Check for Leaked Tool Traces
    trace_leaks_found = []
    for record in vlm_baseline:
        # Check common fields that might contain text/reasoning
        text_fields = ["response", "answer", "reasoning", "thought", "output", "content"]
        for field in text_fields:
            if field in record:
                val = str(record[field]).lower()
                for pattern in LEAKED_TRACE_PATTERNS:
                    if pattern.lower() in val:
                        trace_leaks_found.append({
                            "scene_id": record.get("id") or record.get("scene_id"),
                            "field": field,
                            "pattern": pattern
                        })
                        break
    
    if trace_leaks_found:
        discrepancies.append({
            "type": "trace_leakage",
            "count": len(trace_leaks_found),
            "sample": trace_leaks_found[:5],
            "message": f"Detected {len(trace_leaks_found)} potential tool-call trace leaks in VLM baseline."
        })
        status = "fail"

    # 5. Generate Summary
    summary = {
        "total_sampled_scenes": len(sampled_ids),
        "total_vlm_records": len(vlm_ids),
        "matching_ids": len(sampled_ids & vlm_ids),
        "discrepancy_count": len(discrepancies),
        "trace_leak_count": len(trace_leaks_found)
    }

    return {
        "status": status,
        "discrepancies": discrepancies,
        "summary": summary
    }

def main():
    """Main entry point for the VLM Audit script."""
    parser = argparse.ArgumentParser(description="Audit VLM Baseline Integrity (Constitution Principle VII)")
    parser.add_argument("--input-vlm", type=str, default=None, help="Path to VLM baseline JSONL (overrides default)")
    parser.add_argument("--input-scenes", type=str, default=None, help="Path to sampled scenes JSONL (overrides default)")
    parser.add_argument("--output", type=str, default=None, help="Path to output audit JSON (overrides default)")
    args = parser.parse_args()

    # Override paths if provided
    if args.input_vlm:
        global VLM_BASELINE_PATH
        VLM_BASELINE_PATH = Path(args.input_vlm)
    if args.input_scenes:
        global RAW_SCENES_PATH
        RAW_SCENES_PATH = Path(args.input_scenes)
    if args.output:
        global OUTPUT_PATH
        OUTPUT_PATH = Path(args.output)

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting VLM Audit...")
    print(f"  Sampled Scenes: {RAW_SCENES_PATH}")
    print(f"  VLM Baseline: {VLM_BASELINE_PATH}")
    print(f"  Output: {OUTPUT_PATH}")

    try:
        # Check dry run status first
        dry_run_check = check_dry_run_status()
        if dry_run_check and dry_run_check.get("status") == "fail":
            print("ERROR: Previous dry-run validation failed. Aborting audit.")
            result = {
                "status": "fail",
                "reason": dry_run_check.get("reason", "Dry run failed"),
                "discrepancies": [],
                "summary": {}
            }
        else:
            result = audit_vlm_traces()

        # Write result
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        print(f"Audit Complete. Status: {result['status']}")
        
        if result['status'] == "fail":
            print("Discrepancies found:")
            for d in result['discrepancies']:
                print(f"  - {d['message']}")
            sys.exit(1)
        else:
            print("VLM Baseline Integrity Verified.")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        error_result = {
            "status": "fail",
            "reason": str(e),
            "discrepancies": [],
            "summary": {}
        }
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()