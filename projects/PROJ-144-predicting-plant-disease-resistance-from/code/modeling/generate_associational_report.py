"""
Generate the final associational findings report to ensure FR-011 compliance.

This script reads the model metrics and SHAP analysis results,
and writes a human-readable markdown report that explicitly frames
all findings as associational, avoiding causal language.
"""
import os
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if necessary, though we are mostly reading files
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR

def load_json_file(filepath):
    """Load a JSON file safely."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required artifact not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_associational_report(metrics_data, shap_data, collinearity_data=None):
    """
    Generate a markdown report framing all findings as associational.
    
    Args:
        metrics_data (dict): Metrics from evaluate.py (balanced_acc, auc, etc.)
        shap_data (dict): SHAP analysis results (feature importances, values)
        collinearity_data (dict, optional): Collinearity diagnostics (VIF)
    
    Returns:
        str: The markdown content of the report.
    """
    report_lines = []
    
    # Header
    report_lines.append("# Plant Disease Resistance Prediction: Associational Findings Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Important Disclaimer")
    report_lines.append("")
    report_lines.append("> **This report presents ASSOCIATIONAL findings only.**")
    report_lines.append("> The statistical relationships identified between metabolite profiles")
    report_lines.append("> and disease resistance labels are **CORRELATIONS**, not evidence of")
    report_lines.append("> **CAUSATION**. This analysis does not establish that specific metabolites")
    report_lines.append("> cause disease resistance or susceptibility.")
    report_lines.append("")
    
    # Model Performance Section
    report_lines.append("## 1. Model Performance (Associational Predictive Power)")
    report_lines.append("")
    report_lines.append("The Random Forest model demonstrates the ability to **associate** metabolite")
    report_lines.append("patterns with resistance labels in the held-out test set. These metrics")
    report_lines.append("reflect predictive accuracy, not causal mechanisms.")
    report_lines.append("")
    
    if 'balanced_accuracy' in metrics_data:
        report_lines.append(f"- **Balanced Accuracy:** {metrics_data['balanced_accuracy']:.4f}")
    if 'roc_auc' in metrics_data:
        report_lines.append(f"- **ROC-AUC:** {metrics_data['roc_auc']:.4f}")
    if 'permutation_p_value' in metrics_data:
        report_lines.append(f"- **Permutation Test p-value:** {metrics_data['permutation_p_value']:.4f}")
        report_lines.append("  - *Interpretation:* A low p-value indicates the observed association")
        report_lines.append("    is unlikely to have occurred by random chance, but does not imply causality.")
    
    report_lines.append("")
    
    # Feature Importance Section
    report_lines.append("## 2. Associated Metabolites")
    report_lines.append("")
    report_lines.append("The following metabolites show the strongest **statistical association**")
    report_lines.append("with disease resistance status according to SHAP values. High SHAP values")
    report_lines.append("indicate that the presence or concentration of these metabolites is")
    report_lines.append("associated with the predicted class, but do not prove they drive the outcome.")
    report_lines.append("")
    
    if shap_data and 'top_features' in shap_data:
        report_lines.append("| Metabolite | Mean |SHAP| | Direction of Association |")
        report_lines.append("|------------|------|------------------------|")
        for feat in shap_data['top_features'][:10]:
            name = feat.get('feature', 'Unknown')
            importance = feat.get('importance', 0.0)
            # Determine direction based on sign if available, else generic
            direction = "Positive Association" if feat.get('sign', 0) >= 0 else "Negative Association"
            report_lines.append(f"| {name} | {importance:.4f} | {direction} |")
    else:
        report_lines.append("*No SHAP data available.*")
    
    report_lines.append("")
    
    # Collinearity Section
    if collinearity_data:
        report_lines.append("## 3. Collinearity Diagnostics")
        report_lines.append("")
        report_lines.append("High collinearity among metabolites can affect the stability of")
        report_lines.append("association estimates. The following metabolites exhibited high VIF (>5):")
        report_lines.append("")
        
        high_vif = collinearity_data.get('high_vif_features', [])
        if high_vif:
            report_lines.append("| Metabolite | VIF |")
            report_lines.append("|------------|-----|")
            for item in high_vif:
                report_lines.append(f"| {item.get('feature', 'Unknown')} | {item.get('vif', 0):.2f} |")
        else:
            report_lines.append("No metabolites exceeded the VIF > 5 threshold.")
        report_lines.append("")
    
    # Conclusion Section
    report_lines.append("## 4. Conclusion")
    report_lines.append("")
    report_lines.append("This analysis identifies a set of metabolites that are **statistically associated**")
    report_lines.append("with plant disease resistance. While these associations may suggest biological")
    report_lines.append("pathways worthy of further experimental investigation (e.g., via knockout studies"),
    report_lines.append("or targeted perturbation), **no causal claims are made** based on this observational")
    report_lines.append("data alone.")
    report_lines.append("")
    report_lines.append("Future work involving controlled experiments is required to determine if any of")
    report_lines.append("these metabolites play a causal role in disease resistance mechanisms.")
    report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    """Main entry point to generate the associational report."""
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_path = results_dir / "metrics.json"
    shap_path = results_dir / "shap_analysis.json"
    collinearity_path = results_dir / "collinearity_diagnostics.json"
    output_path = results_dir / "associational_findings_report.md"
    
    try:
        # Load metrics
        print(f"Loading metrics from {metrics_path}...")
        metrics_data = load_json_file(metrics_path)
        
        # Load SHAP analysis
        print(f"Loading SHAP analysis from {shap_path}...")
        shap_data = load_json_file(shap_path)
        
        # Load collinearity diagnostics (optional)
        collinearity_data = None
        if os.path.exists(collinearity_path):
            print(f"Loading collinearity diagnostics from {collinearity_path}...")
            collinearity_data = load_json_file(collinearity_path)
        
        # Generate report
        print("Generating associational report...")
        report_content = generate_associational_report(metrics_data, shap_data, collinearity_data)
        
        # Write report
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        print(f"Report successfully written to: {output_path}")
        
        # Verify the report contains the required disclaimer
        if "ASSOCIATIONAL" in report_content and "CAUSATION" in report_content:
            print("Verification passed: Report contains required associational framing.")
        else:
            print("WARNING: Report may be missing required associational framing.")
            
    except FileNotFoundError as e:
        print(f"Error: Missing required input files. {e}")
        print("Ensure the modeling pipeline (T021, T022) has run successfully first.")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
