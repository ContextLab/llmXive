"""
Report Generator for the HEA Yield Strength Prediction project.

This module reads the various JSON artifacts produced by the pipeline,
assembles a markdown report, injects the mandatory disclaimer, and writes
the final report to ``output/report.md``.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

from utils.logging import get_logger
from utils.report_utils import inject_disclaimer, finalize_report_markdown

LOGGER = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions to load JSON artifacts
# ----------------------------------------------------------------------
def _load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content."""
    if not path.is_file():
        raise FileNotFoundError(f"Required JSON artifact not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Content generation
# ----------------------------------------------------------------------
def generate_report_content() -> str:
    """
    Assemble the markdown report content.

    The function reads the following artifacts (all under the project root):
      - output/data_status.json
      - output/metrics.json
      - output/vif_results.json
      - output/permutation_results.json
      - output/bootstrap_results.json
      - output/sensitivity_results.json

    It creates sections:
      1. Overview
      2. Model Performance
      3. Statistical Validation
      4. Sensitivity Analysis
      5. Data Limitation Warning (conditional)
      6. Disclaimer (added later via ``inject_disclaimer``)

    Returns
    -------
    str
        The full markdown report (without the final disclaimer).
    """
    # Base directory for output artifacts
    out_dir = Path("output")
    data_status_path = out_dir / "data_status.json"
    metrics_path = out_dir / "metrics.json"
    vif_path = out_dir / "vif_results.json"
    perm_path = out_dir / "permutation_results.json"
    boot_path = out_dir / "bootstrap_results.json"
    sens_path = out_dir / "sensitivity_results.json"

    # Load all required JSON files
    data_status = _load_json(data_status_path)
    metrics = _load_json(metrics_path)
    vif = _load_json(vif_path)
    permutation = _load_json(perm_path)
    bootstrap = _load_json(boot_path)
    sensitivity = _load_json(sens_path)

    # ------------------------------------------------------------------
    # 1. Overview
    # ------------------------------------------------------------------
    overview = (
        "# Overview\\n\\n"
        "This report summarizes the results of the high‑entropy alloy (HEA) "
        "yield‑strength prediction pipeline. The workflow includes data "
        "acquisition, descriptor engineering, model training, and extensive "
        "statistical validation.\\n\\n"
    )

    # ------------------------------------------------------------------
    # 2. Model Performance
    # ------------------------------------------------------------------
    perf_lines = ["## Model Performance\\n"]
    for model_key, model_metrics in metrics.items():
        if model_key == "best_model":
            continue
        perf_lines.append(f"### {model_key.upper()} Model")
        perf_lines.append(f"- **R²**: {model_metrics.get('R2', 'N/A')}")
        perf_lines.append(f"- **MAE**: {model_metrics.get('MAE', 'N/A')}")
        perf_lines.append(f"- **RMSE**: {model_metrics.get('RMSE', 'N/A')}\\n")
    perf_lines.append(f"**Best Model:** `{metrics.get('best_model', 'N/A')}`\\n")
    model_performance = "\\n".join(perf_lines) + "\\n"

    # ------------------------------------------------------------------
    # 3. Statistical Validation
    # ------------------------------------------------------------------
    stat_lines = ["## Statistical Validation\\n"]

    # VIF results (linear model only)
    stat_lines.append("### Variance Inflation Factor (VIF) – Linear Regression")
    vif_vals = vif.get("vif_values", {})
    if vif_vals:
        for descriptor, value in vif_vals.items():
            flag = "⚠️ High VIF (>10)" if value > 10 else ""
            stat_lines.append(f"- {descriptor}: {value:.2f} {flag}")
    else:
        stat_lines.append("- No VIF values available.")
    stat_lines.append("")

    # Permutation importance
    stat_lines.append("### Permutation Importance")
    perm_summary = permutation.get("summary", {})
    if perm_summary:
        for desc, info in perm_summary.items():
            pval = info.get("p_value", "N/A")
            stat_lines.append(f"- {desc}: p‑value = {pval}")
    else:
        stat_lines.append("- Permutation results not available.")
    stat_lines.append("")

    # Bootstrap confidence intervals
    stat_lines.append("### Bootstrap Confidence Intervals for R²")
    boot_ci = bootstrap.get("r2_confidence_interval", {})
    if boot_ci:
        lower = boot_ci.get("lower", "N/A")
        upper = boot_ci.get("upper", "N/A")
        stat_lines.append(f"- 95 % CI: [{lower}, {upper}]")
    else:
        stat_lines.append("- Bootstrap results not available.")
    stat_lines.append("")

    statistical_validation = "\\n".join(stat_lines) + "\\n"

    # ------------------------------------------------------------------
    # 4. Sensitivity Analysis
    # ------------------------------------------------------------------
    sens_lines = ["## Sensitivity Analysis\\n"]
    thresholds = sensitivity.get("thresholds", [])
    if thresholds:
        for entry in thresholds:
            alpha = entry.get("alpha")
            r2_best = entry.get("absolute_R2_best")
            r2_linear = entry.get("absolute_R2_linear")
            sig_cnt = entry.get("significant_count")
            sens_lines.append(
                f"- **α = {alpha}**: best model R² = {r2_best}, "
                f"linear model R² = {r2_linear}, "
                f"significant descriptors = {sig_cnt}"
            )
    else:
        sens_lines.append("- No sensitivity analysis results available.")
    sens_lines.append("")
    sensitivity_analysis = "\\n".join(sens_lines) + "\\n"

    # ------------------------------------------------------------------
    # 5. Data Limitation Warning (conditional)
    # ------------------------------------------------------------------
    warning_section = ""
    if data_status.get("count_warning", False):
        count = data_status.get("count", 0)
        warning_section = (
            "## Data Limitation Warning\\n\\n"
            f"Only **{count}** entries were found after preprocessing. "
            "Statistical power may be reduced, and results should be "
            "interpreted with caution.\\n\\n"
        )

    # Assemble full report (without disclaimer)
    report_body = (
        overview
        + model_performance
        + statistical_validation
        + sensitivity_analysis
        + warning_section
    )

    # The disclaimer will be injected later by ``inject_disclaimer``.
    return report_body

# ----------------------------------------------------------------------
# Write report to disk
# ----------------------------------------------------------------------
def write_report(content: str, output_path: Path = Path("output/report.md")) -> None:
    """
    Write the markdown ``content`` to ``output_path``. The function ensures
    the parent directory exists.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(content)
    LOGGER.info(f"Report written to {output_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Generate the report and write it to ``output/report.md``.
    The function:
      1. Generates the core content.
      2. Injects the mandatory disclaimer (via ``utils.report_utils.inject_disclaimer``).
      3. Finalises markdown formatting (via ``utils.report_utils.finalize_report_markdown``).
      4. Writes the final markdown file.
    """
    try:
        LOGGER.info("Generating report content...")
        raw_content = generate_report_content()
        LOGGER.info("Injecting disclaimer...")
        content_with_disclaimer = inject_disclaimer(raw_content)
        LOGGER.info("Finalising markdown...")
        final_content = finalize_report_markdown(content_with_disclaimer)
        write_report(final_content)
    except Exception as exc:
        LOGGER.error(f"Failed to generate report: {exc}")
        raise

if __name__ == "__main__":
    main()
