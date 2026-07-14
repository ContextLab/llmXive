import os
import sys
import json
import logging
from typing import Dict, Any, Optional

from utils.logging import get_logger
from utils.report_utils import inject_disclaimer, finalize_report_markdown

logger = get_logger(__name__)

def load_metrics(path: str) -> Dict[str, Any]:
    """Load the metrics JSON file."""
    if not os.path.exists(path):
        logger.error(f"Metrics file not found: {path}")
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def load_power_analysis(path: str) -> Dict[str, Any]:
    """Load the power analysis JSON file."""
    if not os.path.exists(path):
        logger.error(f"Power analysis file not found: {path}")
        return {"status": "unknown"}
    with open(path, 'r') as f:
        return json.load(f)

def load_vif_results(path: str) -> Dict[str, Any]:
    """
    Load VIF results.
    Note: Depending on T023 implementation, this might be part of metrics or a separate file.
    We assume a standard location or structure for flexibility.
    """
    # T023 writes VIF to output/vif_results.json or similar.
    # If it's embedded in metrics, we extract it.
    # For this implementation, we look for a dedicated file or fallback to metrics.
    dedicated_path = path.replace("metrics.json", "vif_results.json")
    if os.path.exists(dedicated_path):
        with open(dedicated_path, 'r') as f:
            return json.load(f)
    
    # Fallback: Check if metrics contains VIF data (unlikely based on T023 spec but possible)
    metrics = load_metrics(path)
    if "vif" in metrics:
        return metrics["vif"]
    
    return {}

def load_permutation_results(path: str) -> Dict[str, Any]:
    """Load permutation importance results."""
    dedicated_path = path.replace("metrics.json", "permutation_results.json")
    if os.path.exists(dedicated_path):
        with open(dedicated_path, 'r') as f:
            return json.load(f)
    return {}

def load_bootstrap_results(path: str) -> Dict[str, Any]:
    """Load bootstrap resampling results."""
    dedicated_path = path.replace("metrics.json", "bootstrap_results.json")
    if os.path.exists(dedicated_path):
        with open(dedicated_path, 'r') as f:
            return json.load(f)
    return {}

def load_sensitivity_results(path: str) -> Dict[str, Any]:
    """Load sensitivity analysis results."""
    dedicated_path = path.replace("metrics.json", "sensitivity_results.json")
    if os.path.exists(dedicated_path):
        with open(dedicated_path, 'r') as f:
            return json.load(f)
    return {}

