"""
T033: Generate final report for the sensitivity analysis.

This script reads the results from the meta-analysis pipeline (interaction model
and sensitivity sweep) and generates a markdown report summarizing the findings,
specifically focusing on the interaction term p-value and an explicit statement
of the associational nature of the study.

Dependencies:
- artifacts/meta_analysis/interaction_model.json (Output of T034/T031)
- artifacts/meta_analysis/sensitivity_sweep.json (Output of T062)
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Output path as per tasks.md
OUTPUT_PATH = Path("artifacts/meta_analysis/final_report.md")

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_p_value(p_val: float) -> str:
    """Format p-value for display, handling small values."""
    if p_val < 0.001:
        return f"< 0.001"
    return f"{p_val:.4f}"

def generate_report(
    interaction_model: Dict[str, Any],
    sensitivity_sweep: Dict[str, Any]
) -> str:
    """
    Construct the markdown content for the final report.

    Args:
        interaction_model: The loaded interaction model JSON data.
        sensitivity_sweep: The loaded sensitivity sweep JSON data.

    Returns:
        A string containing the formatted markdown report.
    """
    # Extract key metrics
    # The interaction model structure is expected to contain 'results' with 'params'
    # or a flattened structure depending on T031 output. We handle common statsmodels output shapes.
    params = interaction_model.get("results", {}).get("params", [])
    param_names = interaction_model.get("results", {}).get("param_names", [])
    
    interaction_p_value = None
    interaction_coef = None
    
    # Search for the interaction term (Condition Number * Violation Severity)
    # Assuming the column name includes 'interaction' or specific naming convention
    interaction_term_name = None
    for i, name in enumerate(param_names):
        # Heuristic: look for interaction term in name
        if "interaction" in name.lower() or ("condition" in name.lower() and "severity" in name.lower()):
            interaction_term_name = name
            if i < len(params):
                interaction_coef = params[i]
            # Find corresponding p-value. Usually in 'pvalues' list at same index
            pvalues = interaction_model.get("results", {}).get("pvalues", [])
            if i < len(pvalues):
                interaction_p_value = pvalues[i]
            break

    # If not found by heuristic, check if 'interaction' key exists directly or similar
    if interaction_p_value is None:
        # Fallback: check for a generic 'interaction_p_value' field if T031 added it explicitly
        interaction_p_value = interaction_model.get("interaction_p_value")
        interaction_coef = interaction_model.get("interaction_coef")

    # Sensitivity sweep metrics
    variance_rate = sensitivity_sweep.get("variance_in_classification_rates")
    sweep_details = sensitivity_sweep.get("details", [])

    # Construct Report
    report_lines = [
        "# Sensitivity of Regression Coefficients to Dataset Subset Selection: Final Report",
        "",
        "## Executive Summary",
        "",
        "This report summarizes the findings of the meta-analysis investigating the sensitivity of OLS regression coefficients to dataset subset selection. The analysis focuses on the interplay between data quality violations (heteroscedasticity) and numerical stability (multicollinearity).",
        "",
        "## Interaction Analysis Results",
        "",
        "A multiple regression model was fitted to assess the predictive power of the Condition Number, Violation Severity, and their interaction term on the empirical standard deviation of coefficients.",
        "",
        f"**Interaction Term Coefficient**: {interaction_coef:.6f if interaction_coef is not None else 'N/A'}",
        f"**Interaction Term P-Value**: {format_p_value(interaction_p_value) if interaction_p_value is not None else 'N/A'}",
        "",
    ]

    if interaction_p_value is not None:
        if interaction_p_value < 0.05:
            report_lines.append(
                "The interaction term is **statistically significant** (p < 0.05), suggesting that the effect of multicollinearity on coefficient instability is moderated by the severity of OLS assumption violations."
            )
        else:
            report_lines.append(
                "The interaction term is **not statistically significant** (p ≥ 0.05), indicating that the effects of multicollinearity and assumption violations on coefficient instability may be additive rather than multiplicative in this dataset."
            )
    else:
        report_lines.append(
            "**Note**: Interaction term p-value could not be extracted from the model output."
        )

    report_lines.extend([
        "",
        "## Sensitivity Sweep Analysis",
        "",
        "To assess the robustness of our severity classifications, we performed a sensitivity sweep across different Breusch-Pagan p-value cutoffs.",
        "",
        f"**Variance in Classification Rates**: {variance_rate:.6f if variance_rate is not None else 'N/A'}",
        "",
        "### Sweep Details",
        "",
        "| Cutoff | Classification Rate |",
        "| :--- | :--- |",
    ])

    for item in sweep_details:
        cutoff = item.get("cutoff", "N/A")
        rate = item.get("rate", "N/A")
        report_lines.append(f"| {cutoff} | {rate:.4f} |")

    report_lines.extend([
        "",
        "## Limitations and Associational Nature",
        "",
        "### Associational Nature of Findings",
        "",
        "**Crucially, the findings presented in this report are strictly associational.**",
        "",
        "While the analysis identifies significant statistical relationships between dataset characteristics (multicollinearity, assumption violations) and the observed instability of regression coefficients, **these results do not imply causation**.",
        "",
        "The observed interactions describe how these factors co-vary within the sampled subsets. We cannot claim that high multicollinearity *causes* increased sensitivity to subset selection, nor that assumption violations *cause* the observed variance, without further controlled experimentation or causal inference frameworks. The relationships are descriptive of the statistical properties of the data subsets analyzed.",
        "",
        "### Methodological Limitations",
        "",
        "- **Subset Selection**: The stability estimates rely on random subset sampling. Systematic biases in the original dataset may not be fully captured by random subsampling.",
        "- **Model Specification**: The interaction model assumes a linear relationship between the predictors and the log-variance of coefficients. Non-linear effects may be present.",
        "- **Dataset Scope**: The results are specific to the numerical datasets included in the ingestion phase. Generalization to other domains requires further validation.",
        "",
        "## Conclusion",
        "",
        "The meta-analysis provides empirical evidence regarding the stability of regression coefficients under varying data conditions. The significant interaction (if applicable) highlights the complex interplay between data quality and numerical stability, underscoring the importance of rigorous diagnostic checks before interpreting regression coefficients in sensitive applications.",
        "",
        "---",
        f"*Report generated automatically by T033 on {Path.cwd()}.*"
    ])

    return "\n".join(report_lines)

def main():
    """Main entry point for the report generation script."""
    print("Starting T033: Final Report Generation...")

    # Define paths relative to project root
    base_path = Path(".")
    interaction_model_path = base_path / "artifacts" / "meta_analysis" / "interaction_model.json"
    sensitivity_sweep_path = base_path / "artifacts" / "meta_analysis" / "sensitivity_sweep.json"

    # Check inputs
    if not interaction_model_path.exists():
        print(f"ERROR: Missing required input: {interaction_model_path}")
        print("Please ensure T034 (Interaction Model) and T031 (Regression Analysis) have completed successfully.")
        sys.exit(1)

    if not sensitivity_sweep_path.exists():
        print(f"ERROR: Missing required input: {sensitivity_sweep_path}")
        print("Please ensure T062 (Sensitivity Sweep) has completed successfully.")
        sys.exit(1)

    try:
        # Load data
        print(f"Loading interaction model from {interaction_model_path}...")
        interaction_model = load_json_file(interaction_model_path)

        print(f"Loading sensitivity sweep from {sensitivity_sweep_path}...")
        sensitivity_sweep = load_json_file(sensitivity_sweep_path)

        # Generate report
        print("Generating report content...")
        report_content = generate_report(interaction_model, sensitivity_sweep)

        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        print(f"Writing final report to {OUTPUT_PATH}...")
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(report_content)

        print("SUCCESS: Final report generated successfully.")
        return 0

    except Exception as e:
        print(f"ERROR: Failed to generate report: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())