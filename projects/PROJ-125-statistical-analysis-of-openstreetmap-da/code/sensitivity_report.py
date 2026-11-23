"""
Sensitivity Report Generator for GWR Bandwidth Sweep.

This module generates a markdown sensitivity report visualizing the stability
of R² scores across different GWR bandwidths. It reads results from the
bandwidth sweep performed in `modeling.py` and outputs a structured report
to `data/results/sensitivity_report.md`.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

from utils.logging import get_logger
from config import get_path

logger = get_logger(__name__)


def load_bandwidth_sweep_results(results_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the GWR bandwidth sweep results from a JSON file.

    Args:
        results_path: Path to the JSON file containing sweep results.
                      Defaults to 'data/results/gwr_bandwidth_sweep.json'.

    Returns:
        A dictionary containing the sweep results (bandwidths, R² scores, etc.).

    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    if results_path is None:
        results_path = get_path("data/results/gwr_bandwidth_sweep.json")

    if not os.path.exists(results_path):
        raise FileNotFoundError(
            f"Sweep results file not found: {results_path}. "
            "Ensure run_gwr_bandwidth_sweep in modeling.py has been executed."
        )

    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded bandwidth sweep results from {results_path}")
    return data


def calculate_stability_metrics(results: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate stability metrics from the bandwidth sweep results.

    This includes the standard deviation of R², the range (max - min),
    and the coefficient of variation.

    Args:
        results: The dictionary of sweep results.

    Returns:
        A dictionary with calculated stability metrics.
    """
    r2_scores = results.get("r2_scores", [])
    if not r2_scores:
        logger.warning("No R² scores found in results. Returning zero metrics.")
        return {
            "r2_std": 0.0,
            "r2_range": 0.0,
            "r2_cv": 0.0,
            "best_bandwidth": None,
            "best_r2": None,
            "worst_bandwidth": None,
            "worst_r2": None
        }

    r2_array = np.array(r2_scores)
    r2_mean = np.mean(r2_array)
    r2_std = np.std(r2_array)
    r2_range = np.max(r2_array) - np.min(r2_array)
    r2_cv = r2_std / r2_mean if r2_mean != 0 else 0.0

    best_idx = int(np.argmax(r2_array))
    worst_idx = int(np.argmin(r2_array))

    bandwidths = results.get("bandwidths", [])
    best_bandwidth = bandwidths[best_idx] if bandwidths else None
    worst_bandwidth = bandwidths[worst_idx] if bandwidths else None

    return {
        "r2_std": float(r2_std),
        "r2_range": float(r2_range),
        "r2_cv": float(r2_cv),
        "best_bandwidth": best_bandwidth,
        "best_r2": float(r2_array[best_idx]),
        "worst_bandwidth": worst_bandwidth,
        "worst_r2": float(r2_array[worst_idx])
    }


def generate_report_content(
    results: Dict[str, Any],
    stability_metrics: Dict[str, float]
) -> str:
    """
    Generate the markdown content for the sensitivity report.

    Args:
        results: The raw sweep results.
        stability_metrics: The calculated stability metrics.

    Returns:
        A markdown string representing the report.
    """
    timestamp = results.get("timestamp", "N/A")
    city = results.get("city", "Unknown")
    model_type = results.get("model_type", "GWR")
    bandwidths = results.get("bandwidths", [])
    r2_scores = results.get("r2_scores", [])
    aic_scores = results.get("aic_scores", [])

    # Header
    report_lines = [
        f"# GWR Bandwidth Sensitivity Report",
        f"",
        f"**Generated**: {timestamp}",
        f"**City**: {city}",
        f"**Model**: {model_type}",
        f"",
        f"## Summary",
        f"",
        f"This report analyzes the stability of the Geographically Weighted Regression (GWR) model",
        f"performance across different bandwidth configurations. The bandwidth parameter controls",
        f"the spatial extent of the local regression, influencing the trade-off between bias and variance.",
        f"",
        f"### Key Stability Metrics",
        f"",
        f"| Metric | Value |",
        f"| :--- | :--- |",
        f"| **R² Standard Deviation** | {stability_metrics['r2_std']:.4f} |",
        f"| **R² Range (Max - Min)** | {stability_metrics['r2_range']:.4f} |",
        f"| **Coefficient of Variation** | {stability_metrics['r2_cv']:.4f} |",
        f"| **Best Bandwidth** | {stability_metrics['best_bandwidth']} |",
        f"| **Best R²** | {stability_metrics['best_r2']:.4f} |",
        f"| **Worst Bandwidth** | {stability_metrics['worst_bandwidth']} |",
        f"| **Worst R²** | {stability_metrics['worst_r2']:.4f} |",
        f"",
        f"## Interpretation",
        f"",
    ]

    # Interpretation logic
    if stability_metrics['r2_cv'] < 0.05:
        interpretation = (
            f"The model performance is **highly stable** across the tested bandwidths. "
            f"The low coefficient of variation ({stability_metrics['r2_cv']:.4f}) suggests that "
            f"the choice of bandwidth within this range has a minimal impact on the predictive power (R²). "
            f"The optimal bandwidth can be selected based on other criteria (e.g., AIC, computational cost)."
        )
    elif stability_metrics['r2_cv'] < 0.15:
        interpretation = (
            f"The model performance shows **moderate stability**. "
            f"There is some variation in R² ({stability_metrics['r2_cv']:.4f}), indicating that bandwidth selection "
            f"does influence model fit, but the model is not extremely sensitive to small changes."
        )
    else:
        interpretation = (
            f"The model performance is **unstable** across the tested bandwidths. "
            f"The high coefficient of variation ({stability_metrics['r2_cv']:.4f}) suggests that "
            f"the model fit is highly sensitive to the bandwidth parameter. "
            f"Careful selection of the bandwidth is critical, and the range of tested values might need to be expanded."
        )

    report_lines.append(interpretation)
    report_lines.append("")
    report_lines.append("## Detailed Results")
    report_lines.append("")
    report_lines.append("| Bandwidth | R² Score | AIC Score |")
    report_lines.append("| :--- | :--- | :--- |")

    for bw, r2, aic in zip(bandwidths, r2_scores, aic_scores):
        report_lines.append(f"| {bw} | {r2:.4f} | {aic:.4f} |")

    report_lines.append("")
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append(
        f"The GWR model was fitted using a bandwidth sweep approach. "
        f"A series of bandwidth values were tested, and for each value, the model was trained "
        f"and evaluated. The R² score and AIC (Akaike Information Criterion) were recorded. "
        f"The stability of the R² score was then analyzed to determine the robustness of the model "
        f"to bandwidth selection."
    )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Generated by llmXive Sensitivity Report Generator*")

    return "\n".join(report_lines)


def main():
    """
    Main entry point to generate the sensitivity report.

    1. Loads bandwidth sweep results from `data/results/gwr_bandwidth_sweep.json`.
    2. Calculates stability metrics.
    3. Generates the markdown report content.
    4. Writes the report to `data/results/sensitivity_report.md`.
    """
    logger.info("Starting sensitivity report generation...")

    try:
        # 1. Load Results
        results = load_bandwidth_sweep_results()

        # 2. Calculate Metrics
        stability_metrics = calculate_stability_metrics(results)

        # 3. Generate Content
        report_content = generate_report_content(results, stability_metrics)

        # 4. Write Output
        output_path = get_path("data/results/sensitivity_report.md")
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Sensitivity report successfully written to {output_path}")
        print(f"Report generated: {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise


if __name__ == "__main__":
    main()