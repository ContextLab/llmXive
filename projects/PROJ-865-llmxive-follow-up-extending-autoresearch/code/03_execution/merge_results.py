import json
import csv
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS

logger = get_logger(__name__)

# Censored sentinel value for time_to_pivot when baseline fails/times out
CENSORED_SENTINEL = float(TIMEOUT_SECONDS)

def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Load the experiment manifest CSV."""
    logger.info(f"Loading experiment manifest from {manifest_path}")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    manifest = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            manifest.append(row)
    
    if not manifest:
        raise ValueError("Manifest file is empty.")
    
    logger.info(f"Loaded {len(manifest)} task IDs from manifest.")
    return manifest

def load_rule_engine_results(results_path: str) -> Dict[str, Dict[str, Any]]:
    """Load rule engine results from CSV, keyed by task_id."""
    logger.info(f"Loading rule engine results from {results_path}")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Rule engine results file not found: {results_path}")

    results = {}
    with open(results_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            if task_id:
                results[task_id] = {
                    'method': row.get('method', 'rule_engine'),
                    'time_to_pivot': float(row.get('time_to_pivot', 0)),
                    'success': row.get('success', '').lower() == 'true',
                    'failure_type': row.get('failure_type', 'Unknown')
                }
    logger.info(f"Loaded {len(results)} rule engine results.")
    return results

def load_baseline_results(results_path: str) -> Dict[str, Dict[str, Any]]:
    """Load baseline results from JSON, keyed by task_id."""
    logger.info(f"Loading baseline results from {results_path}")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Baseline results file not found: {results_path}")

    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = {}
    # Handle list of dicts or dict of dicts
    entries = data if isinstance(data, list) else data.get('results', [])
    
    for entry in entries:
        task_id = entry.get('task_id')
        if task_id:
            # Determine success and time_to_pivot
            success = entry.get('success', False)
            time_to_pivot = entry.get('time_to_pivot')
            
            # If time_to_pivot is missing or null, treat as censored (failed/timeout)
            if time_to_pivot is None or time_to_pivot == '':
                time_to_pivot = CENSORED_SENTINEL
                success = False
            else:
                time_to_pivot = float(time_to_pivot)

            results[task_id] = {
                'method': 'baseline',
                'time_to_pivot': time_to_pivot,
                'success': success,
                'failure_type': entry.get('failure_type', 'Unknown')
            }
    
    logger.info(f"Loaded {len(results)} baseline results.")
    return results

def merge_results(
    manifest: List[Dict[str, Any]],
    rule_engine_results: Dict[str, Dict[str, Any]],
    baseline_results: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge rule engine and baseline results based on the manifest.
    Ensures strict ID matching. If a baseline result is missing, mark as failed/censored.
    """
    merged = []
    manifest_ids = {row['task_id'] for row in manifest}
    baseline_ids = set(baseline_results.keys())
    
    # Validation: Check for missing baseline IDs
    missing_baseline_ids = manifest_ids - baseline_ids
    if missing_baseline_ids:
        logger.warning(f"Missing baseline results for {len(missing_baseline_ids)} tasks: {missing_baseline_ids}")
        logger.warning("These will be marked as 'failed' with censored time_to_pivot.")

    for row in manifest:
        task_id = row['task_id']
        
        # Get rule engine result (should exist for all manifest items if pipeline ran correctly)
        re_result = rule_engine_results.get(task_id)
        if not re_result:
            logger.error(f"Missing rule engine result for task {task_id}. Skipping.")
            continue

        # Get baseline result
        base_result = baseline_results.get(task_id)
        
        # If baseline result is missing, create a censored entry
        if not base_result:
            base_result = {
                'method': 'baseline',
                'time_to_pivot': CENSORED_SENTINEL,
                'success': False,
                'failure_type': row.get('failure_type', 'Unknown')
            }

        merged_row = {
            'task_id': task_id,
            'rule_engine_time_to_pivot': re_result['time_to_pivot'],
            'rule_engine_success': re_result['success'],
            'baseline_time_to_pivot': base_result['time_to_pivot'],
            'baseline_success': base_result['success'],
            'failure_type': re_result.get('failure_type', row.get('failure_type', 'Unknown'))
        }
        merged.append(merged_row)

    logger.info(f"Merged {len(merged)} paired results.")
    return merged

def write_merged_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write merged results to CSV."""
    logger.info(f"Writing merged results to {output_path}")
    
    if not results:
        logger.warning("No results to write.")
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        'task_id', 
        'rule_engine_time_to_pivot', 
        'rule_engine_success', 
        'baseline_time_to_pivot', 
        'baseline_success', 
        'failure_type'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Ensure boolean values are written as strings 'True'/'False' for CSV compatibility
            row_copy = row.copy()
            row_copy['rule_engine_success'] = str(row_copy['rule_engine_success'])
            row_copy['baseline_success'] = str(row_copy['baseline_success'])
            writer.writerow(row_copy)

    logger.info(f"Successfully wrote {len(results)} rows to {output_path}")

def main():
    """Main entry point for merging results."""
    log_stage_start(logger, "merge_results")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    rule_engine_path = project_root / "data" / "derived" / "results_rule_engine.csv"
    baseline_path = project_root / "data" / "derived" / "baseline_results.json"
    output_path = project_root / "data" / "derived" / "results.csv"

    try:
        # 1. Load Manifest
        manifest = load_manifest(str(manifest_path))
        
        # 2. Load Rule Engine Results
        rule_engine_results = load_rule_engine_results(str(rule_engine_path))
        
        # 3. Load Baseline Results
        baseline_results = load_baseline_results(str(baseline_path))
        
        # 4. Merge
        merged = merge_results(manifest, rule_engine_results, baseline_results)
        
        # 5. Write Output
        write_merged_results(merged, str(output_path))
        
        logger.info("Merge completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}", exc_info=True)
        return 1
    finally:
        log_stage_end(logger, "merge_results")

if __name__ == "__main__":
    sys.exit(main())