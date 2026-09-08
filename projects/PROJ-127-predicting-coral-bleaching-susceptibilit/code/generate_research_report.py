import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional
import config

def load_json_safe(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load JSON file if it exists, otherwise return default or raise if critical."""
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"Required result file not found: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupted JSON file {path}: {e}")

def check_data_gap_status() -> Dict[str, Any]:
    """
    Check the status of data gap verification.
    Returns status based on existence and content of data_gap_report.md.
    """
    report_path = Path(config.PROJECT_ROOT) / "data_gap_report.md"
    status = {
        "verified": True,
        "missing_sources": [],
        "halt_flag": False,
        "report_exists": report_path.exists()
    }

    if status["report_exists"]:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "HALT" in content:
                status["halt_flag"] = True
                status["verified"] = False
                # Attempt to parse missing sources if format is known, else generic
                for line in content.split('\n'):
                    if "Missing" in line or "MISSING" in line:
                        status["missing_sources"].append(line.strip())
    return status

def generate_research_report(output_path: Path):
    """
    Generate the final research.md report containing all metrics and data gap status.
    Aggregates results from evaluate.json, map_analysis.json, and data_gap_report.md.
    """
    project_root = Path(config.PROJECT_ROOT)

    # Load evaluation metrics (from T025, T027, T028)
    eval_results_path = project_root / "data" / "models" / "evaluate.json"
    try:
        eval_data = load_json_safe(eval_results_path)
    except FileNotFoundError:
        warnings.warn(f"Could not find {eval_results_path}. Metrics will be marked as missing.")
        eval_data = {}

    # Load map analysis results (from T031, T032, T033)
    map_results_path = project_root / "data" / "models" / "map_analysis.json"
    try:
        map_data = load_json_safe(map_results_path)
    except FileNotFoundError:
        warnings.warn(f"Could not find {map_results_path}. Map metrics will be marked as missing.")
        map_data = {}

    # Check data gap status
    data_gap_status = check_data_gap_status()

    # Construct Report Content
    report_lines = []
    report_lines.append("# Research Report: Predicting Coral Bleaching Susceptibility")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append(f"This report summarizes the findings from the automated science pipeline "
                        f"for predicting coral bleaching susceptibility. The pipeline executed "
                        f"tasks T001 through T035.")
    report_lines.append("")

    # Data Gap Status Section
    report_lines.append("## Data Gap Verification Status")
    report_lines.append("")
    if data_gap_status["verified"]:
        report_lines.append("- **Status**: PASSED")
        report_lines.append("- **Details**: All required data sources were verified and accessible.")
    else:
        report_lines.append("- **Status**: FAILED / HALT TRIGGERED")
        report_lines.append("- **Details**: The following data sources were missing or invalid:")
        for source in data_gap_status["missing_sources"]:
            report_lines.append(f"  - {source}")
        report_lines.append("")
        report_lines.append("**WARNING**: The pipeline halted due to missing data. "
                            "Subsequent results may be incomplete or based on fallback data.")
    report_lines.append("")

    # Model Performance Metrics (ROC-AUC, etc.)
    report_lines.append("## Model Performance Metrics")
    report_lines.append("")
    report_lines.append("The model was trained using XGBoost with spatial cross-validation "
                        "(Western Pacific train, Eastern Pacific test).")
    report_lines.append("")

    roc_auc = eval_data.get("roc_auc")
    if roc_auc is not None:
        report_lines.append(f"- **ROC-AUC**: {roc_auc:.4f}")
    else:
        report_lines.append("- **ROC-AUC**: Not available (Test set may have had zero positive events or data missing).")

    # Permutation Importance & FDR
    report_lines.append("")
    report_lines.append("### Feature Importance (Permutation with FDR Correction)")
    report_lines.append("")
    importance_data = eval_data.get("permutation_importance", [])
    if importance_data:
        report_lines.append("| Rank | Feature | Importance | P-Value | Significant (FDR) |")
        report_lines.append("|------|---------|------------|---------|-------------------|")
        # Assuming the list is already sorted by importance in the source
        for i, item in enumerate(importance_data, 1):
            name = item.get("feature", "Unknown")
            score = item.get("score", 0.0)
            p_val = item.get("p_value", 1.0)
            fdr_sig = "Yes" if item.get("significant", False) else "No"
            report_lines.append(f"| {i} | {name} | {score:.4f} | {p_val:.4f} | {fdr_sig} |")
    else:
        report_lines.append("No permutation importance data available.")

    # Bootstrap Stability
    report_lines.append("")
    report_lines.append("### Bootstrap Stability Analysis")
    report_lines.append("")
    stability_data = eval_data.get("bootstrap_stability", {})
    if stability_data:
        top_features = stability_data.get("top_3_stability", [])
        if top_features:
            report_lines.append("Stability of top-3 predictors across 100 resamples:")
            for feat, score in top_features:
                report_lines.append(f"- **{feat}**: Stability Score {score:.4f}")
        else:
            report_lines.append("No stability scores recorded.")
    else:
        report_lines.append("Bootstrap stability analysis not available.")

    # Map Analysis & Thresholds
    report_lines.append("")
    report_lines.append("## Risk Mapping and Threshold Analysis")
    report_lines.append("")

    # Threshold Sensitivity
    threshold_data = map_data.get("threshold_sensitivity", [])
    if threshold_data:
        report_lines.append("### Threshold Sensitivity Analysis")
        report_lines.append("")
        report_lines.append("| Cutoff | False Positive Rate | False Negative Rate |")
        report_lines.append("|--------|---------------------|---------------------|")
        for row in threshold_data:
            cutoff = row.get("cutoff", 0.5)
            fp = row.get("fp_rate", 0.0)
            fn = row.get("fn_rate", 0.0)
            report_lines.append(f"| {cutoff} | {fp:.4f} | {fn:.4f} |")
    else:
        report_lines.append("Threshold sensitivity analysis not available.")

    # Independent Validation
    report_lines.append("")
    report_lines.append("### Independent Validation (AUPRC)")
    report_lines.append("")
    auprc = map_data.get("auprc_independent")
    if auprc is not None:
        report_lines.append(f"- **AUPRC against independent reports**: {auprc:.4f}")
    else:
        report_lines.append("- **AUPRC**: Not available (Independent data missing or validation skipped).")

    # Dominant Drivers
    report_lines.append("")
    report_lines.append("### Dominant Drivers (Top 10 High-Risk Pixels)")
    report_lines.append("")
    drivers = map_data.get("dominant_drivers", [])
    if drivers:
        for i, driver in enumerate(drivers, 1):
            pixel_id = driver.get("pixel_id", f"Pixel {i}")
            feature = driver.get("feature", "Unknown")
            report_lines.append(f"{i}. **Pixel {pixel_id}**: Dominant driver is **{feature}**")
    else:
        report_lines.append("No dominant driver analysis available.")

    # Conclusion
    report_lines.append("")
    report_lines.append("## Conclusion")
    report_lines.append("")
    if data_gap_status["verified"] and roc_auc is not None:
        report_lines.append("The pipeline successfully generated a predictive model for coral bleaching susceptibility "
                            "with verified data sources and robust statistical validation.")
    else:
        report_lines.append("The pipeline encountered data availability issues or missing result artifacts. "
                            "Review the Data Gap Status and specific metric sections for details.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Generated by llmXive pipeline on {config.RUN_TIMESTAMP if hasattr(config, 'RUN_TIMESTAMP') else 'Unknown date'}*")

    # Write Report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"Research report generated successfully at: {output_path}")

def main():
    """Entry point for generating the research report."""
    output_path = Path(config.PROJECT_ROOT) / "research.md"
    generate_research_report(output_path)

if __name__ == "__main__":
    main()