def generate_report_content(
    metrics: Dict[str, Any],
    power_analysis: Dict[str, Any],
    vif_results: Dict[str, Any],
    perm_results: Dict[str, Any],
    boot_results: Dict[str, Any],
    sens_results: Dict[str, Any]
) -> str:
    """
    Generate the raw markdown content for the statistical report.
    Integrates all results from T023-T027.
    """
    lines = []
    lines.append("# Statistical Validation Report: HEA Yield Strength Prediction")
    lines.append("")
    
    # 1. Executive Summary & Power Status
    lines.append("## 1. Executive Summary")
    lines.append("")
    status = power_analysis.get("status", "unknown")
    lines.append(f"**Sample Size Status**: {status}")
    if status == "insufficient_power":
        lines.append(f"> **Warning**: The dataset size (N={power_analysis.get('n', 'N/A')}) is insufficient for robust statistical inference (N < 50).")
    lines.append("")

    # 2. Model Performance Metrics
    lines.append("## 2. Model Performance Metrics")
    lines.append("")
    lines.append("| Model | R² | MAE (MPa) | RMSE (MPa) |")
    lines.append("| :--- | :--- | :--- | :--- |")
    
    model_metrics = metrics.get("models", metrics) # Handle both nested and flat structures
    for model_name, data in model_metrics.items():
        if isinstance(data, dict):
            r2 = data.get("r2", "N/A")
            mae = data.get("mae", "N/A")
            rmse = data.get("rmse", "N/A")
            lines.append(f"| {model_name} | {r2} | {mae} | {rmse} |")
    lines.append("")

    # 3. Multicollinearity (VIF) - Linear Baseline Only
    lines.append("## 3. Multicollinearity Analysis (VIF)")
    lines.append("")
    lines.append("Variance Inflation Factors (VIF) calculated for the Linear Regression baseline descriptors.")
    lines.append("A VIF > 10 indicates severe multicollinearity.")
    lines.append("")
    
    if not vif_results:
        lines.append("*No VIF results available.*")
    else:
        lines.append("| Descriptor | VIF | Flag (>10) |")
        lines.append("| :--- | :--- | :--- |")
        for desc, val in vif_results.items():
            flag = "⚠️ HIGH" if val > 10 else "OK"
            lines.append(f"| {desc} | {val:.2f} | {flag} |")
    lines.append("")

    # 4. Permutation Importance & Significance
    lines.append("## 4. Permutation Importance & Significance")
    lines.append("")
    
    if status == "insufficient_power":
        lines.append("> **Skipped**: Permutation testing was skipped due to insufficient sample size (N < 50).")
    else:
        lines.append("P-values derived from 1000 permutations. Significance corrected via Bonferroni/Holm-Bonferroni.")
        lines.append("")
        
        if not perm_results:
            lines.append("*No permutation results available.*")
        else:
            lines.append("| Descriptor | Permutation Importance | Raw P-value | Corrected P-value | Significant? |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            
            # Assuming structure: list of dicts or dict of dicts
            items = perm_results if isinstance(perm_results, list) else [perm_results]
            for item in items:
                desc = item.get("descriptor", "Unknown")
                imp = item.get("importance", "N/A")
                raw_p = item.get("p_value", "N/A")
                corr_p = item.get("corrected_p_value", "N/A")
                sig = "Yes" if item.get("is_significant", False) else "No"
                lines.append(f"| {desc} | {imp} | {raw_p} | {corr_p} | {sig} |")
    lines.append("")

    # 5. Bootstrap Confidence Intervals
    lines.append("## 5. Bootstrap Resampling (95% CI)")
    lines.append("")
    
    if status == "insufficient_power":
        lines.append("> **Skipped**: Bootstrap resampling was skipped due to insufficient sample size (N < 50).")
    else:
        lines.append("95% Confidence Intervals for R² based on 1000 resamples.")
        lines.append("")
        
        if not boot_results:
            lines.append("*No bootstrap results available.*")
        else:
            lines.append("| Model | Mean R² | 95% CI Lower | 95% CI Upper |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for model_name, data in boot_results.items():
                if isinstance(data, dict):
                    mean_r2 = data.get("mean_r2", "N/A")
                    ci_low = data.get("ci_lower", "N/A")
                    ci_high = data.get("ci_upper", "N/A")
                    lines.append(f"| {model_name} | {mean_r2} | {ci_low} | {ci_high} |")
    lines.append("")

    # 6. Sensitivity Analysis
    lines.append("## 6. Sensitivity Analysis (Alpha Sweep)")
    lines.append("")
    lines.append("Impact of varying significance threshold (α) on descriptor count and model performance.")
    lines.append("")
    
    if not sens_results:
        lines.append("*No sensitivity results available.*")
    else:
        lines.append("| Alpha (α) | Significant Descriptors | R² (Best Model) |")
        lines.append("| :--- | :--- | :--- |")
        for alpha_val, data in sens_results.items():
            if isinstance(data, dict):
                count = data.get("significant_count", "N/A")
                r2 = data.get("best_r2", "N/A")
                lines.append(f"| {alpha_val} | {count} | {r2} |")
    lines.append("")

    # 7. Conclusions
    lines.append("## 7. Conclusions")
    lines.append("")
    lines.append("This report summarizes the statistical validation of the HEA yield strength prediction models.")
    lines.append("Key findings include the performance metrics, descriptor stability (VIF), and significance of compositional features.")
    lines.append("")

    return "\n".join(lines)

def main():
    """Main entry point to generate the statistical report."""
    logger.info("Starting statistical report generation (T028)...")
    
    # Define paths based on project structure
    base_output_dir = "output"
    metrics_path = os.path.join(base_output_dir, "metrics.json")
    power_path = os.path.join(base_output_dir, "power_analysis.json")
    report_path = os.path.join(base_output_dir, "report.md")
    
    # Load all necessary data artifacts
    metrics = load_metrics(metrics_path)
    power_analysis = load_power_analysis(power_path)
    vif_results = load_vif_results(metrics_path)
    perm_results = load_permutation_results(metrics_path)
    boot_results = load_bootstrap_results(metrics_path)
    sens_results = load_sensitivity_results(metrics_path)
    
    # Generate raw content
    raw_content = generate_report_content(
        metrics, power_analysis, vif_results, perm_results, boot_results, sens_results
    )
    
    # Inject mandatory disclaimers using T029b utility
    final_content = inject_disclaimer(raw_content)
    final_content = finalize_report_markdown(final_content)
    
    # Ensure output directory exists
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Write the report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    logger.info(f"Statistical report successfully generated at: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
