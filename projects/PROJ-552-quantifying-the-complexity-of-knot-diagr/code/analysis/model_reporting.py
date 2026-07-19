"""
Model Reporting Module for Knot Complexity Analysis.

This module handles the generation of markdown and JSON reports for regression models.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.reproducibility.logs import get_logger, log_operation

logger = get_logger(__name__)


@log_operation
def generate_model_summary_markdown(
    models: List[Dict[str, Any]],
    outliers: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate a markdown report summarizing model performance and outliers.

    Args:
        models: List of model result dictionaries.
        outliers: List of outlier entry dictionaries.
        output_path: Path to the output markdown file.
    """
    lines = [
        "# Regression Model Analysis Report",
        "",
        "## Model Summary",
        ""
    ]

    for i, model in enumerate(models, 1):
        lines.append(f"### Model {i}: {model.get('model_type', 'Unknown')}")
        lines.append("")
        lines.append(f"- **Formula**: {model.get('formula', 'N/A')}")
        metrics = model.get('metrics', {})
        lines.append(f"- **R²**: {metrics.get('r_squared', 0):.4f}")
        lines.append(f"- **AIC**: {metrics.get('aic', 0):.2f}")
        lines.append(f"- **BIC**: {metrics.get('bic', 0):.2f}")
        lines.append(f"- **MAE**: {metrics.get('mae', 0):.4f}")
        lines.append(f"- **RMSE**: {metrics.get('rmse', 0):.4f}")
        lines.append(f"- **Variance Explained**: {metrics.get('variance_explained', 0):.4f}")
        lines.append("")

    lines.append("## Outlier Analysis")
    lines.append("")
    lines.append(f"Total outliers identified (≥ 2 SD): **{len(outliers)}**")
    lines.append("")

    if outliers:
        lines.append("| Knot ID | Family | Crossing # | Braid Index | Residual | Std Residual |")
        lines.append("|---|---|---|---|---|---|")
        for o in outliers:
            lines.append(
                f"| {o.get('knot_id', 'N/A')} | {o.get('family', 'N/A')} | "
                f"{o.get('crossing_number', 0):.2f} | {o.get('braid_index', 0):.2f} | "
                f"{o.get('residual', 0):.4f} | {o.get('standardized_residual', 0):.4f} |"
            )
        lines.append("")
    else:
        lines.append("No significant outliers found.")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- Models fitted: Linear, Polynomial (deg=2), Logarithmic.")
    lines.append("- Outliers defined as residuals deviating ≥ 2 standard deviations from the mean.")
    lines.append("- Coefficients are for descriptive variance partitioning only, not independent predictive value (FR-005).")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.log("model_report_generated", parameters={"path": str(output_path), "models": len(models), "outliers": len(outliers)})


@log_operation
def generate_json_report(
    models: List[Dict[str, Any]],
    outliers: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate a JSON report containing all model data and outliers.

    Args:
        models: List of model result dictionaries.
        outliers: List of outlier entry dictionaries.
        output_path: Path to the output JSON file.
    """
    report = {
        "models": models,
        "outliers": outliers,
        "metadata": {
            "generated_by": "model_reporting.py",
            "description": "Regression model analysis and outlier detection"
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.log("json_report_generated", parameters={"path": str(output_path)})


def main() -> None:
    """
    Main entry point for model reporting.
    Loads existing model data and generates reports.
    """
    logger.log("model_reporting_start", parameters={})

    # Example: Load data from previous steps (in real pipeline, these come from model_fitting)
    # For now, we assume empty data if files don't exist to avoid errors in this standalone task
    models_path = Path("data/reports/regression_metrics.json")
    outliers_path = Path("data/reports/residual_outliers.json")

    models = []
    outliers = []

    if models_path.exists():
        with open(models_path, "r") as f:
            models = json.load(f)

    if outliers_path.exists():
        with open(outliers_path, "r") as f:
            outliers = json.load(f)

    # Generate reports
    md_path = Path("docs/reproducibility/regression_analysis_report.md")
    generate_model_summary_markdown(models, outliers, md_path)

    json_path = Path("data/reports/full_model_report.json")
    generate_json_report(models, outliers, json_path)

    logger.log("model_reporting_complete", parameters={})


if __name__ == "__main__":
    main()