import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_failure_cases(file_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load failure cases and index by task_id for quick lookup."""
    data = load_json_file(file_path)
    if not isinstance(data, list):
        logger.error("Failure cases file must contain a list of objects")
        raise ValueError("Invalid failure cases format")
    
    return {entry['task_id']: entry for entry in data if 'task_id' in entry}

def analyze_baseline_failures(baseline_results_path: Path, failure_cases_path: Path) -> Dict[str, Any]:
    """
    Categorize baseline agent failures by their failure_type.
    
    Args:
        baseline_results_path: Path to baseline_results.json
        failure_cases_path: Path to failure_cases.json
    
    Returns:
        Dictionary containing failure analysis by type
    """
    logger.info("Loading baseline results...")
    baseline_results = load_json_file(baseline_results_path)
    
    logger.info("Loading failure cases...")
    failure_cases = load_failure_cases(failure_cases_path)
    
    # Filter for failed baseline runs
    failed_runs = [run for run in baseline_results if not run.get('success', True)]
    
    logger.info(f"Found {len(failed_runs)} failed baseline runs out of {len(baseline_results)} total")
    
    # Categorize failures by type
    failure_by_type: Dict[str, Dict[str, int]] = {}
    total_failures = len(failed_runs)
    
    for run in failed_runs:
        task_id = run.get('task_id')
        if not task_id:
            logger.warning("Skipping run without task_id")
            continue
        
        # Look up failure type from failure cases
        failure_case = failure_cases.get(task_id)
        if failure_case:
            failure_type = failure_case.get('annotated_structural_feature', 'Unknown')
        else:
            failure_type = 'Unknown'
        
        if failure_type not in failure_by_type:
            failure_by_type[failure_type] = {
                'count': 0,
                'task_ids': []
            }
        
        failure_by_type[failure_type]['count'] += 1
        failure_by_type[failure_type]['task_ids'].append(task_id)
    
    # Calculate failure rates per type
    # Get total count per type from all failure cases (not just failed runs)
    type_totals: Dict[str, int] = {}
    for case in failure_cases.values():
        f_type = case.get('annotated_structural_feature', 'Unknown')
        type_totals[f_type] = type_totals.get(f_type, 0) + 1
    
    # Calculate rates
    analysis_result = {
        'total_baseline_failures': total_failures,
        'breakdown_by_type': {},
        'failure_rates_by_type': {}
    }
    
    for f_type, data in failure_by_type.items():
        count = data['count']
        total_in_type = type_totals.get(f_type, 0)
        rate = count / total_in_type if total_in_type > 0 else 0.0
        
        analysis_result['breakdown_by_type'][f_type] = {
            'failed_count': count,
            'task_ids': data['task_ids']
        }
        analysis_result['failure_rates_by_type'][f_type] = {
            'failed_count': count,
            'total_count': total_in_type,
            'failure_rate': round(rate, 4)
        }
        
        logger.info(f"Failure type '{f_type}': {count} failures / {total_in_type} total = {rate:.2%}")
    
    return analysis_result

def save_analysis_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save the analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Analysis results saved to {output_path}")

def main() -> int:
    """Main entry point for the baseline failure analysis."""
    log_stage_start(logger, "analyze_baseline_failures")
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    baseline_results_path = project_root / "data" / "derived" / "baseline_results.json"
    failure_cases_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "baseline_failure_analysis.json"
    
    # Pre-check: Verify input files exist
    if not baseline_results_path.exists():
        logger.error(f"Baseline results file not found: {baseline_results_path}")
        logger.error("Ensure T021 (run_baseline.py) has completed successfully and produced baseline_results.json")
        return 1
    
    if not failure_cases_path.exists():
        logger.error(f"Failure cases file not found: {failure_cases_path}")
        logger.error("Ensure T011b (annotate_failures.py) has completed successfully and produced failure_cases.json")
        return 1
    
    try:
        # Perform analysis
        results = analyze_baseline_failures(baseline_results_path, failure_cases_path)
        
        # Save results
        save_analysis_results(results, output_path)
        
        log_stage_end(logger, "analyze_baseline_failures", success=True)
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed with error: {str(e)}", exc_info=True)
        log_stage_end(logger, "analyze_baseline_failures", success=False)
        return 1

if __name__ == "__main__":
    sys.exit(main())