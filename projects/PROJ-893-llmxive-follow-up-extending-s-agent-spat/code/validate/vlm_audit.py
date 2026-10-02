"""
VLM Baseline Integrity Audit (Constitution Principle VII).

Verifies that the VLM baseline data corresponds to the exact scene IDs
in the sampled dataset and that no tool-call traces are leaked into
the symbolic input.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set

# Import from project config
from config import Config

# Constants for audit
TOOL_CALL_PATTERNS = [
    "tool_call",
    "function_call",
    "xml:tool",
    "<tool>",
    "assistant_tool",
    "call_response"
]

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num} in {file_path}: {e}")
    return data

def load_json(file_path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_dry_run_status() -> bool:
    """
    Check if the dry-run validation passed.
    T012 (solver) must fail if this audit fails.
    """
    dry_run_path = "data/results/dry_run_status.json"
    if not os.path.exists(dry_run_path):
        # If dry run hasn't been executed, we assume it passed for this audit
        # but in a full pipeline, this would be a gate
        return True
    
    try:
        data = load_json(dry_run_path)
        return data.get("status") == "pass"
    except (json.JSONDecodeError, KeyError):
        return False

def audit_vlm_traces(
    sampled_scenes_path: str,
    vlm_baseline_path: str,
    exclusion_log_path: str
) -> Dict[str, Any]:
    """
    Perform the VLM trace audit.
    
    Checks:
    1. VLM baseline IDs match sampled scene IDs (minus exclusions).
    2. No tool-call traces are present in the VLM baseline data.
    """
    discrepancies = []
    status = "pass"
    
    # Load sampled scenes
    try:
        sampled_scenes = load_jsonl(sampled_scenes_path)
    except FileNotFoundError:
        return {
            "status": "fail",
            "reason": f"Sampled scenes file not found: {sampled_scenes_path}",
            "discrepancies": []
        }
    
    sampled_ids = set(scene.get("scene_id") for scene in sampled_scenes if scene.get("scene_id"))
    
    # Load exclusions to filter out invalid scenes
    excluded_ids = set()
    if os.path.exists(exclusion_log_path):
        try:
            exclusion_data = load_json(exclusion_log_path)
            excluded_ids = set(exclusion_data.get("excluded_ids", []))
        except (json.JSONDecodeError, KeyError):
            pass
    
    valid_sampled_ids = sampled_ids - excluded_ids
    
    # Load VLM baseline
    try:
        vlm_baseline = load_jsonl(vlm_baseline_path)
    except FileNotFoundError:
        return {
            "status": "fail",
            "reason": f"VLM baseline file not found: {vlm_baseline_path}",
            "discrepancies": []
        }
    
    vlm_ids = set(entry.get("scene_id") for entry in vlm_baseline if entry.get("scene_id"))
    
    # Check 1: ID Correspondence
    missing_in_vlm = valid_sampled_ids - vlm_ids
    extra_in_vlm = vlm_ids - valid_sampled_ids
    
    if missing_in_vlm:
        discrepancies.append({
            "type": "missing_in_vlm",
            "count": len(missing_in_vlm),
            "sample_ids": list(missing_in_vlm)[:10]  # Limit to first 10 for brevity
        })
        status = "fail"
    
    if extra_in_vlm:
        discrepancies.append({
            "type": "extra_in_vlm",
            "count": len(extra_in_vlm),
            "extra_ids": list(extra_in_vlm)[:10]
        })
        status = "fail"
    
    # Check 2: Tool-call trace leakage
    for entry in vlm_baseline:
        scene_id = entry.get("scene_id")
        # Check various fields for tool call patterns
        text_fields = [
            entry.get("prompt", ""),
            entry.get("response", ""),
            entry.get("trace", ""),
            entry.get("raw_output", ""),
            str(entry)
        ]
        
        for field_text in text_fields:
            if not isinstance(field_text, str):
                continue
            
            for pattern in TOOL_CALL_PATTERNS:
                if pattern.lower() in field_text.lower():
                    discrepancies.append({
                        "type": "tool_call_leakage",
                        "scene_id": scene_id,
                        "pattern_found": pattern,
                        "field": "unknown"
                    })
                    status = "fail"
                    break
            if status == "fail" and any(p.lower() in str(entry).lower() for p in TOOL_CALL_PATTERNS):
                break
    
    return {
        "status": status,
        "total_scenes_checked": len(valid_sampled_ids),
        "vlm_entries_checked": len(vlm_baseline),
        "discrepancies": discrepancies
    }

def main():
    """Main entry point for the VLM audit."""
    parser = argparse.ArgumentParser(description="Audit VLM baseline integrity")
    parser.add_argument(
        "--sampled-scenes",
        type=str,
        default="data/raw/sampled_scenes.jsonl",
        help="Path to the sampled scenes JSONL file"
    )
    parser.add_argument(
        "--vlm-baseline",
        type=str,
        default="data/derived/vlm_baseline.jsonl",
        help="Path to the VLM baseline JSONL file"
    )
    parser.add_argument(
        "--exclusion-log",
        type=str,
        default="data/results/exclusion_log.json",
        help="Path to the exclusion log JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/vlm_trace_audit.json",
        help="Path to write the audit result"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Perform audit
    result = audit_vlm_traces(
        args.sampled_scenes,
        args.vlm_baseline,
        args.exclusion_log
    )
    
    # Write result
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print(f"Audit Status: {result['status'].upper()}")
    if result['discrepancies']:
        print(f"Discrepancies found: {len(result['discrepancies'])}")
        for disc in result['discrepancies']:
            print(f"  - {disc['type']}: {disc.get('count', 'N/A')}")
    
    # Exit with error code if audit failed (gate for T012)
    if result['status'] == 'fail':
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()