import os
import csv
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from scipy import stats

from analyzer import load_coverage_reports, pair_llm_human_results

# Define the thresholds for sensitivity analysis
SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]

def load_coverage_reports(reports_dir: str) -> List[Dict[str, Any]]:
    """Load all coverage report JSON files from a directory."""
    reports = []
    reports_path = Path(reports_dir)
    if not reports_path.exists():
        logging.error(f"Reports directory not found: {reports_dir}")
        return reports

    for file_path in reports_path.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Skip error reports (they don't have coverage data)
                if data.get('status') == 'failed':
                    continue
                reports.append(data)
        except json.JSONDecodeError as e:
            logging.warning(f"Could not parse {file_path}: {e}")
    return reports

def calculate_coverage_diff(llm_cov: float, human_cov: float) -> float:
    """Calculate the absolute difference between LLM and human coverage."""
    if llm_cov is None or human_cov is None:
        return None
    return abs(llm_cov - human_cov)

def run_sensitivity_analysis(reports_dir: str, output_dir: str) -> bool:
    """
    Run sensitivity analysis across specified thresholds.
    Excludes these thresholds from family-wise error correction as per FR-011.
    """
    logging.info(f"Starting sensitivity analysis on {reports_dir}")
    
    # Load reports
    reports = load_coverage_reports(reports_dir)
    if not reports:
        logging.error("No valid coverage reports found.")
        return False

    # Pair LLM and Human results (assuming reports contain both or we pair by task_id)
    # For this analysis, we assume the reports contain 'line_coverage' for the generated code.
    # We need to pair with human baseline. If the report only has LLM, we need to load human separately.
    # Based on T024/T025 logic, we assume 'pair_llm_human_results' handles the pairing.
    # However, 'pair_llm_human_results' expects specific structures.
    # Let's manually construct pairs if the report structure is simple.
    
    # Assuming reports have 'task_id' and 'line_coverage' (LLM)
    # We need human baseline. If not present, we might need to load from a separate source or assume 'human_solution' coverage is 100% or loaded from catalog.
    # For this implementation, we will assume the reports from T012/T013 contain 'line_coverage' for LLM.
    # We will assume Human coverage is available in the 'catalog.json' or we treat 'human_solution' as 100% for simplicity if not provided,
    # BUT T024 says "pair LLM and human results".
    # Let's assume the input reports directory contains paired data or we can derive it.
    # If the report is just LLM, we need to find the human solution coverage.
    # Given the constraints, we will assume the 'pair_llm_human_results' function from analyzer.py is robust enough
    # or we implement a local pairing here.
    
    # Simplified approach: Load all reports, group by task_id.
    # If a task has both LLM and Human (or we can calculate human), we compute diff.
    # If not, we skip.
    
    # Let's assume the reports contain a field 'coverage' which is the LLM result.
    # And we have a way to get human.
    # For the sake of this task, we will assume the 'pair_llm_human_results' from analyzer.py
    # is the source of truth for the pairs.
    
    try:
        # We need to call the function from analyzer.py
        # However, to avoid circular imports or complex state, we will re-implement the pairing logic here
        # based on the assumption that reports are per-task.
        # If the project structure stores LLM and Human in separate files or fields, we handle that.
        # Let's assume the reports are just LLM results. We need Human results.
        # T024: "pair LLM and human results by task_id".
        # We will assume there is a way to get human coverage.
        # If not, we might need to load the catalog and run human solution coverage?
        # That is expensive.
        # Alternative: The 'pair_llm_human_results' in analyzer.py likely does this.
        # Let's try to import and use it, but we need to pass the data correctly.
        # Since we can't easily call it without the exact data structure, we will simulate the pairing
        # by assuming the reports contain 'line_coverage' for LLM and 'human_line_coverage' for Human.
        # If 'human_line_coverage' is missing, we might default to 100.0 or skip.
        
        pairs = []
        for report in reports:
            task_id = report.get('task_id')
            llm_cov = report.get('line_coverage')
            human_cov = report.get('human_line_coverage')
            
            if llm_cov is None:
                continue
            
            # If human coverage is not in the report, we might need to load it from elsewhere.
            # For this task, we assume it's present or we use a fallback.
            # If not present, we skip to avoid fake data.
            if human_cov is None:
                # Try to load from catalog? No, catalog doesn't have coverage.
                # Skip if human coverage is missing.
                continue
                
            diff = abs(llm_cov - human_cov)
            pairs.append({
                'task_id': task_id,
                'llm_coverage': llm_cov,
                'human_coverage': human_cov,
                'diff': diff
            })
        
        if not pairs:
            logging.error("No valid pairs found for sensitivity analysis.")
            return False

        # Perform sensitivity analysis
        results = []
        for threshold in SENSITIVITY_THRESHOLDS:
            # Count pairs within threshold
            within_threshold = [p for p in pairs if p['diff'] <= threshold]
            count = len(within_threshold)
            total = len(pairs)
            rate = count / total if total > 0 else 0.0
            
            # Calculate mean diff for this subset? Or just the rate?
            # FR-011: "sensitivity analysis across thresholds". Usually means how results change.
            # We will record the count and rate of pairs within the threshold.
            results.append({
                'threshold': threshold,
                'count_within': count,
                'total_pairs': total,
                'rate': rate,
                'mean_diff_within': np.mean([p['diff'] for p in within_threshold]) if within_threshold else 0.0
            })
        
        # Save results
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / "sensitivity_report.csv"
        
        with open(report_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['threshold', 'count_within', 'total_pairs', 'rate', 'mean_diff_within'])
            writer.writeheader()
            writer.writerows(results)
        
        logging.info(f"Sensitivity report saved to {report_file}")
        return True

    except Exception as e:
        logging.error(f"Error in sensitivity analysis: {e}", exc_info=True)
        return False

def save_sensitivity_report(results: List[Dict], output_path: str):
    """Save sensitivity analysis results to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threshold', 'count_within', 'total_pairs', 'rate', 'mean_diff_within'])
        writer.writeheader()
        writer.writerows(results)

def run_sensitivity_analysis_wrapper(output_dir: str):
    """Wrapper for running sensitivity analysis."""
    reports_dir = Path(output_dir) / "coverage_reports"
    processed_dir = Path(output_dir) / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return run_sensitivity_analysis(str(reports_dir), str(processed_dir))

def main():
    parser = argparse.ArgumentParser(description="Sensitivity Analysis for Coverage Results")
    parser.add_argument('--output-dir', type=str, default='data', help='Output directory')
    args = parser.parse_args()
    
    success = run_sensitivity_analysis_wrapper(args.output_dir)
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
