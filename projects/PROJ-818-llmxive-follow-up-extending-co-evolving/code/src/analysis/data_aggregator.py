"""
Data aggregation module for collecting batch runner results.

This module implements T030: Collects results from the batch runner output
in data/results/, verifies that the number of runs meets the SC-004 requirement
(N ≥ 30), and prepares the aggregated data for statistical analysis.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import glob

# Minimum number of runs required by SC-004 for statistical power
MIN_RUNS_REQUIRED = 30

@dataclass
class AggregationResult:
    """Container for aggregated data and validation status."""
    success: bool
    total_runs: int
    runs_per_condition: Dict[str, int]
    aggregated_data: List[Dict[str, Any]]
    missing_conditions: List[str]
    insufficient_conditions: List[str]
    error_message: Optional[str] = None

def load_single_result_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a single result file from the batch runner output.
    
    Args:
        file_path: Path to the JSON result file.
        
    Returns:
        Parsed JSON data or None if loading fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Basic validation: ensure it looks like a result
            if 'condition' not in data or 'seed' not in data:
                return None
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {file_path}: {e}", file=sys.stderr)
        return None

def collect_results_from_directory(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Collect all valid result files from the results directory.
    
    Args:
        results_dir: Directory containing batch runner output files.
        
    Returns:
        List of valid result dictionaries.
    """
    results = []
    
    if not results_dir.exists():
        print(f"Warning: Results directory does not exist: {results_dir}", file=sys.stderr)
        return results
    
    # Find all JSON files in the directory (non-recursive for simplicity)
    json_files = list(results_dir.glob("*.json"))
    
    for file_path in json_files:
        data = load_single_result_file(file_path)
        if data is not None:
            # Add source file path for traceability
            data['_source_file'] = str(file_path)
            results.append(data)
    
    return results

def validate_run_counts(
    results: List[Dict[str, Any]], 
    min_runs: int = MIN_RUNS_REQUIRED
) -> Tuple[Dict[str, int], List[str], List[str]]:
    """
    Validate that each condition has sufficient runs.
    
    Args:
        results: List of result dictionaries.
        min_runs: Minimum required runs per condition (SC-004).
        
    Returns:
        Tuple of (counts per condition, missing conditions, insufficient conditions)
    """
    counts: Dict[str, int] = {}
    
    for result in results:
        condition = result.get('condition', 'unknown')
        counts[condition] = counts.get(condition, 0) + 1
    
    expected_conditions = {'sequential', 'mixed', 'coevolving'}
    found_conditions = set(counts.keys())
    
    missing = list(expected_conditions - found_conditions)
    insufficient = [
        cond for cond in found_conditions 
        if counts.get(cond, 0) < min_runs
    ]
    
    return counts, missing, insufficient

def aggregate_batch_results(
    results_dir: Optional[Path] = None,
    min_runs: int = MIN_RUNS_REQUIRED
) -> AggregationResult:
    """
    Main aggregation function for T030.
    
    Collects results from the batch runner, validates against SC-004 requirements,
    and returns aggregated data ready for analysis.
    
    Args:
        results_dir: Directory containing batch results. Defaults to data/results/.
        min_runs: Minimum runs required per condition (SC-004).
        
    Returns:
        AggregationResult with validation status and aggregated data.
    """
    if results_dir is None:
        results_dir = Path("data/results")
    
    # Collect all results
    results = collect_results_from_directory(results_dir)
    
    if not results:
        return AggregationResult(
            success=False,
            total_runs=0,
            runs_per_condition={},
            aggregated_data=[],
            missing_conditions=['sequential', 'mixed', 'coevolving'],
            insufficient_conditions=['sequential', 'mixed', 'coevolving'],
            error_message="No valid result files found in the results directory."
        )
    
    # Validate run counts
    counts, missing, insufficient = validate_run_counts(results, min_runs)
    
    # Determine success
    success = (
        len(missing) == 0 and 
        len(insufficient) == 0 and 
        len(results) >= min_runs
    )
    
    return AggregationResult(
        success=success,
        total_runs=len(results),
        runs_per_condition=counts,
        aggregated_data=results,
        missing_conditions=missing,
        insufficient_conditions=insufficient,
        error_message=None if success else f"Insufficient data: Missing={missing}, Insufficient={insufficient}"
    )

def save_aggregated_results(
    aggregation_result: AggregationResult,
    output_path: Path
) -> bool:
    """
    Save the aggregated results to a JSON file for downstream analysis.
    
    Args:
        aggregation_result: The aggregation result to save.
        output_path: Path to the output file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a summary report
        report = {
            "summary": {
                "total_runs": aggregation_result.total_runs,
                "runs_per_condition": aggregation_result.runs_per_condition,
                "success": aggregation_result.success,
                "sc_004_requirement_met": len(aggregation_result.insufficient_conditions) == 0 and len(aggregation_result.missing_conditions) == 0,
                "min_runs_required": MIN_RUNS_REQUIRED
            },
            "validation": {
                "missing_conditions": aggregation_result.missing_conditions,
                "insufficient_conditions": aggregation_result.insufficient_conditions,
                "error_message": aggregation_result.error_message
            },
            "data": aggregation_result.aggregated_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return True
    except IOError as e:
        print(f"Error saving aggregated results: {e}", file=sys.stderr)
        return False

def main():
    """
    CLI entry point for data aggregation.
    
    Usage: python -m src.analysis.data_aggregator [results_dir]
    """
    results_dir = None
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    
    print(f"Aggregating results from: {results_dir or 'data/results'}")
    print(f"SC-004 Requirement: N ≥ {MIN_RUNS_REQUIRED} runs per condition")
    print("-" * 60)
    
    result = aggregate_batch_results(results_dir)
    
    print(f"Total runs collected: {result.total_runs}")
    print(f"Runs per condition: {result.runs_per_condition}")
    
    if result.missing_conditions:
        print(f"⚠ Missing conditions: {result.missing_conditions}")
    
    if result.insufficient_conditions:
        print(f"⚠ Insufficient runs for: {result.insufficient_conditions}")
    
    if result.success:
        print("✅ SC-004 requirement MET: Sufficient data for statistical analysis.")
        
        # Save aggregated results
        output_path = Path("data/results/aggregated_results.json")
        if save_aggregated_results(result, output_path):
            print(f"✅ Aggregated results saved to: {output_path}")
        else:
            print("⚠ Failed to save aggregated results.")
        
        sys.exit(0)
    else:
        print(f"❌ SC-004 requirement NOT MET: {result.error_message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
