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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_coverage_reports(reports_dir: str = "data/coverage_reports") -> List[Dict[str, Any]]:
    """Load all coverage report JSON files from the specified directory."""
    reports_path = Path(reports_dir)
    if not reports_path.exists():
        logger.warning(f"Reports directory {reports_dir} does not exist.")
        return []
    
    reports = []
    for json_file in reports_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Filter out failed tasks if they don't have coverage data
                if data.get('status') != 'failed' and 'line_coverage' in data:
                    reports.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading {json_file}: {e}")
    return reports

def pair_llm_human_results(reports: List[Dict[str, Any]]) -> List[Tuple[Dict, Dict]]:
    """
    Pair LLM and Human coverage results by task_id.
    Assumes human solution coverage is stored with the same task_id but potentially
    different source or marked as 'human'.
    For this analysis, we assume the 'human' coverage is already present in the reports
    (e.g., from the canonical solution execution).
    """
    # Group by task_id
    by_task = {}
    for r in reports:
        tid = r.get('task_id')
        if tid:
            if tid not in by_task:
                by_task[tid] = {'llm': None, 'human': None}
            
            # Determine if this is LLM or Human based on metadata or filename convention
            # If the report contains 'source' or 'model' it's likely LLM.
            # If it's the canonical solution, it might be marked differently.
            # For robustness, we'll assume:
            # - If 'model' key exists or 'generated' is True -> LLM
            # - Otherwise -> Human (assuming we ran canonical solutions separately)
            if r.get('model') or r.get('is_generated', False):
                by_task[tid]['llm'] = r
            else:
                by_task[tid]['human'] = r

    pairs = []
    for tid, data in by_task.items():
        if data['llm'] and data['human']:
            pairs.append((data['llm'], data['human']))
        elif data['llm']:
            # If no human solution found, we might need to handle this
            # For now, skip if no pair exists to avoid NaNs in stats
            logger.warning(f"No human solution found for {tid}, skipping pair.")
    return pairs

def run_sensitivity_analysis(pairs: List[Tuple[Dict, Any]], thresholds: List[float] = None) -> pd.DataFrame:
    """
    Perform sensitivity analysis across specified significance thresholds.
    FR-011: Explicitly exclude these thresholds from family-wise error correction.
    
    Calculates the proportion of significant results at each threshold.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25]
    
    if not pairs:
        logger.error("No valid pairs found for sensitivity analysis.")
        return pd.DataFrame()

    # Extract coverage differences (Human - LLM)
    # We use line_coverage for this analysis as it's available for all tasks
    # Branch coverage might be N/A for HumanEval
    diffs = []
    for llm_r, human_r in pairs:
        # Prefer line_coverage if branch is N/A or missing
        llm_cov = llm_r.get('line_coverage', 0.0)
        human_cov = human_r.get('line_coverage', 0.0)
        
        # Handle potential string "N/A" or None
        if isinstance(llm_cov, str) and llm_cov.upper() == "N/A":
            llm_cov = 0.0
        if isinstance(human_cov, str) and human_cov.upper() == "N/A":
            human_cov = 0.0
        
        diffs.append(human_cov - llm_cov)
    
    diffs = np.array(diffs)
    
    if len(diffs) == 0:
        return pd.DataFrame()

    # Perform a paired t-test to get a baseline p-value distribution
    # Since we are doing sensitivity analysis, we treat the differences as a sample
    # and check significance against 0 at various alpha levels.
    # However, sensitivity analysis usually implies: "How many hypotheses are significant at alpha X?"
    # Here, we have one aggregate test. We can simulate the sensitivity by checking
    # the p-value of the mean difference against each threshold.
    
    # Calculate mean and standard error
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    n = len(diffs)
    
    if std_diff == 0:
        t_stat = 0.0 if mean_diff == 0 else float('inf')
    else:
        t_stat = mean_diff / (std_diff / np.sqrt(n))
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
    
    results = []
    for alpha in thresholds:
        is_significant = p_value < alpha
        results.append({
            'threshold': alpha,
            'p_value': p_value,
            'is_significant': is_significant,
            'mean_difference': mean_diff,
            'sample_size': n,
            't_statistic': t_stat,
            # FR-011 Constraint: Note that these are NOT corrected for FWE
            'fwe_corrected': False 
        })
    
    return pd.DataFrame(results)

def save_sensitivity_report(df: pd.DataFrame, output_path: str = "data/processed/sensitivity_report.csv"):
    """Save the sensitivity analysis report to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if df.empty:
        logger.warning("Empty dataframe, writing empty CSV with headers.")
        df.to_csv(output_file, index=False)
    else:
        df.to_csv(output_file, index=False)
        logger.info(f"Sensitivity report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on coverage data.")
    parser.add_argument(
        "--reports-dir", 
        type=str, 
        default="data/coverage_reports",
        help="Directory containing coverage report JSON files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/sensitivity_report.csv",
        help="Output path for the sensitivity report CSV."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="0.01,0.05,0.10,0.15,0.20,0.25",
        help="Comma-separated list of significance thresholds to test."
    )
    
    args = parser.parse_args()
    
    logger.info(f"Loading coverage reports from {args.reports_dir}")
    reports = load_coverage_reports(args.reports_dir)
    logger.info(f"Loaded {len(reports)} reports.")
    
    logger.info("Pairing LLM and Human results...")
    pairs = pair_llm_human_results(reports)
    logger.info(f"Found {len(pairs)} valid pairs.")
    
    thresholds = [float(x.strip()) for x in args.thresholds.split(",")]
    
    logger.info(f"Running sensitivity analysis for thresholds: {thresholds}")
    df = run_sensitivity_analysis(pairs, thresholds)
    
    if not df.empty:
        logger.info(f"Analysis complete. Mean difference: {df['mean_difference'].iloc[0]:.4f}")
        logger.info(f"P-value: {df['p_value'].iloc[0]:.6f}")
    
    save_sensitivity_report(df, args.output)
    
    return 0 if not df.empty else 1

if __name__ == "__main__":
    exit(main())
