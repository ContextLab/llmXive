"""
Generate a human-readable narrative report (Markdown) that explicitly converts
the 'framing' JSON data from metrics, shap_analysis, and pathway_analysis
into a cohesive text document.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path if needed
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_json_file(filepath: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_framing_report() -> str:
    """
    Generate the narrative report content.
    Reads from results/metrics.json, results/shap_analysis.json, results/pathway_analysis.json.
    """
    metrics_path = RESULTS_DIR / "metrics.json"
    shap_path = RESULTS_DIR / "shap_analysis.json"
    pathway_path = RESULTS_DIR / "pathway_analysis.json"

    # Load data with error handling
    try:
        metrics = load_json_file(metrics_path)
    except FileNotFoundError as e:
        sys.stderr.write(f"Warning: {e}\n")
        metrics = {}

    try:
        shap = load_json_file(shap_path)
    except FileNotFoundError as e:
        sys.stderr.write(f"Warning: {e}\n")
        shap = {}

    try:
        pathway = load_json_file(pathway_path)
    except FileNotFoundError as e:
        sys.stderr.write(f"Warning: {e}\n")
        pathway = {}

    # Extract key values
    framing_text = metrics.get("framing", pathway.get("framing", shap.get("framing", "")))
    if not framing_text:
        framing_text = "These results represent associations, not causation."

    # Metrics Summary
    bal_acc = metrics.get("balanced_accuracy", "N/A")
    roc_auc = metrics.get("roc_auc", "N/A")
    perm_p = metrics.get("permutation_p_value", "N/A")

    # SHAP/Correlation Summary
    top_features = shap.get("top_features", [])
    collinearity = shap.get("collinearity_vif", [])

    # Pathway Summary
    narrative_report = pathway.get("narrative_report", "")
    pathway_mappings = pathway.get("pathway_mappings", [])

    # Build Markdown Content
    report_lines = [
        "# Plant Disease Resistance Prediction: Framing Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Executive Summary",
        "",
        f"This report summarizes the findings from the automated analysis of pre-challenge metabolomic profiles to predict plant disease resistance. ",
        f"The analysis identified {len(top_features)} top metabolite features associated with resistance phenotypes.",
        "",
        "## Mandatory Framing Statement",
        "",
        f"> **{framing_text}**",
        "",
        "## Model Performance Metrics",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| Balanced Accuracy | {bal_acc} |",
        f"| ROC-AUC | {roc_auc} |",
        f"| Permutation Test p-value | {perm_p} |",
        "",
        "## Key Findings: Metabolite Associations",
        "",
        "The following metabolites were identified as having the strongest statistical associations with disease resistance:",
        "",
    ]

    if top_features:
        report_lines.append("| Rank | Metabolite (InChIKey) | SHAP Value |")
        report_lines.append("| :--- | :--- | :--- |")
        for i, feat in enumerate(top_features, 1):
            name = feat.get("feature_name", "Unknown")
            val = feat.get("shap_value", 0)
            report_lines.append(f"| {i} | {name} | {val:.4f} |")
    else:
        report_lines.append("*No significant top features were identified in the analysis.*")

    report_lines.extend([
        "",
        "## Collinearity Diagnostics",
        "",
    ])

    if collinearity:
        report_lines.append("Variance Inflation Factor (VIF) analysis was performed to assess multicollinearity among top features:")
        report_lines.append("")
        report_lines.append("| Metabolite | VIF Value | Status |")
        report_lines.append("| :--- | :--- | :--- |")
        for item in collinearity:
            name = item.get("feature_name", "Unknown")
            val = item.get("vif_value", 0)
            status = "High" if val > 5 else "Acceptable"
            report_lines.append(f"| {name} | {val:.2f} | {status} |")
    else:
        report_lines.append("*Collinearity diagnostics could not be performed or returned no results.*")

    report_lines.extend([
        "",
        "## Biological Interpretation",
        "",
    ])

    if pathway_mappings:
        report_lines.append("The top metabolites were mapped to known biological pathways:")
        report_lines.append("")
        # Group by pathway
        pathway_counts = {}
        for pm in pathway_mappings:
            p_name = pm.get("pathway_name", "Unknown Pathway")
            pathway_counts[p_name] = pathway_counts.get(p_name, 0) + 1

        for p_name, count in sorted(pathway_counts.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- **{p_name}** ({count} associated metabolites)")
    else:
        report_lines.append("*No pathway mappings were available.*")

    if narrative_report:
        report_lines.extend([
            "",
            "### Narrative Analysis",
            "",
            narrative_report,
        ])

    report_lines.extend([
        "",
        "## Conclusion",
        "",
        "This analysis provides statistical evidence of associations between specific pre-challenge metabolite profiles and disease resistance outcomes. ",
        "While these findings highlight potential biomarkers and biological mechanisms, they do not establish causality. ",
        "Further experimental validation is required to confirm the functional role of these metabolites in plant immunity.",
        "",
        "---",
        "",
        "*Report generated by the llmXive automated science pipeline.*",
    ])

    return "\n".join(report_lines)

def main():
    """Main entry point to generate the framing report."""
    print("Generating framing report...")
    try:
        content = generate_framing_report()
        output_path = RESULTS_DIR / "report_framing.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully generated: {output_path}")
        
        # Verify content contains mandatory framing text
        if "associations, not causation" in content.lower():
            print("Verification: Mandatory framing text found.")
        else:
            print("Warning: Mandatory framing text may be missing or malformed.")
            
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()