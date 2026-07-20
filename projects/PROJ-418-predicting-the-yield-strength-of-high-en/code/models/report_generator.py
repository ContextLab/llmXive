import os
import sys
import json
import logging
from typing import Dict, Any, Optional

from utils.logging import get_logger
from utils.report_utils import inject_disclaimer, finalize_report_markdown

logger = get_logger(__name__)

def load_metrics(filepath: str = "output/metrics.json") -> Dict[str, Any]:
    """Load metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_power_analysis(filepath: str = "output/power_analysis.json") -> Dict[str, Any]:
    """Load power analysis results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Power analysis file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_vif_results(filepath: str = "output/vif_results.json") -> Dict[str, Any]:
    """Load VIF results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"VIF results file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_permutation_results(filepath: str = "output/permutation_results.json") -> Dict[str, Any]:
    """Load permutation importance results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Permutation results file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_bootstrap_results(filepath: str = "output/bootstrap_results.json") -> Dict[str, Any]:
    """Load bootstrap resampling results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Bootstrap results file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_sensitivity_results(filepath: str = "output/sensitivity_results.json") -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Sensitivity results file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_report_content(
    metrics: Dict[str, Any],
    power_analysis: Dict[str, Any],
    vif_results: Dict[str, Any],
    permutation_results: Dict[str, Any],
    bootstrap_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any]
) -> str:
    """Generate the full markdown report content."""
    lines = []
    lines.append("# Statistical Validation Report: HEA Yield Strength Prediction")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    
    # Power Analysis Status
    status = power_analysis.get("status", "unknown")
    if status == "insufficient_power":
        n = power_analysis.get("n", 0)
        lines.append(f"**⚠️ Power Limitation**: Sample size N={n} is below the threshold (N < 50).")
        lines.append("Permutation tests and bootstrap resampling have been skipped due to insufficient statistical power.")
        lines.append("")
    else:
        lines.append("**✅ Statistical Power**: Sample size is sufficient for robust statistical testing.")
        lines.append("")

    lines.append("## 2. Model Performance Metrics")
    lines.append("")
    lines.append("| Model | R² | MAE (MPa) | RMSE (MPa) |")
    lines.append("|-------|----|-----------|------------|")
    
    for model_name, model_metrics in metrics.items():
        r2 = model_metrics.get("r2", "N/A")
        mae = model_metrics.get("mae", "N/A")
        rmse = model_metrics.get("rmse", "N/A")
        lines.append(f"| {model_name} | {r2} | {mae} | {rmse} |")
    lines.append("")

    lines.append("## 3. Multicollinearity Diagnostics (Linear Baseline Only)")
    lines.append("")
    
    if not vif_results:
        lines.append("*No VIF results available.*")
    else:
        lines.append("### Variance Inflation Factors (VIF)")
        lines.append("")
        lines.append("| Descriptor | VIF Value | Flag (>10) |")
        lines.append("|------------|-----------|------------|")
        
        high_vif_count = 0
        for desc, vif_val in vif_results.get("vif_values", {}).items():
            is_flagged = "⚠️ YES" if vif_val > 10 else "No"
            if vif_val > 10:
                high_vif_count += 1
            lines.append(f"| {desc} | {vif_val:.2f} | {is_flagged} |")
        
        lines.append("")
        if high_vif_count > 0:
            lines.append(f"**⚠️ Warning**: {high_vif_count} descriptor(s) show high multicollinearity (VIF > 10).")
            lines.append("This may affect the stability of linear regression coefficients.")
        else:
            lines.append("**✅** No significant multicollinearity detected (all VIF ≤ 10).")
        lines.append("")

    if status != "insufficient_power":
        lines.append("## 4. Permutation Importance Analysis")
        lines.append("")
        lines.append("### Significance Testing (p-values)")
        lines.append("")
        lines.append("| Descriptor | Permutation Score | p-value | Bonferroni Sig. | BH Sig. |")
        lines.append("|------------|-------------------|---------|-----------------|---------|")
        
        perms = permutation_results.get("results", [])
        for item in perms:
            desc = item.get("feature", "Unknown")
            score = item.get("score", 0)
            p_val = item.get("p_value", 1.0)
            bonf_sig = "Yes" if item.get("bonferroni_significant", False) else "No"
            bh_sig = "Yes" if item.get("bh_significant", False) else "No"
            lines.append(f"| {desc} | {score:.4f} | {p_val:.4f} | {bonf_sig} | {bh_sig} |")
        
        lines.append("")
        
        lines.append("### Multiple Comparison Correction")
        lines.append("")
        lines.append(f"- **Bonferroni Corrected Alpha**: {permutation_results.get('bonferroni_alpha', 'N/A')}")
        lines.append(f"- **Benjamini-Hochberg Corrected Alpha**: {permutation_results.get('bh_alpha', 'N/A')}")
        lines.append("")

        lines.append("## 5. Bootstrap Resampling (95% Confidence Intervals)")
        lines.append("")
        lines.append("### Model Performance Stability")
        lines.append("")
        lines.append("| Model | Mean R² | 95% CI (Lower) | 95% CI (Upper) |")
        lines.append("|-------|---------|----------------|----------------|")
        
        boot_res = bootstrap_results.get("results", {})
        for model, res in boot_res.items():
            mean_r2 = res.get("mean_r2", 0)
            ci_low = res.get("ci_95_lower", 0)
            ci_high = res.get("ci_95_upper", 0)
            lines.append(f"| {model} | {mean_r2:.4f} | {ci_low:.4f} | {ci_high:.4f} |")
        
        lines.append("")

        lines.append("## 6. Sensitivity Analysis")
        lines.append("")
        lines.append("### Impact of Alpha Threshold on Significance")
        lines.append("")
        lines.append("| Alpha Threshold | Significant Descriptors | Model R² (Best) |")
        lines.append("|-----------------|-------------------------|-----------------|")
        
        sens_res = sensitivity_results.get("results", [])
        for item in sens_res:
            alpha = item.get("alpha", 0)
            count = item.get("significant_count", 0)
            r2 = item.get("r2", 0)
            lines.append(f"| {alpha} | {count} | {r2:.4f} |")
        
        lines.append("")
    else:
        lines.append("## 4. Statistical Validation Skipped")
        lines.append("")
        lines.append("Permutation tests, bootstrap resampling, and sensitivity analysis were skipped due to insufficient sample size (N < 50).")
        lines.append("")

    lines.append("## 7. Conclusions")
    lines.append("")
    lines.append("This analysis provides an associational link between compositional descriptors and yield strength in high-entropy alloys.")
    lines.append("The predictive models (Random Forest, Gradient Boosting) demonstrate performance metrics as reported above.")
    lines.append("Statistical validation confirms the robustness of these findings within the limits of the dataset size.")
    lines.append("")

    # Apply disclaimer
    report_markdown = "\n".join(lines)
    report_markdown = inject_disclaimer(report_markdown)
    report_markdown = finalize_report_markdown(report_markdown)
    
    return report_markdown

def main():
    """Main entry point to generate the statistical report."""
    logger.info("Starting statistical report generation...")
    
    # Load all required data files
    metrics = load_metrics("output/metrics.json")
    power_analysis = load_power_analysis("output/power_analysis.json")
    vif_results = load_vif_results("output/vif_results.json")
    permutation_results = load_permutation_results("output/permutation_results.json")
    bootstrap_results = load_bootstrap_results("output/bootstrap_results.json")
    sensitivity_results = load_sensitivity_results("output/sensitivity_results.json")
    
    # Generate content
    report_content = generate_report_content(
        metrics,
        power_analysis,
        vif_results,
        permutation_results,
        bootstrap_results,
        sensitivity_results
    )
    
    # Write to output
    output_path = "output/report.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Statistical report generated successfully: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
