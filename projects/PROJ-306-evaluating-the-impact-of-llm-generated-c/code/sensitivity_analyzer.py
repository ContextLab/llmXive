import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_coverage_reports(coverage_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON coverage reports from the specified directory."""
    reports = []
    coverage_path = Path(coverage_dir)
    if not coverage_path.exists():
        logger.warning(f"Coverage directory not found: {coverage_dir}")
        return reports
    
    for json_file in coverage_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Skip failed reports if they lack coverage data
                if data.get('status') == 'failed' or 'line_coverage' not in data:
                    continue
                reports.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading {json_file}: {e}")
    return reports

def pair_llm_human_results(reports: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Pair LLM and human results by task_id.
    Assumes reports contain 'task_id', 'line_coverage' (or branch_coverage).
    Human solution coverage is assumed to be 1.0 (100%) or extracted if available.
    For this implementation, we treat 'human_solution' coverage as 1.0 if not explicitly reported in a separate human run.
    However, to be robust, we look for a 'source' or 'type' field if available, otherwise assume:
    - If the report is from the LLM generation pipeline, we need a corresponding human baseline.
    - In this specific project context (T029), we assume the 'coverage_reports' contain both LLM generated and Human baseline runs,
      or we derive human baseline as 1.0 for valid tasks if not present.
    
    For the purpose of T029 sensitivity analysis, we calculate the difference:
    diff = human_coverage - llm_coverage.
    If human coverage is not explicitly in the report, we assume 1.0 (perfect coverage for reference solution).
    """
    data = []
    for report in reports:
        task_id = report.get('task_id')
        if not task_id:
            continue
        
        # Assume human coverage is 1.0 if not explicitly provided as a separate "human" run in the same report
        # In many setups, the 'human_solution' is the reference, so coverage is 100%.
        # If the report has a specific field for 'human_coverage', use it.
        human_cov = report.get('human_coverage', 1.0)
        llm_cov = report.get('line_coverage')
        
        if llm_cov is None:
            continue
        
        data.append({
            'task_id': task_id,
            'human_coverage': float(human_cov),
            'llm_coverage': float(llm_cov),
            'diff': float(human_cov) - float(llm_cov)
        })
    
    return pd.DataFrame(data)

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: List[float]) -> pd.DataFrame:
    """
    Perform sensitivity analysis across specified thresholds.
    Calculate the proportion of tasks where the coverage gap exceeds each threshold.
    Constraint: Explicitly exclude these thresholds from family-wise error correction (handled by caller if needed).
    """
    results = []
    
    if df.empty:
        logger.warning("No data to perform sensitivity analysis on.")
        return pd.DataFrame(columns=['threshold', 'proportion_exceeding', 'count_exceeding', 'total_count'])

    total_count = len(df)
    
    for threshold in thresholds:
        # Count tasks where the absolute difference (or just difference) exceeds the threshold
        # Usually sensitivity is about how many results change significance or magnitude.
        # Here, we interpret it as: how many tasks have a gap > threshold?
        count_exceeding = (df['diff'] > threshold).sum()
        proportion = count_exceeding / total_count if total_count > 0 else 0.0
        
        results.append({
            'threshold': threshold,
            'proportion_exceeding': proportion,
            'count_exceeding': int(count_exceeding),
            'total_count': total_count
        })
    
    return pd.DataFrame(results)

def save_sensitivity_report(report_df: pd.DataFrame, output_path: str):
    """Save the sensitivity analysis report to a CSV file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_file, index=False)
    logger.info(f"Sensitivity report saved to {output_file}")

def main():
    """Main entry point for running sensitivity analysis."""
    # Default paths
    coverage_dir = "data/coverage_reports"
    output_dir = "data/processed"
    output_file = os.path.join(output_dir, "sensitivity_report.csv")
    
    # Parse arguments if needed, for now use defaults or check environment
    import argparse
    parser = argparse.ArgumentParser(description="Run Sensitivity Analysis")
    parser.add_argument("--coverage-dir", type=str, default=coverage_dir, help="Directory containing coverage reports")
    parser.add_argument("--output-file", type=str, default=output_file, help="Output CSV file path")
    args = parser.parse_args()
    
    logger.info(f"Loading coverage reports from {args.coverage_dir}")
    reports = load_coverage_reports(args.coverage_dir)
    
    if not reports:
        logger.error("No valid coverage reports found. Cannot run sensitivity analysis.")
        return
    
    logger.info(f"Loaded {len(reports)} reports.")
    
    df = pair_llm_human_results(reports)
    
    if df.empty:
        logger.error("No valid paired data found.")
        return
    
    # Define thresholds as per task T029: {0.01, 0.05, 0.10, 0.15, 0.20, 0.25}
    thresholds = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]
    
    logger.info(f"Running sensitivity analysis for thresholds: {thresholds}")
    sensitivity_df = run_sensitivity_analysis(df, thresholds)
    
    save_sensitivity_report(sensitivity_df, args.output_file)
    logger.info("Sensitivity analysis completed successfully.")

if __name__ == "__main__":
    main()
