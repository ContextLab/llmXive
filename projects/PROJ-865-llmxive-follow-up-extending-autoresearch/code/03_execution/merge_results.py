"""
merge_results.py

Implements T022: Data Merging
Merges CI rule-engine logs (results_rule_engine.csv) with external baseline logs (baseline_results.json)
into a single results.csv, ensuring strict ID matching using the manifest (experiment_manifest.csv).
"""

import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Import logging utilities from the project's utils
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS

logger = get_logger(__name__)

# Paths relative to project root
PATH_MANIFEST = Path("data/derived/experiment_manifest.csv")
PATH_RULE_RESULTS = Path("data/derived/results_rule_engine.csv")
PATH_BASELINE_RESULTS = Path("data/derived/baseline_results.json")
PATH_OUTPUT = Path("data/derived/results.csv")


def load_manifest() -> List[str]:
    """
    Load task IDs from the experiment manifest.
    Returns a list of task IDs in the order they appear.
    """
    if not PATH_MANIFEST.exists():
        raise FileNotFoundError(f"Manifest file not found: {PATH_MANIFEST}")

    task_ids = []
    with open(PATH_MANIFEST, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_ids.append(row['task_id'])
    return task_ids


def load_rule_engine_results() -> Dict[str, Dict[str, Any]]:
    """
    Load rule engine results from CSV.
    Returns a dict: { task_id: { 'time_to_pivot': float, 'success': bool, 'method': str, 'failure_type': str } }
    """
    if not PATH_RULE_RESULTS.exists():
        raise FileNotFoundError(f"Rule engine results file not found: {PATH_RULE_RESULTS}")

    results = {}
    with open(PATH_RULE_RESULTS, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row['task_id']
            results[task_id] = {
                'time_to_pivot': float(row['time_to_pivot']),
                'success': row['success'].lower() == 'true',
                'method': row['method'],
                'failure_type': row['failure_type']
            }
    return results


def load_baseline_results() -> Dict[str, Dict[str, Any]]:
    """
    Load baseline results from JSON.
    Returns a dict: { task_id: { 'time_to_pivot': float, 'success': bool } }
    """
    if not PATH_BASELINE_RESULTS.exists():
        raise FileNotFoundError(f"Baseline results file not found: {PATH_BASELINE_RESULTS}")

    with open(PATH_BASELINE_RESULTS, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list and dict formats for baseline results
    baseline_map = {}
    if isinstance(data, list):
        for entry in data:
            baseline_map[entry['task_id']] = {
                'time_to_pivot': float(entry['time_to_pivot']),
                'success': bool(entry['success'])
            }
    elif isinstance(data, dict):
        # If it's a dict keyed by task_id directly
        for task_id, entry in data.items():
            baseline_map[task_id] = {
                'time_to_pivot': float(entry['time_to_pivot']),
                'success': bool(entry['success'])
            }
    else:
        raise ValueError(f"Unexpected baseline results format: {type(data)}")

    return baseline_map


def merge_results(
    manifest_ids: List[str],
    rule_results: Dict[str, Dict[str, Any]],
    baseline_results: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge results ensuring strict ID matching against the manifest.
    If a baseline task is missing, mark it as 'failed'.
    """
    merged = []
    baseline_ids = set(baseline_results.keys())
    manifest_ids_set = set(manifest_ids)

    # Verify all manifest IDs are present in baseline (unless they failed externally)
    missing_in_baseline = manifest_ids_set - baseline_ids
    if missing_in_baseline:
        logger.warning(f"Baseline results missing {len(missing_in_baseline)} task IDs from manifest: {missing_in_baseline}")

    for task_id in manifest_ids:
        rule_entry = rule_results.get(task_id)
        baseline_entry = baseline_results.get(task_id)

        if rule_entry is None:
            # This should not happen if rule engine ran on the full manifest, but handle gracefully
            logger.error(f"Rule engine results missing for task_id: {task_id}")
            continue

        row = {
            'task_id': task_id,
            'failure_type': rule_entry['failure_type'],
            'rule_engine_time_to_pivot': rule_entry['time_to_pivot'],
            'rule_engine_success': rule_entry['success'],
            'baseline_time_to_pivot': baseline_entry['time_to_pivot'] if baseline_entry else None,
            'baseline_success': baseline_entry['success'] if baseline_entry else False,
            'baseline_status': 'completed' if baseline_entry else 'failed'
        }

        # If baseline is missing, we mark it as failed per spec
        if not baseline_entry:
            row['baseline_time_to_pivot'] = TIMEOUT_SECONDS
            row['baseline_success'] = False
            row['baseline_status'] = 'failed'

        merged.append(row)

    return merged


def write_merged_results(merged_data: List[Dict[str, Any]]) -> None:
    """
    Write the merged results to the output CSV.
    """
    if not merged_data:
        logger.warning("No data to write to merged results.")
        return

    # Ensure output directory exists
    PATH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'task_id',
        'failure_type',
        'rule_engine_time_to_pivot',
        'rule_engine_success',
        'baseline_time_to_pivot',
        'baseline_success',
        'baseline_status'
    ]

    with open(PATH_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in merged_data:
            writer.writerow(row)

    logger.info(f"Merged results written to {PATH_OUTPUT} ({len(merged_data)} rows)")


def main() -> int:
    """
    Main entry point for the merge results task.
    """
    log_stage_start(logger, "merge_results")

    try:
        # Load inputs
        logger.info("Loading manifest...")
        manifest_ids = load_manifest()
        logger.info(f"Loaded {len(manifest_ids)} task IDs from manifest.")

        logger.info("Loading rule engine results...")
        rule_results = load_rule_engine_results()
        logger.info(f"Loaded results for {len(rule_results)} tasks from rule engine.")

        logger.info("Loading baseline results...")
        baseline_results = load_baseline_results()
        logger.info(f"Loaded results for {len(baseline_results)} tasks from baseline.")

        # Validate strict ID matching
        baseline_ids = set(baseline_results.keys())
        manifest_ids_set = set(manifest_ids)

        # The spec says: "Verify that baseline_results.json contains all task IDs from the manifest."
        # If missing, we handle it by marking as failed, but we log a warning.
        missing = manifest_ids_set - baseline_ids
        if missing:
            logger.warning(f"Baseline missing {len(missing)} tasks: {missing}. Marking as failed in output.")

        # Merge
        logger.info("Merging results...")
        merged_data = merge_results(manifest_ids, rule_results, baseline_results)

        # Write output
        logger.info("Writing merged results...")
        write_merged_results(merged_data)

        log_stage_end(logger, "merge_results", status="success")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_stage_end(logger, "merge_results", status="failed")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        log_stage_end(logger, "merge_results", status="failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())