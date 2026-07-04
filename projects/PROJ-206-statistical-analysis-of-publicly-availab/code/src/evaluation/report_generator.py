"""
Report generation module for framing statistical findings.

This module implements FR-007: Logic to frame findings as "predictive accuracy"
and "associational uncertainty" in output reports.

It consumes evaluation metrics (RMSE, MAE, coverage) and model outputs to generate
human-readable summaries that correctly distinguish between:
1. Predictive Accuracy: How well the model forecasts the true outcome (point estimate error).
2. Associational Uncertainty: The spread of the posterior distribution or confidence intervals,
   representing the model's internal uncertainty about the relationships.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import get_project_root, get_data_processed_path

logger = get_logger(__name__)


def _format_percentage(value: float) -> str:
    """Format a float as a percentage string."""
    return f"{value * 100:.2f}%"


def _format_number(value: float) -> str:
    """Format a float with 4 decimal places."""
    return f"{value:.4f}"


def generate_predictive_accuracy_summary(
    metrics: Dict[str, Dict[str, float]],
    model_names: Optional[List[str]] = None
) -> str:
    """
    Generate a text summary framing findings as 'predictive accuracy'.

    This function takes evaluation metrics (RMSE, MAE) for different models
    and frames them in the context of how accurately the models predicted
    the actual election outcomes.

    Args:
        metrics: Dictionary mapping model names to their metrics (rmse, mae).
        model_names: Optional list of model names to include. If None, uses all keys.

    Returns:
        A formatted string summarizing predictive accuracy findings.
    """
    if not metrics:
        return "No predictive accuracy metrics available to report."

    if model_names is None:
        model_names = list(metrics.keys())

    lines = [
        "## Predictive Accuracy Analysis",
        "",
        "The following analysis frames the model performance in terms of **predictive accuracy**,"
        " which measures the deviation between the model's point forecasts and the actual election outcomes.",
        ""
    ]

    # Find the best performing model based on RMSE
    best_model = None
    best_rmse = float('inf')

    for model_name in model_names:
        if model_name in metrics and 'rmse' in metrics[model_name]:
            if metrics[model_name]['rmse'] < best_rmse:
                best_rmse = metrics[model_name]['rmse']
                best_model = model_name

    lines.append("### Key Findings on Predictive Accuracy")
    lines.append("")

    if best_model:
        lines.append(
            f"The **{best_model}** model demonstrated the highest predictive accuracy "
            f"with a Root Mean Squared Error (RMSE) of {_format_number(best_rmse)}."
        )
        lines.append("")

    lines.append("### Detailed Metrics by Model")
    lines.append("")
    lines.append("| Model | RMSE (Predictive Error) | MAE (Mean Absolute Error) |")
    lines.append("|-------|-------------------------|---------------------------|")

    for model_name in model_names:
        if model_name in metrics:
            rmse = metrics[model_name].get('rmse', 0.0)
            mae = metrics[model_name].get('mae', 0.0)
            lines.append(
                f"| {model_name} | {_format_number(rmse)} | {_format_number(mae)} |"
            )

    lines.append("")
    lines.append(
        "**Interpretation**: Lower values indicate higher predictive accuracy. "
        "These metrics quantify the average magnitude of forecast errors in percentage points."
    )
    lines.append("")

    return "\n".join(lines)


def generate_associational_uncertainty_summary(
    coverage_results: Dict[str, Any],
    ci_level: float = 0.95
) -> str:
    """
    Generate a text summary framing findings as 'associational uncertainty'.

    This function takes coverage analysis results and frames them in the context
    of the model's internal uncertainty estimates (credible/confidence intervals).

    Args:
        coverage_results: Dictionary containing coverage statistics (coverage_rate,
                         number_of_intervals, successful_covers).
        ci_level: The nominal confidence/credible interval level (default 0.95).

    Returns:
        A formatted string summarizing associational uncertainty findings.
    """
    if not coverage_results:
        return "No associational uncertainty metrics available to report."

    coverage_rate = coverage_results.get('coverage_rate', 0.0)
    total_intervals = coverage_results.get('total_intervals', 0)
    successful_covers = coverage_results.get('successful_covers', 0)

    lines = [
        "## Associational Uncertainty Analysis",
        "",
        "The following analysis frames the model performance in terms of **associational uncertainty**,"
        " which reflects the reliability of the model's internal uncertainty estimates (credible intervals)."
        "",
        "Unlike predictive accuracy (which measures point forecast error), associational uncertainty "
        "assesses whether the model's stated confidence intervals actually contain the true outcome "
        "at the expected rate."
        ""
    ]

    lines.append("### Coverage Reliability")
    lines.append("")

    nominal_rate = _format_percentage(ci_level)
    actual_rate = _format_percentage(coverage_rate)

    lines.append(
        f"For a nominal {nominal_rate} interval, the model achieved an actual coverage rate of "
        f"**{actual_rate}** ({successful_covers} out of {total_intervals} intervals)."
    )
    lines.append("")

    # Assess if the uncertainty is well-calibrated
    tolerance = 0.05  # 5% tolerance for calibration
    if abs(coverage_rate - ci_level) <= tolerance:
        status = "well-calibrated"
        interpretation = (
            "The model's uncertainty estimates are **well-calibrated**. "
            "The frequency of the true outcome falling within the predicted intervals "
            "matches the theoretical expectation."
        )
    elif coverage_rate > ci_level + tolerance:
        status = "conservative"
        interpretation = (
            "The model's uncertainty estimates are **conservative**. "
            "The intervals are wider than necessary, containing the true outcome more often than expected."
        )
    else:
        status = "overconfident"
        interpretation = (
            "The model's uncertainty estimates appear **overconfident**. "
            "The intervals are too narrow, failing to capture the true outcome as often as expected."
        )

    lines.append(f"**Assessment**: The model is **{status}**.")
    lines.append("")
    lines.append(interpretation)
    lines.append("")

    lines.append("### Statistical Reliability")
    lines.append("")
    lines.append(
        "This analysis distinguishes between **predictive accuracy** (how close the point forecast is) "
        "and **associational uncertainty** (how reliable the range of plausible values is). "
        "A model can have high predictive accuracy but poor associational uncertainty (tight but wrong intervals), "
        "or vice versa."
    )
    lines.append("")

    return "\n".join(lines)


def generate_framed_report(
    metrics_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a complete report framing findings as predictive accuracy and associational uncertainty.

    This is the main entry point for FR-007. It loads evaluation results from disk (if available),
    generates the framed summaries, and optionally writes them to a report file.

    Args:
        metrics_path: Path to the metrics CSV or JSON file. If None, attempts to find the default location.
        output_path: Path to write the report. If None, prints to stdout.

    Returns:
        The generated report as a string.
    """
    project_root = get_project_root()
    processed_dir = get_data_processed_path()

    # Default paths if not provided
    if metrics_path is None:
        # Try to find the metrics file
        possible_paths = [
            processed_dir / "evaluation_metrics.csv",
            processed_dir / "model_metrics.csv",
            project_root / "data" / "processed" / "evaluation_metrics.csv"
        ]
        metrics_path = next((p for p in possible_paths if p.exists()), None)

    # Load metrics if file exists
    metrics = {}
    coverage_results = {}

    if metrics_path and os.path.exists(metrics_path):
        try:
            df = pd.read_csv(metrics_path)
            # Assume columns: model_name, rmse, mae, coverage_rate, total_intervals, successful_covers
            for _, row in df.iterrows():
                model_name = row.get('model_name', 'Unknown')
                metrics[model_name] = {
                    'rmse': float(row.get('rmse', 0.0)),
                    'mae': float(row.get('mae', 0.0))
                }
                coverage_results = {
                    'coverage_rate': float(row.get('coverage_rate', 0.0)),
                    'total_intervals': int(row.get('total_intervals', 0)),
                    'successful_covers': int(row.get('successful_covers', 0))
                }
                break  # Take first row if multiple exist
        except Exception as e:
            logger.warning(f"Could not load metrics from {metrics_path}: {e}")
    else:
        logger.warning(f"No metrics file found at {metrics_path}. Generating template report.")

    # Generate framed sections
    accuracy_section = generate_predictive_accuracy_summary(metrics)
    uncertainty_section = generate_associational_uncertainty_summary(coverage_results)

    # Assemble full report
    report = [
        "# Statistical Analysis Report: Framed Findings",
        "",
        "This report presents the results of the election poll aggregation analysis, "
        "framed according to the distinction between **predictive accuracy** and **associational uncertainty** "
        "(FR-007).",
        "",
        "---",
        "",
        accuracy_section,
        "---",
        "",
        uncertainty_section,
        "---",
        "",
        "## Methodology Note",
        "",
        "The analysis separates two distinct aspects of model performance:",
        "",
        "1. **Predictive Accuracy**: Measured by RMSE and MAE, these metrics quantify "
        "the average error of the point forecasts against the actual election results.",
        "",
        "2. **Associational Uncertainty**: Measured by interval coverage rates, these metrics "
        "assess the reliability of the model's uncertainty quantification (credible/confidence intervals).",
        "",
        "This distinction is critical for understanding not just *how well* the model predicts, "
        "but also *how confident* we should be in those predictions."
    ]

    report_text = "\n".join(report)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info(f"Framed report written to {output_path}")

    return report_text


def main():
    """
    Main entry point for the report generator script.
    Generates the framed report and saves it to data/processed/framed_findings_report.md
    """
    logger.info("Starting framed report generation (FR-007)")

    project_root = get_project_root()
    processed_dir = get_data_processed_path()

    output_path = processed_dir / "framed_findings_report.md"

    try:
        report = generate_framed_report(
            metrics_path=None,  # Auto-detect
            output_path=str(output_path)
        )
        logger.info("Framed report generation completed successfully.")
        print(f"Report generated at: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate framed report: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()