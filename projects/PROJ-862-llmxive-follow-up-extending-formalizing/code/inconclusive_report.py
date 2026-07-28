"""
Module: code/inconclusive_report.py

Implements the "No Valid Sigma" reporting logic (Task T051).
Generates a Markdown report if no sigma level yields a validity pass-rate > threshold.
"""
import os
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Constants
DEFAULT_THRESHOLD = 0.10  # 10%
VALIDITY_LOG_PATH = "data/processed/validity_log.csv"
OUTPUT_REPORT_PATH = "data/processed/inconclusive_report.md"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_no_valid_sigma_scenario(
    validity_log_path: str = VALIDITY_LOG_PATH,
    threshold: float = DEFAULT_THRESHOLD
) -> Dict[str, Any]:
    """
    Analyzes the validity_log.csv to determine if ANY sigma level for ANY task type
    exceeds the given validity pass-rate threshold.

    Args:
        validity_log_path: Path to the validity log CSV.
        threshold: Minimum pass-rate required (e.g., 0.10).

    Returns:
        A dictionary with:
            - 'is_inconclusive': bool (True if no valid sigma found)
            - 'max_pass_rate': float (The highest pass-rate observed globally)
            - 'task_results': List[Dict] (Details per task type: max_pass_rate, collapse_point, sigma_range)
    """
    if not os.path.exists(validity_log_path):
        logger.warning(f"Validity log not found at {validity_log_path}. Assuming inconclusive.")
        return {
            'is_inconclusive': True,
            'max_pass_rate': 0.0,
            'task_results': [],
            'reason': 'Validity log file missing'
        }

    task_data: Dict[str, List[float]] = {}
    global_max = 0.0
    rows = []

    try:
        with open(validity_log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                task_type = row.get('task_type')
                sigma_str = row.get('sigma')
                pass_rate_str = row.get('pass_rate')

                if not task_type or sigma_str is None or pass_rate_str is None:
                    continue

                try:
                    sigma = float(sigma_str)
                    pass_rate = float(pass_rate_str)
                except ValueError:
                    continue

                if task_type not in task_data:
                    task_data[task_type] = []
                task_data[task_type].append(pass_rate)
                rows.append(row)

                if pass_rate > global_max:
                    global_max = pass_rate

    except Exception as e:
        logger.error(f"Error reading validity log: {e}")
        return {
            'is_inconclusive': True,
            'max_pass_rate': 0.0,
            'task_results': [],
            'reason': f"Error reading log: {e}"
        }

    if not task_data:
        return {
            'is_inconclusive': True,
            'max_pass_rate': 0.0,
            'task_results': [],
            'reason': 'No data found in validity log'
        }

    # Determine per-task max and collapse point
    task_results = []
    for t_type, rates in task_data.items():
        max_rate = max(rates)
        # Find the sigma associated with the max rate (or first collapse point if all fail)
        # We look for the first row where pass_rate < threshold to identify collapse
        collapse_sigma = None
        for row in rows:
            if row['task_type'] == t_type:
                try:
                    if float(row['pass_rate']) < threshold:
                        collapse_sigma = float(row['sigma'])
                        break
                except ValueError:
                    continue

        task_results.append({
            'task_type': t_type,
            'max_pass_rate': max_rate,
            'collapse_sigma': collapse_sigma,
            'all_rates': rates
        })

    is_inconclusive = global_max <= threshold

    return {
        'is_inconclusive': is_inconclusive,
        'max_pass_rate': global_max,
        'task_results': task_results,
        'threshold': threshold
    }


def generate_inconclusive_report(
    analysis_result: Dict[str, Any],
    output_path: str = OUTPUT_REPORT_PATH
) -> str:
    """
    Generates a Markdown report explaining why the analysis is inconclusive.

    Args:
        analysis_result: The dictionary returned by check_no_valid_sigma_scenario.
        output_path: Path to write the .md file.

    Returns:
        The path to the generated report.
    """
    if not analysis_result['is_inconclusive']:
        logger.info("Analysis is conclusive. No inconclusive report needed.")
        return output_path

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    max_rate = analysis_result['max_pass_rate']
    threshold = analysis_result.get('threshold', DEFAULT_THRESHOLD)
    reason = analysis_result.get('reason', 'No valid sigma found')

    md_content = f"""# Inconclusive Analysis Report: Input Manifold Smoothness Hypothesis

**Generated:** {timestamp}
**Status:** INCONCLUSIVE
**Reason:** {reason}

## Executive Summary

The "Input Manifold Smoothness" hypothesis could not be tested for the provided task types.
The semantic validity of the model's outputs collapsed at noise levels ($\\sigma$) too low to establish a separability baseline.
Specifically, **no** $\\sigma$ level achieved a semantic validity pass-rate greater than **{threshold*100:.1f}%**.

## Key Metrics

| Metric | Value |
| :--- | :--- |
| **Global Max Pass-Rate** | {max_rate*100:.2f}% |
| **Required Threshold** | {threshold*100:.1f}% |
| **Status** | **Failed** (Max < Threshold) |

## Per-Task Breakdown

The following table details the maximum validity pass-rate observed for each task type before semantic collapse occurred.

| Task Type | Max Pass-Rate Observed | Collapse Point ($\\sigma$) |
| :--- | :--- | :--- |
"""

    for task in analysis_result['task_results']:
        t_type = task['task_type']
        t_max = task['max_pass_rate'] * 100
        t_collapse = task['collapse_sigma']
        collapse_str = f"{t_collapse:.4f}" if t_collapse is not None else "N/A"
        md_content += f"| {t_type} | {t_max:.2f}% | {collapse_str} |\n"

    md_content += f"""
## Implications

1.  **No Valid Sigma Found:** The model's output validity is highly sensitive to input perturbations. Even minimal noise ($\\sigma$ approaching 0) caused semantic drift or output invalidity.
2.  **Hypothesis Un-testable:** The statistical analysis for "Latent Separability" requires a range of valid perturbed vectors to compare against the baseline. Since no valid perturbed vectors exist (pass-rate < {threshold*100:.1f}%), the hypothesis test cannot proceed.
3.  **Potential Causes:**
    *   The model may be brittle to input noise.
    *   The chosen threshold ({threshold*100:.1f}%) may be too high for the specific task types.
    *   The noise injection method (nearest token projection) may be too aggressive for the input manifold.

## Recommendations

*   **Lower Threshold:** Consider re-running the analysis with a lower validity threshold (e.g., 5%) if the research question allows for noisy outputs.
*   **Refine Perturbation:** Investigate smoother perturbation methods that preserve token semantics better.
*   **Task Selection:** Focus on task types that demonstrated higher robustness (if any).

## Data Artifacts

This report was generated based on the following data:
*   `data/processed/validity_log.csv`

---
*Generated by llmXive Pipeline (Task T051)*
"""

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    logger.info(f"Inconclusive report generated at: {output_path}")
    return output_path


def main():
    """
    Entry point for the inconclusive report generation.
    Checks the validity log and generates the report if needed.
    """
    logger.info("Starting No Valid Sigma Check (T051)...")

    result = check_no_valid_sigma_scenario(
        validity_log_path=VALIDITY_LOG_PATH,
        threshold=DEFAULT_THRESHOLD
    )

    if result['is_inconclusive']:
        generate_inconclusive_report(result, OUTPUT_REPORT_PATH)
        logger.info("Inconclusive report generated.")
    else:
        logger.info(f"Analysis is conclusive. Max pass-rate: {result['max_pass_rate']*100:.2f}% > {DEFAULT_THRESHOLD*100:.1f}%")

    return result


if __name__ == "__main__":
    main()