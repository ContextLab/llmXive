"""
Generate sensitivity analysis report confirming threshold stability.

This script reads the power results and the sensitivity sweep data generated
by the sensitivity analysis module (T031). It computes the variation in the
identified threshold across the ±10% sweep and writes a formal report to
`data/results/sensitivity_report.txt`.

The report confirms whether the threshold (resolution where power < 0.80)
varies by no more than one resolution step as per the project requirements.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils import get_logger
from sensitivity_analysis import load_power_results, find_inflection_point, get_factor_for_resolution

# Configure logger
logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
POWER_CSV_PATH = RESULTS_DIR / "power_results.csv"
SENSITIVITY_CSV_PATH = RESULTS_DIR / "sensitivity_sweep.csv"
REPORT_PATH = RESULTS_DIR / "sensitivity_report.txt"

# Resolution steps (factors relative to 30m)
VALID_FACTORS = [1, 2, 4, 8, 16]  # 30m, 60m, 120m, 240m, 480m

def factor_to_resolution(factor: int) -> str:
    """Convert aggregation factor to resolution string (e.g., 2 -> '60m')."""
    base = 30
    return f"{base * factor}m"

def get_threshold_for_run(sweep_row: pd.Series) -> Optional[str]:
    """
    Extract the threshold resolution for a specific sensitivity run.
    
    The sweep CSV contains columns like 'threshold_factor_30m', 'threshold_factor_60m', etc.
    We look for the column corresponding to the run's seed or factor and return the threshold.
    """
    # The sweep CSV structure from T031 typically has:
    # 'perturbation_factor', 'threshold_factor', 'threshold_resolution'
    # We need to find the threshold resolution for this specific perturbation.
    
    if 'threshold_resolution' in sweep_row.index:
        return sweep_row['threshold_resolution']
    elif 'threshold_factor' in sweep_row.index:
        factor = int(sweep_row['threshold_factor'])
        return factor_to_resolution(factor)
    return None

def generate_report(power_df: pd.DataFrame, sensitivity_df: pd.DataFrame) -> str:
    """
    Generate the sensitivity analysis report text.
    
    Returns a formatted string containing:
    - Baseline threshold identification
    - Sensitivity sweep results summary
    - Stability confirmation (variation <= 1 step)
    """
    lines = []
    lines.append("=" * 70)
    lines.append("SENSITIVITY ANALYSIS REPORT: THRESHOLD STABILITY")
    lines.append("=" * 70)
    lines.append("")
    
    # 1. Baseline Threshold
    logger.info("Loading baseline power results...")
    if POWER_CSV_PATH.exists():
        baseline_threshold = None
        # Find the first resolution where power < 0.80
        sorted_power = power_df.sort_values(by='factor')
        for _, row in sorted_power.iterrows():
            if row['power'] < 0.80:
                baseline_threshold = row['resolution']
                break
        
        if baseline_threshold:
            lines.append(f"Baseline Threshold (Power < 0.80): {baseline_threshold}")
            lines.append(f"  - Based on: {POWER_CSV_PATH.name}")
        else:
            lines.append("Baseline Threshold: Not found (Power >= 0.80 for all resolutions)")
            baseline_threshold = "N/A"
    else:
        lines.append("ERROR: Power results file not found.")
        baseline_threshold = "N/A"
    
    lines.append("")
    lines.append("-" * 70)
    lines.append("SENSITIVITY SWEEP RESULTS (±10% perturbation)")
    lines.append("-" * 70)
    
    if not sensitivity_df.empty:
        thresholds_found = []
        for _, row in sensitivity_df.iterrows():
            thresh = get_threshold_for_run(row)
            perturbation = row.get('perturbation_factor', row.get('factor', 'unknown'))
            if thresh:
                thresholds_found.append(thresh)
                lines.append(f"  Perturbation {perturbation}: Threshold = {thresh}")
        
        lines.append("")
        if thresholds_found:
            unique_thresholds = list(set(thresholds_found))
            lines.append(f"Unique Thresholds Observed: {', '.join(unique_thresholds)}")
            
            # Check stability: does it vary by more than one step?
            # Map resolutions to their step index (30m=0, 60m=1, etc.)
            resolution_steps = {
                "30m": 0, "60m": 1, "120m": 2, "240m": 3, "480m": 4
            }
            
            if len(unique_thresholds) > 1:
                indices = [resolution_steps.get(t, -1) for t in unique_thresholds if t in resolution_steps]
                if indices and min(indices) != -1 and max(indices) != -1:
                    span = max(indices) - min(indices)
                    lines.append(f"Threshold Variation: {span} step(s)")
                    
                    if span <= 1:
                        lines.append("")
                        lines.append("STABILITY VERDICT: STABLE")
                        lines.append("The threshold varies by no more than one resolution step.")
                        lines.append("Requirement satisfied.")
                    else:
                        lines.append("")
                        lines.append("STABILITY VERDICT: UNSTABLE")
                        lines.append(f"The threshold varies by {span} steps, exceeding the allowed 1 step.")
                        lines.append("Requirement NOT satisfied.")
            else:
                lines.append("")
                lines.append("STABILITY VERDICT: STABLE")
                lines.append("No variation observed across the sensitivity sweep.")
                lines.append("Requirement satisfied.")
        else:
            lines.append("No valid thresholds found in sensitivity sweep.")
    else:
        lines.append("No sensitivity sweep data available.")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)
    
    return "\n".join(lines)

def main():
    """Main entry point for the sensitivity report generation."""
    logger.info("Starting sensitivity analysis report generation...")
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not POWER_CSV_PATH.exists():
        logger.error(f"Power results not found at {POWER_CSV_PATH}.")
        # Create a minimal report indicating failure
        report_content = "ERROR: Power results file not found. Cannot generate report."
        with open(REPORT_PATH, 'w') as f:
            f.write(report_content)
        return
    
    power_df = load_power_results(str(POWER_CSV_PATH))
    
    # Load sensitivity data if it exists, otherwise create a dummy structure for the report
    sensitivity_df = pd.DataFrame()
    if SENSITIVITY_CSV_PATH.exists():
        logger.info(f"Loading sensitivity sweep data from {SENSITIVITY_CSV_PATH}")
        sensitivity_df = pd.read_csv(SENSITIVITY_CSV_PATH)
    else:
        logger.warning(f"Sensitivity sweep file not found at {SENSITIVITY_CSV_PATH}.")
        logger.warning("Generating report with baseline data only (sweep stability cannot be verified).")
    
    # Generate report
    report_content = generate_report(power_df, sensitivity_df)
    
    # Write report
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Sensitivity report written to {REPORT_PATH}")
    print(report_content)

if __name__ == "__main__":
    main()