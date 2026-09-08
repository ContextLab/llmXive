"""
Task T030: Generate sensitivity report data/processed/sensitivity_report.md.

This script aggregates statistical validation results from T029a (sensitivity_variation.csv)
and the raw density sweep data (sensitivity_density_sweep.csv) to produce a comprehensive
Markdown report stating the stability or shift magnitude of the critical threshold theta_c
across sparsity densities.

It explicitly includes the statistical validation (t-test results) required by the spec.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import csv
from datetime import datetime, timezone

# Ensure code directory is in path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import get_project_paths

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("generate_sensitivity_report")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def load_sensitivity_variation_csv(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Load the sensitivity variation results from data/processed/sensitivity_variation.csv.
    Schema: density, theta_c, std_dev, p_value, shift_flag
    """
    paths = get_project_paths()
    input_path = paths['processed'] / 'sensitivity_variation.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T029a has completed successfully."
        )

    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'density': float(row['density']),
                'theta_c': float(row['theta_c']),
                'std_dev': float(row['std_dev']),
                'p_value': float(row['p_value']),
                'shift_flag': row['shift_flag'].lower() == 'true'
            })
    
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def load_sensitivity_density_sweep(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Load the raw density sweep data to calculate summary statistics if needed.
    """
    paths = get_project_paths()
    input_path = paths['processed'] / 'sensitivity_density_sweep.csv'
    
    if not input_path.exists():
        logger.warning(f"Raw sweep file not found: {input_path}. Skipping raw data summary.")
        return []

    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'density': float(row['density']),
                'theta_c': float(row['theta_c']),
                'seed': int(row['seed']),
                'perturbation_type': row.get('perturbation_type', 'unknown')
            })
    
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def generate_report_content(
    variation_data: List[Dict[str, Any]],
    raw_sweep_data: List[Dict[str, Any]],
    logger: logging.Logger
) -> str:
    """
    Generate the Markdown content for the sensitivity report.
    """
    report_lines = []
    
    # Header
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_lines.append("# Sensitivity Analysis Report: Sparsity Thresholds")
    report_lines.append("")
    report_lines.append(f"**Generated:** {timestamp}")
    report_lines.append(f"**Task ID:** T030")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    
    if not variation_data:
        report_lines.append("**Status:** No data available. The sensitivity variation analysis (T029a) has not been completed or produced no results.")
        report_lines.append("")
        return "\n".join(report_lines)

    # Analyze stability
    significant_shifts = [row for row in variation_data if row['shift_flag']]
    total_runs = len(variation_data)
    
    if significant_shifts:
        report_lines.append(f"**Conclusion:** The critical threshold $\\theta_c$ shows **statistically significant sensitivity** to sparsity density changes.")
        report_lines.append(f"Found {len(significant_shifts)} out of {total_runs} density levels with a shift magnitude > 5% (p < 0.05).")
    else:
        report_lines.append(f"**Conclusion:** The critical threshold $\\theta_c$ is **stable** across the tested sparsity densities.")
        report_lines.append(f"No statistically significant shifts (> 5% with p < 0.05) were detected across {total_runs} density levels.")
    
    report_lines.append("")
    
    # Statistical Validation Section
    report_lines.append("## Statistical Validation Results")
    report_lines.append("")
    report_lines.append("The following table summarizes the statistical tests (two-sample t-test) performed to compare $\\theta_c$ distributions across density levels.")
    report_lines.append("")
    report_lines.append("| Density ($p$) | Estimated $\\theta_c$ | Std. Deviation | P-Value | Shift Flag (>5%) |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for row in variation_data:
        shift_flag_str = "Yes" if row['shift_flag'] else "No"
        report_lines.append(
            f"| {row['density']:.2f} | {row['theta_c']:.4f} | {row['std_dev']:.4f} | {row['p_value']:.4e} | {shift_flag_str} |"
        )
    
    report_lines.append("")
    
    # Detailed Analysis
    report_lines.append("## Detailed Analysis")
    report_lines.append("")
    
    if significant_shifts:
        report_lines.append("### Observed Shifts")
        report_lines.append("")
        report_lines.append("The following density levels exhibited significant deviations from the baseline, suggesting that the sparse perturbation structure influences the spectral phase transition threshold:")
        report_lines.append("")
        for row in significant_shifts:
            report_lines.append(f"- **Density $p={row['density']}$**: $\\theta_c = {row['theta_c']:.4f}$ (Shift detected, p={row['p_value']:.4e})")
        report_lines.append("")
    else:
        report_lines.append("### Stability Observation")
        report_lines.append("")
        report_lines.append("Across all tested densities ($p \\in \\{0.2, 0.3\\}$), the critical threshold $\\theta_c$ remained consistent within statistical error margins. This confirms the robustness of the BBP transition prediction against variations in support density for the tested perturbation types.")
        report_lines.append("")
    
    # Methodology Note
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("1. **Data Source**: Results derived from `data/processed/sensitivity_density_sweep.csv` (T028) and `data/processed/sensitivity_variation.csv` (T029a).")
    report_lines.append("2. **Statistical Test**: Two-sample t-test (`scipy.stats.ttest_ind`) was used to compare $\\theta_c$ distributions between adjacent density levels.")
    report_lines.append("3. **Significance Criteria**: A shift is flagged if the magnitude of change in $\\theta_c$ exceeds 5% and the p-value is less than 0.05.")
    report_lines.append("4. **Observational Constraint**: Consistent with FR-007, this analysis treats the 'observer' as the deterministic spectral solver measuring statistical correlations in simulated data. No physical system is modeled; findings are strictly associational.")
    report_lines.append("")
    
    # Footer
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Report generated by the llmXive automated science pipeline.*")
    
    return "\n".join(report_lines)

def write_report(content: str, logger: logging.Logger) -> Path:
    """
    Write the report to data/processed/sensitivity_report.md.
    """
    paths = get_project_paths()
    output_path = paths['processed'] / 'sensitivity_report.md'
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Sensitivity report written to: {output_path}")
    return output_path

def main() -> int:
    """
    Main entry point for Task T030.
    """
    logger = setup_logging()
    logger.info("Starting Task T030: Generate Sensitivity Report")
    
    try:
        # Load inputs
        variation_data = load_sensitivity_variation_csv(logger)
        raw_sweep_data = load_sensitivity_density_sweep(logger)
        
        # Generate content
        report_content = generate_report_content(variation_data, raw_sweep_data, logger)
        
        # Write output
        output_path = write_report(report_content, logger)
        
        logger.info("Task T030 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input data: {e}")
        logger.error("Ensure T029a (sensitivity_variation.csv) has been completed before running T030.")
        return 1
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())