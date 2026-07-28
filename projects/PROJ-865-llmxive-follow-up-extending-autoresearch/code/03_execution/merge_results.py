import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

# Constants
MISSING_BASELINE_SENTINEL = -1.0
FAILED_SUCCESS_FLAG = False

def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Load the experiment manifest CSV."""
    logger.info(f"Loading manifest from {manifest_path}")
    manifest = []
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            manifest.append(row)
    logger.info(f"Loaded {len(manifest)} task IDs from manifest")
    return manifest

def load_rule_engine_results(results_path: str) -> Dict[str, Dict[str, Any]]:
    """Load rule engine results from CSV into a dictionary keyed by task_id."""
    logger.info(f"Loading rule engine results from {results_path}")
    results = {}
    with open(results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            if task_id:
                # Convert time_to_pivot to float, handle potential parsing errors
                try:
                    ttp = float(row.get('time_to_pivot', 0))
                except ValueError:
                    ttp = 0.0
                
                success = row.get('success', '').lower() == 'true'
                results[task_id] = {
                    'time_to_pivot': ttp,
                    'success': success,
                    'failure_type': row.get('failure_type', 'Unknown')
                }
    logger.info(f"Loaded {len(results)} rule engine results")
    return results

def load_baseline_results(results_path: str) -> Dict[str, Dict[str, Any]]:
    """Load baseline results from JSON into a dictionary keyed by task_id."""
    logger.info(f"Loading baseline results from {results_path}")
    results = {}
    if not Path(results_path).exists():
        logger.warning(f"Baseline results file not found at {results_path}")
        return results

    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list of objects and single object formats
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # If it's a single object, wrap it in a list or check if it contains a list key
        if 'results' in data and isinstance(data['results'], list):
            items = data['results']
        else:
            items = [data]
    else:
        logger.error("Unexpected format in baseline results JSON")
        return results

    for item in items:
        task_id = item.get('task_id')
        if task_id:
            # Handle missing or failed tasks
            ttp = item.get('time_to_pivot')
            if ttp is None:
                # If the task failed to run or timed out, use sentinel
                ttp = MISSING_BASELINE_SENTINEL
            else:
                try:
                    ttp = float(ttp)
                except (ValueError, TypeError):
                    ttp = MISSING_BASELINE_SENTINEL

            success = item.get('success', False)
            if ttp == MISSING_BASELINE_SENTINEL:
                success = False

            results[task_id] = {
                'time_to_pivot': ttp,
                'success': success,
                'failure_type': item.get('failure_type', 'Unknown')
            }
    
    logger.info(f"Loaded {len(results)} baseline results")
    return results

def merge_results(manifest: List[Dict[str, Any]], 
                  rule_results: Dict[str, Dict[str, Any]], 
                  baseline_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge rule engine and baseline results based on the manifest."""
    merged = []
    manifest_ids = set()
    baseline_ids = set(baseline_results.keys())
    rule_ids = set(rule_results.keys())

    missing_from_baseline = []
    missing_from_rule = []

    for entry in manifest:
        task_id = entry.get('task_id')
        if not task_id:
            continue

        manifest_ids.add(task_id)
        
        # Get rule engine data
        rule_data = rule_results.get(task_id, {})
        rule_ttp = rule_data.get('time_to_pivot', 0.0)
        rule_success = rule_data.get('success', False)
        rule_ft = rule_data.get('failure_type', entry.get('failure_type', 'Unknown'))

        # Get baseline data
        baseline_data = baseline_results.get(task_id)
        if baseline_data is None:
            # Task failed in baseline execution or was not run
            baseline_ttp = MISSING_BASELINE_SENTINEL
            baseline_success = FAILED_SUCCESS_FLAG
            missing_from_baseline.append(task_id)
            logger.warning(f"Baseline result missing for task {task_id}. Marking as failed.")
        else:
            baseline_ttp = baseline_data.get('time_to_pivot', MISSING_BASELINE_SENTINEL)
            baseline_success = baseline_data.get('success', False)
            if baseline_ttp == MISSING_BASELINE_SENTINEL:
                baseline_success = False

        merged_row = {
            'task_id': task_id,
            'method_rule_ttp': rule_ttp,
            'method_rule_success': str(rule_success).lower(),
            'method_rule_failure_type': rule_ft,
            'method_baseline_ttp': baseline_ttp,
            'method_baseline_success': str(baseline_success).lower(),
            'method_baseline_failure_type': baseline_data.get('failure_type', entry.get('failure_type', 'Unknown')) if baseline_data else entry.get('failure_type', 'Unknown')
        }
        merged.append(merged_row)

    # Validation
    if missing_from_baseline:
        logger.warning(f"Found {len(missing_from_baseline)} tasks missing from baseline results: {missing_from_baseline[:5]}...")
    
    if not baseline_ids.issuperset(manifest_ids):
        missing = manifest_ids - baseline_ids
        logger.warning(f"Baseline results do not contain all manifest IDs. Missing: {len(missing)}")

    return merged

def write_merged_results(merged_data: List[Dict[str, Any]], output_path: str) -> None:
    """Write merged results to CSV."""
    logger.info(f"Writing merged results to {output_path}")
    if not merged_data:
        logger.error("No data to write.")
        return

    fieldnames = list(merged_data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)
    
    logger.info(f"Successfully wrote {len(merged_data)} rows to {output_path}")

def main():
    """Main entry point for merging results."""
    log_stage_start(logger, "merge_results")
    
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    manifest_path = project_root / 'data' / 'derived' / 'experiment_manifest.csv'
    rule_results_path = project_root / 'data' / 'derived' / 'results_rule_engine.csv'
    baseline_results_path = project_root / 'data' / 'derived' / 'baseline_results.json'
    output_path = project_root / 'data' / 'derived' / 'results.csv'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Manifest
        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}. Ensure T019a has completed.")
            sys.exit(1)
        manifest = load_manifest(str(manifest_path))
        if not manifest:
            logger.error("Manifest is empty.")
            sys.exit(1)

        # 2. Load Rule Engine Results
        if not rule_results_path.exists():
            logger.error(f"Rule engine results not found: {rule_results_path}. Ensure T019 has completed.")
            sys.exit(1)
        rule_results = load_rule_engine_results(str(rule_results_path))

        # 3. Load Baseline Results
        # Note: T021 might produce this file. If it doesn't exist, we treat it as all failures.
        baseline_results = load_baseline_results(str(baseline_results_path))

        # 4. Merge
        merged_data = merge_results(manifest, rule_results, baseline_results)

        # 5. Write Output
        write_merged_results(merged_data, str(output_path))

        logger.info("Merge results completed successfully.")
        log_stage_end(logger, "merge_results")

    except Exception as e:
        logger.error(f"Error during merge: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()