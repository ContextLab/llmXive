"""
Report Generator for HEA Yield Strength Prediction Project
---------------------------------------------------------

This script assembles the final markdown report (`output/report.md`) by
loading the various JSON artifacts produced by earlier pipeline stages,
formatting them into human‑readable sections, and injecting the mandatory
disclaimer.

The required sections are:

1. Overview
2. Model Performance (metrics for Linear Regression, Random Forest,
   Gradient Boosting and the best model)
3. Statistical Validation (VIF, Permutation Importance, Bootstrap CI)
4. Sensitivity Analysis
5. Data Limitation Warning (conditionally included)
6. Conclusion

The disclaimer *“Associational analysis only; no causal inference”* is
appended using the utilities in ``utils.report_utils``.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from utils.logging import get_logger
from utils.report_utils import inject_disclaimer, finalize_report_markdown

LOGGER = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
def _load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content.

    Parameters
    ----------
    file_path: Path
        Path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Required artifact not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------------------------------------------------
# Section builders
# -------------------------------------------------------------------------
def _build_overview() -> str:
    return (
        "## Overview\n\n"
        "This report summarizes the results of the high‑entropy alloy (HEA) "
        "yield‑strength prediction project. It includes model performance "
        "metrics, statistical validation analyses, and a discussion of data "
        "limitations.\n"
    )

def _build_model_performance(metrics: Dict[str, Any]) -> str:
    """Create the Model Performance markdown section."""
    lines = ["## Model Performance\n"]
    for model_key in ["linear", "rf", "gb"]:
        if model_key not in metrics:
            continue
        model_metrics = metrics[model_key]
        lines.append(f"### {model_key.title()} Regression")
        lines.append(
            f"- **R²**: {model_metrics.get('R2', 'N/A'):.4f}\n"
            f"- **MAE**: {model_metrics.get('MAE', 'N/A'):.4f}\n"
            f"- **RMSE**: {model_metrics.get('RMSE', 'N/A'):.4f}\n"
        )
    best = metrics.get("best_model", "N/A")
    lines.append(f"**Best model**: `{best}`\n")
    return "\n".join(lines)

def _build_vif_section(vif_results: Dict[str, Any]) -> str:
    lines = ["## Statistical Validation – VIF\n"]
    max_vif = vif_results.get("max_vif", None)
    needs = vif_results.get("needs_remediation", False)
    lines.append(f"- **Maximum VIF**: {max_vif:.2f}" if max_vif is not None else "- **Maximum VIF**: N/A")
    lines.append(f"- **Remediation needed**: {'Yes' if needs else 'No'}")
    lines.append("\n**Individual VIF values**\n")
    for descriptor, value in vif_results.get("vif_values", {}).items():
        lines.append(f"- {descriptor}: {value:.2f}")
    return "\n".join(lines)

def _build_permutation_section(permutation: Dict[str, Any]) -> str:
    lines = ["## Statistical Validation – Permutation Importance\n"]
    lines.append(f"- **Number of permutations**: {permutation.get('n_permutations', 'N/A')}")
    lines.append("\n**p‑values for descriptors**\n")
    for desc, pval in permutation.get("p_values", {}).items():
        lines.append(f"- {desc}: {pval:.4f}")
    return "\n".join(lines)

def _build_bootstrap_section(bootstrap: Dict[str, Any]) -> str:
    lines = ["## Statistical Validation – Bootstrap Confidence Intervals\n"]
    ci = bootstrap.get("confidence_interval", {})
    lines.append(
        f"- **R² confidence interval (best model)**: [{ci.get('best_model_lower', 'N/A'):.4f}, {ci.get('best_model_upper', 'N/A'):.4f}]\n"
        f"- **R² confidence interval (linear model)**: [{ci.get('linear_model_lower', 'N/A'):.4f}, {ci.get('linear_model_upper', 'N/A'):.4f}]"
    )
    return "\n".join(lines)

def _build_sensitivity_section(sensitivity: Dict[str, Any]) -> str:
    lines = ["## Sensitivity Analysis\n"]
    thresholds = sensitivity.get("thresholds", [])
    if not thresholds:
        lines.append("No sensitivity analysis data available.")
        return "\n".join(lines)

    lines.append("| α | R² (best model) | R² (linear) | Significant descriptors |\n")
    lines.append("|---|----------------|-------------|------------------------|\n")
    for entry in thresholds:
        alpha = entry.get("alpha")
        r2_best = entry.get("absolute_R2_best")
        r2_lin = entry.get("absolute_R2_linear")
        sig_cnt = entry.get("significant_count")
        lines.append(f"| {alpha:.2f} | {r2_best:.4f} | {r2_lin:.4f} | {sig_cnt} |")
    return "\n".join(lines)

def _build_data_limitation_warning(data_status: Dict[str, Any]) -> str:
    """Conditionally include the warning section."""
    if data_status.get("count_warning", False):
        count = data_status.get("count", 0)
        return (
            "## Data Limitation Warning\n\n"
            f"The processed dataset contains only **{count}** entries, which is "
            "below the recommended threshold of 500. Statistical power may be "
            "reduced, and results should be interpreted with caution.\n"
        )
    return ""

def _build_conclusion() -> str:
    return (
        "## Conclusion\n\n"
        "The predictive models demonstrate the feasibility of estimating HEA "
        "yield strength from compositional descriptors. While the best model "
        "offers promising performance, the data limitation warning highlights "
        "the need for larger, more diverse datasets to improve confidence in "
        "the findings.\n"
    )

# -------------------------------------------------------------------------
# Main orchestration
# -------------------------------------------------------------------------
def generate_report_content() -> str:
    """Assemble the full markdown report content."""
    base_path = Path("output")
    # Load required JSON artifacts
    metrics = _load_json(base_path / "metrics.json")
    data_status = _load_json(base_path / "data_status.json")
    vif = _load_json(base_path / "vif_results.json")
    permutation = _load_json(base_path / "permutation_results.json")
    bootstrap = _load_json(base_path / "bootstrap_results.json")
    sensitivity = _load_json(base_path / "sensitivity_results.json")

    sections = [
        _build_overview(),
        _build_model_performance(metrics),
        _build_vif_section(vif),
        _build_permutation_section(permutation),
        _build_bootstrap_section(bootstrap),
        _build_sensitivity_section(sensitivity),
        _build_data_limitation_warning(data_status),
        _build_conclusion(),
    ]

    report_body = "\n".join(sections)

    # Inject mandatory disclaimer
    report_with_disclaimer = inject_disclaimer(report_body)

    # Optionally run any finalisation steps (e.g., ensure trailing newline)
    final_report = finalize_report_markdown(report_with_disclaimer)

    return final_report

def write_report(output_path: Path = Path("output/report.md")) -> None:
    """Write the assembled report to the given path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = generate_report_content()
    with output_path.open("w", encoding="utf-8") as f:
        f.write(content)
    LOGGER.info("Report written to %s", output_path)

def main() -> None:
    """Entry point for ``python -m code.models.report_generator``."""
    try:
        write_report()
    except Exception as exc:
        LOGGER.error("Failed to generate report: %s", exc)
        raise

if __name__ == "__main__":
    main()