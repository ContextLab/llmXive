import os
import json
import sys
from pathlib import Path
from datetime import datetime
from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR

def load_json_file(file_path: str) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required metrics file not found: {file_path}. "
                                "Ensure T021 (evaluate.py) has run successfully.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metrics file {file_path}: {e}")

def generate_associational_report(metrics_data: dict, correlations_data: dict, vif_data: dict) -> dict:
    """
    Generate a report ensuring all findings are framed as ASSOCIATIONAL (FR-011).
    
    This function takes the raw metrics, correlations, and collinearity diagnostics
    and wraps them in a narrative that explicitly avoids causal language.
    """
    timestamp = datetime.now().isoformat()
    
    report = {
        "report_type": "Associational Analysis Summary",
        "generation_timestamp": timestamp,
        "disclaimer": (
          "CRITICAL NOTE: This study is OBSERVATIONAL and ASSOCIATIONAL in nature. "
          "The findings described below represent statistical correlations and associations "
          "between metabolomic profiles and disease resistance phenotypes. "
          "NO CAUSAL INFERENCES should be drawn from this analysis. "
          "Confounding factors, reverse causality, and unmeasured variables may explain "
          "the observed associations. Further experimental validation is required to "
          "establish causality."
        ),
        "summary": {
            "model_performance": {
                "balanced_accuracy": metrics_data.get("balanced_accuracy", "N/A"),
                "roc_auc": metrics_data.get("roc_auc", "N/A"),
                "interpretation": (
                    f"The model demonstrates an associational signal with a "
                    f"balanced accuracy of {metrics_data.get('balanced_accuracy', 'N/A')}. "
                    "This indicates that metabolomic features are statistically "
                    "associated with the resistance labels in the dataset, "
                    "but does not imply that these metabolites cause resistance."
                )
            },
            "significance": {
                "permutation_p_value": metrics_data.get("permutation_p_value", "N/A"),
                "fdr_corrected_threshold": metrics_data.get("fdr_threshold", 0.05),
                "interpretation": (
                    "Statistical significance was assessed via permutation testing. "
                    "A low p-value indicates that the observed association is unlikely "
                    "to have occurred by chance, but does not confirm a causal mechanism."
                )
            },
            "collinearity_warning": {
                "high_vif_metabolites": vif_data.get("high_vif_metabolites", []),
                "interpretation": (
                    "High collinearity (VIF > 5) detected in the following metabolites. "
                    "This suggests that the association strength for these features "
                    "may be shared with other correlated metabolites. "
                    "Feature importance scores should be interpreted with caution "
                    "as they reflect associational strength within a correlated group, "
                    "not necessarily individual causal contribution."
                )
            }
        },
        "associational_findings": {
            "top_associated_metabolites": [],
            "interpretation_template": (
                "Metabolite '{metabolite}' shows a strong statistical association "
                "with disease resistance (Correlation: {corr}, FDR-corrected p-value: {pval}). "
                "This association suggests a potential biological link, but the direction "
                "of effect and causality remain unproven without further experimental "
                "intervention (e.g., metabolite application or knock-out studies)."
            )
        },
        "limitations": [
            "Observational study design precludes causal inference.",
            "Potential unmeasured confounders (e.g., soil composition, weather) may drive associations.",
            "Metabolomic profiles are correlative snapshots; temporal dynamics are not fully captured.",
            "Model performance is specific to the dataset and may not generalize to other plant species or environments."
        ],
        "recommendations": [
            "Treat all feature importances as markers of association, not targets for intervention.",
            "Prioritize top-associated metabolites for downstream experimental validation (e.g., CRISPR, exogenous application).",
            "Replicate findings in independent cohorts to verify robustness of associations."
        ]
    }

    # Populate top associated metabolites from correlation data
    if "correlations" in correlations_data:
        for item in correlations_data["correlations"]:
            report["associational_findings"]["top_associated_metabolites"].append({
                "metabolite": item.get("metabolite", "Unknown"),
                "correlation_coefficient": item.get("correlation", 0.0),
                "fdr_corrected_p_value": item.get("fdr_p_value", 1.0),
                "narrative": report["associational_findings"]["interpretation_template"].format(
                    metabolite=item.get("metabolite", "Unknown"),
                    corr=item.get("correlation", 0.0),
                    pval=item.get("fdr_p_value", 1.0)
                )
            })

    return report

def main():
    """
    Main entry point to generate the associational report.
    Loads metrics, correlations, and VIF data, then writes the final report.
    """
    # Ensure results directory exists
    results_path = Path(RESULTS_DIR)
    results_path.mkdir(parents=True, exist_ok=True)

    # Define input paths based on previous tasks (T021, T022)
    metrics_path = results_path / "metrics.json"
    correlations_path = results_path / "shap_analysis.json" # T021 output for correlations
    vif_path = results_path / "collinearity.json" # T022 output

    # Check for existence of prerequisite files
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics file: {metrics_path}. Run T021 first.")
    if not correlations_path.exists():
        raise FileNotFoundError(f"Missing correlations/shap file: {correlations_path}. Run T021 first.")
    if not vif_path.exists():
        raise FileNotFoundError(f"Missing VIF file: {vif_path}. Run T022 first.")

    # Load data
    metrics_data = load_json_file(str(metrics_path))
    correlations_data = load_json_file(str(correlations_path))
    vif_data = load_json_file(str(vif_path))

    # Generate report
    report = generate_associational_report(metrics_data, correlations_data, vif_data)

    # Write report
    output_path = results_path / "associational_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Associational report generated successfully at: {output_path}")
    print("WARNING: All findings in this report are framed as ASSOCIATIONAL only.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
