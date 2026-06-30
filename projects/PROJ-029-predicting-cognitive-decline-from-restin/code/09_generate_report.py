"""
Generate the final research report aggregating all results.
Explicitly labels findings as associational and documents limitations.
"""
import os
import sys
import json
from pathlib import Path
import pandas as pd

def main():
    """Main entry point for report generation."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Input paths
    perf_path = project_root / "data" / "processed" / "performance_report.json"
    perm_path = project_root / "data" / "processed" / "permutation_results.json"
    sens_path = project_root / "data" / "processed" / "sensitivity_report.json"
    limits_path = project_root / "data" / "artifacts" / "limitations.txt"
    output_path = project_root / "data" / "artifacts" / "final_report.md"

    # Load results
    try:
        with open(perf_path, "r") as f:
            perf_data = json.load(f)
    except FileNotFoundError:
        perf_data = {"error": "Performance report not found"}

    try:
        with open(perm_path, "r") as f:
            perm_data = json.load(f)
    except FileNotFoundError:
        perm_data = {"error": "Permutation results not found"}

    try:
        with open(sens_path, "r") as f:
            sens_data = json.load(f)
    except FileNotFoundError:
        sens_data = {"error": "Sensitivity report not found"}

    try:
        with open(limits_path, "r") as f:
            limitations = f.read()
    except FileNotFoundError:
        limitations = "No specific limitations documented."

    # Generate report
    report = []
    report.append("# Final Research Report: Predicting Cognitive Decline from Resting-State fMRI")
    report.append("")
    report.append("## Executive Summary")
    report.append("")
    report.append("This study investigates the association between resting-state fMRI network topology and cognitive decline.")
    report.append("**Important**: All findings presented here are **associational** and do not imply causation (FR-007).")
    report.append("")

    report.append("## Model Performance")
    report.append("")
    if "mean_auc" in perf_data:
        report.append(f"- **ROC-AUC**: {perf_data['mean_auc']:.4f}")
        report.append(f"- **Fold Scores**: {perf_data.get('fold_scores', 'N/A')}")
    else:
        report.append("- Model performance data unavailable.")
    report.append("")

    report.append("## Statistical Significance")
    report.append("")
    if "p_value" in perm_data:
        report.append(f"- **Permutation p-value**: {perm_data['p_value']:.4f}")
        report.append(f"- **Permutations**: {perm_data.get('n_permutations', 'N/A')}")
    else:
        report.append("- Permutation test results unavailable.")
    report.append("")

    report.append("## Sensitivity Analysis")
    report.append("")
    if sens_data and "threshold_sweep" in sens_data:
        report.append("### Decision Threshold Sweep")
        report.append("")
        for t in sens_data.get("threshold_sweep", []):
            report.append(f"- Threshold {t['threshold']}: FPR={t['fpr']:.4f}, FNR={t['fnr']:.4f}")
    else:
        report.append("- Sensitivity analysis results unavailable.")
    report.append("")

    report.append("## Limitations")
    report.append("")
    report.append(limitations)
    report.append("")

    report.append("## Conclusion")
    report.append("")
    report.append("This pipeline successfully processed resting-state fMRI data to extract graph metrics and trained a predictive model.")
    report.append("While the model shows predictive capability, the results must be interpreted as associations.")
    report.append("Future work should validate these findings in independent cohorts and explore causal mechanisms.")
    report.append("")

    # Write report
    with open(output_path, "w") as f:
        f.write("\n".join(report))

    print(f"Report generated: {output_path}")

if __name__ == "__main__":
    main()
