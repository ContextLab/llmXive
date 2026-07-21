"""
Task T022: Merge rule-engine logs with external baseline logs.

Implements logic to merge CI rule-engine logs (results.csv) with external
baseline logs (baseline_results.json) into a single results.csv, ensuring
strict ID matching for paired comparison using the manifest.
"""
import json
import csv
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import from sibling modules as per API surface
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
MANIFEST_PATH = DATA_DERIVED / "experiment_manifest.csv"
RULE_ENGINE_RESULTS_PATH = DATA_DERIVED / "results.csv"
BASELINE_RESULTS_PATH = DATA_DERIVED / "baseline_results.json"
FINAL_RESULTS_PATH = DATA_DERIVED / "results.csv"  # Overwrite/Update the single file

# Expected schema for baseline results (from T021/T021b)
# Expected: List of dicts with keys: task_id, time_to_pivot, success (or similar)
# The merge logic must align these with the rule engine results.

def load_manifest() -> List[Dict[str, str]]:
    """Load the experiment manifest."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    
    with open(MANIFEST_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_rule_engine_results() -> Dict[str, Dict[str, Any]]:
    """
    Load existing rule-engine results from results.csv.
    Returns a dict keyed by task_id for O(1) lookup.
    """
    results = {}
    if not RULE_ENGINE_RESULTS_PATH.exists():
        logger.warning(f"Rule engine results not found at {RULE_ENGINE_RESULTS_PATH}. Starting fresh.")
        return results

    with open(RULE_ENGINE_RESULTS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure task_id is the key
            tid = row.get('task_id')
            if tid:
                results[tid] = row
    return results

def load_baseline_results() -> Dict[str, Dict[str, Any]]:
    """
    Load external baseline results from baseline_results.json.
    Returns a dict keyed by task_id.
    """
    if not BASELINE_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Baseline results not found at {BASELINE_RESULTS_PATH}. "
                                "T021b must complete successfully before running this merge.")
    
    with open(BASELINE_RESULTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Normalize to a dict keyed by task_id
    # Expected format: list of objects with 'task_id'
    if isinstance(data, list):
        return {item['task_id']: item for item in data}
    elif isinstance(data, dict):
        # If it's already a dict keyed by task_id, return as is
        return data
    else:
        raise ValueError(f"Unexpected baseline results format: {type(data)}")

def merge_results(manifest: List[Dict[str, str]], 
                  rule_engine_data: Dict[str, Dict[str, Any]], 
                  baseline_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge rule-engine and baseline results based on the manifest.
    Ensures strict ID matching.
    
    Returns a list of rows to be written to results.csv.
    Columns: task_id, method, time_to_pivot, success, failure_type
    """
    merged_rows = []
    manifest_task_ids = set()
    
    logger.info(f"Processing {len(manifest)} tasks from manifest...")
    
    for entry in manifest:
        tid = entry.get('task_id')
        failure_type = entry.get('failure_type', 'Unknown')
        manifest_task_ids.add(tid)
        
        if not tid:
            logger.warning("Skipping manifest entry with missing task_id")
            continue

        row = {
            'task_id': tid,
            'failure_type': failure_type
        }

        # 1. Rule Engine Data
        if tid in rule_engine_data:
            re_row = rule_engine_data[tid]
            row['method'] = 'rule_engine'
            row['time_to_pivot'] = re_row.get('time_to_pivot', '')
            row['success'] = re_row.get('success', '')
            merged_rows.append(row.copy())
        else:
            logger.warning(f"Rule engine result missing for task {tid} (in manifest)")

        # 2. Baseline Data
        if tid in baseline_data:
            bl_row = baseline_data[tid]
            # Map baseline keys to our standard schema if necessary
            # Assuming baseline JSON has: task_id, time_to_pivot, success
            row['method'] = 'baseline'
            row['time_to_pivot'] = bl_row.get('time_to_pivot', '')
            row['success'] = bl_row.get('success', '')
            merged_rows.append(row.copy())
        else:
            logger.warning(f"Baseline result missing for task {tid} (in manifest)")

    # Verify strict matching: every task in manifest should ideally have both
    # (though the task says "merge", implying we output what we have, 
    # but strict ID matching ensures we only output rows for IDs in the manifest)
    
    logger.info(f"Merged {len(merged_rows)} total rows.")
    return merged_rows

def write_merged_results(rows: List[Dict[str, Any]], output_path: Path):
    """Write the merged results to CSV."""
    if not rows:
        logger.warning("No rows to write.")
        return

    # Define standard columns
    fieldnames = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Ensure all keys exist, fill empty if missing
            safe_row = {k: row.get(k, '') for k in fieldnames}
            writer.writerow(safe_row)
    
    logger.info(f"Wrote merged results to {output_path}")

def run_experiments():
    """
    Main entry point for T022: Merge results.
    """
    log_stage_start("T022_Merge_Results")
    
    try:
        # 1. Load Manifest
        manifest = load_manifest()
        logger.info(f"Loaded manifest with {len(manifest)} tasks.")

        # 2. Load Rule Engine Results (if they exist)
        rule_engine_data = load_rule_engine_results()
        logger.info(f"Loaded {len(rule_engine_data)} rule engine results.")

        # 3. Load Baseline Results (Mandatory for this task)
        baseline_data = load_baseline_results()
        logger.info(f"Loaded {len(baseline_data)} baseline results.")

        # 4. Merge
        merged_rows = merge_results(manifest, rule_engine_data, baseline_data)

        # 5. Write Final Output
        write_merged_results(merged_rows, FINAL_RESULTS_PATH)

        log_stage_end("T022_Merge_Results", status="success")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required file missing: {e}")
        log_stage_end("T022_Merge_Results", status="failed")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}", exc_info=True)
        log_stage_end("T022_Merge_Results", status="failed")
        return 1

def main():
    """CLI entry point."""
    sys.exit(run_experiments())

if __name__ == "__main__":
    main()