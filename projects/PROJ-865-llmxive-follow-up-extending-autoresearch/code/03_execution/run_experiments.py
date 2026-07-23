import json
import csv
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the experiment manifest CSV."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    tasks = []
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append({
                'task_id': row['task_id'],
                'failure_type': row['failure_type']
            })
    return tasks

def load_rule_engine_results(results_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load rule engine results from CSV into a dictionary keyed by task_id."""
    if not results_path.exists():
        raise FileNotFoundError(f"Rule engine results not found: {results_path}")
    
    results = {}
    with open(results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row['task_id']
            results[task_id] = {
                'task_id': task_id,
                'method': row['method'],
                'time_to_pivot': float(row['time_to_pivot']),
                'success': row['success'].lower() == 'true',
                'failure_type': row['failure_type']
            }
    return results

def load_baseline_results(baseline_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load external baseline results from JSON into a dictionary keyed by task_id."""
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline results not found: {baseline_path}")
    
    with open(baseline_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict format
    if isinstance(data, list):
        results = {}
        for item in data:
            task_id = item['task_id']
            results[task_id] = {
                'task_id': task_id,
                'method': 'baseline',
                'time_to_pivot': float(item['time_to_pivot']),
                'success': bool(item['success']),
                'failure_type': item.get('failure_type', 'Unknown')
            }
        return results
    elif isinstance(data, dict):
        # If it's already keyed by task_id
        results = {}
        for task_id, item in data.items():
            results[task_id] = {
                'task_id': task_id,
                'method': 'baseline',
                'time_to_pivot': float(item['time_to_pivot']),
                'success': bool(item['success']),
                'failure_type': item.get('failure_type', 'Unknown')
            }
        return results
    else:
        raise ValueError(f"Unexpected baseline results format: {type(data)}")

def merge_results(manifest: List[Dict[str, Any]], 
                  rule_results: Dict[str, Dict[str, Any]], 
                  baseline_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge rule-engine logs with external baseline logs using strict ID matching.
    
    Validates that baseline_results contains all task IDs from the manifest.
    Returns a list of merged result dictionaries.
    """
    manifest_task_ids = {t['task_id'] for t in manifest}
    baseline_task_ids = set(baseline_results.keys())
    
    # Validation: Ensure baseline has all manifest IDs
    missing_ids = manifest_task_ids - baseline_task_ids
    if missing_ids:
        raise ValueError(
            f"Baseline results missing task IDs from manifest: {sorted(missing_ids)}"
        )
    
    # Build a lookup for manifest failure types
    manifest_lookup = {t['task_id']: t['failure_type'] for t in manifest}
    
    merged = []
    
    for task_id in manifest_task_ids:
        rule_entry = rule_results.get(task_id)
        baseline_entry = baseline_results.get(task_id)
        
        if not rule_entry:
            logger.warning(f"Rule engine result missing for task_id: {task_id}")
            continue
        
        if not baseline_entry:
            # This should not happen due to validation above, but safety check
            logger.warning(f"Baseline result missing for task_id: {task_id}")
            continue
        
        # Use failure_type from manifest for consistency
        failure_type = manifest_lookup.get(task_id, 'Unknown')
        
        # Append rule engine result
        merged_entry = {
            'task_id': rule_entry['task_id'],
            'method': rule_entry['method'],
            'time_to_pivot': rule_entry['time_to_pivot'],
            'success': str(rule_entry['success']).lower(),
            'failure_type': failure_type
        }
        merged.append(merged_entry)
        
        # Append baseline result
        merged_entry_baseline = {
            'task_id': baseline_entry['task_id'],
            'method': baseline_entry['method'],
            'time_to_pivot': baseline_entry['time_to_pivot'],
            'success': str(baseline_entry['success']).lower(),
            'failure_type': failure_type
        }
        merged.append(merged_entry_baseline)
    
    return merged

def write_merged_results(merged_results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write merged results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_results)
    
    logger.info(f"Wrote {len(merged_results)} merged results to {output_path}")

def run_experiments(manifest_path: Path, 
                    rule_results_path: Path, 
                    baseline_results_path: Path, 
                    output_path: Path) -> None:
    """
    Main orchestration function to merge rule-engine and baseline results.
    """
    log_stage_start(logger, "merge_results")
    
    try:
        # Load inputs
        logger.info(f"Loading manifest from {manifest_path}")
        manifest = load_manifest(manifest_path)
        logger.info(f"Loaded {len(manifest)} tasks from manifest")
        
        logger.info(f"Loading rule engine results from {rule_results_path}")
        rule_results = load_rule_engine_results(rule_results_path)
        logger.info(f"Loaded {len(rule_results)} rule engine results")
        
        logger.info(f"Loading baseline results from {baseline_results_path}")
        baseline_results = load_baseline_results(baseline_results_path)
        logger.info(f"Loaded {len(baseline_results)} baseline results")
        
        # Merge
        logger.info("Merging results with strict ID matching...")
        merged = merge_results(manifest, rule_results, baseline_results)
        logger.info(f"Total merged entries: {len(merged)}")
        
        # Write output
        logger.info(f"Writing merged results to {output_path}")
        write_merged_results(merged, output_path)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        raise
    finally:
        log_stage_end(logger, "merge_results")

def main() -> None:
    """Entry point for script execution."""
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / "data" / "derived" / "experiment_manifest.csv"
    rule_results_path = project_root / "data" / "derived" / "results.csv"
    baseline_results_path = project_root / "data" / "derived" / "baseline_results.json"
    output_path = project_root / "data" / "derived" / "results.csv"
    
    # Allow override via command line arguments
    if len(sys.argv) > 1:
        manifest_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        baseline_results_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
    
    run_experiments(manifest_path, rule_results_path, baseline_results_path, output_path)

if __name__ == "__main__":
    main()