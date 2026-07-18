"""
T044: Generate the final `docs/final_report.md` by aggregating results from
data artifacts produced in the pipeline execution and model fitting stages.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Import helper from existing report module if needed, or define locally
# The API surface shows `from evaluation.report import ...` but we are creating a new file
# We will define local helpers to ensure independence and clarity.

def load_json_safe(filepath: str) -> dict:
    """Load JSON file, return empty dict if missing or invalid."""
    path = Path(filepath)
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def load_gate_validation() -> dict:
    return load_json_safe("data/gate_validation_report.json")

def load_sensitivity_analysis() -> dict:
    return load_json_safe("data/auc_delta_metrics.json") # Using AUC delta as proxy for sensitivity

def load_power_analysis() -> dict:
    return load_json_safe("data/power_analysis.json")

def load_vif_test_set() -> dict:
    # T047 output might be in vif_scores_initial or a specific test set file
    # Based on T047 description, it flags instability. We check initial VIF.
    return load_json_safe("data/vif_scores_initial.json")

def load_calibration_results() -> dict:
    return load_json_safe("data/calibration_test_results.json")

def load_auc_delta() -> dict:
    return load_json_safe("data/auc_delta_metrics.json")

def load_bayesian_convergence() -> dict:
    return load_json_safe("data/bayesian_convergence_log.json")

def load_lrt_vif_corrected() -> dict:
    return load_json_safe("data/lrt_result_vif_corrected.json")

def load_final_validation_report() -> dict:
    return load_json_safe("data/final_validation_report.json")

def generate_constitution_compliance_section(gate_data: dict, bayesian_data: dict, vif_data: dict, cal_data: dict) -> str:
    """Generate Constitution Compliance section."""
    lines = []
    lines.append("### Constitution Compliance")
    lines.append("")
    
    # Check Gate
    gate_passed = gate_data.get("status") == "PASS"
    lines.append(f"- **Gate Validation**: {'✅ PASSED' if gate_passed else '❌ FAILED'}")
    
    # Bayesian Convergence
    bayes_status = bayesian_data.get("status", "UNKNOWN")
    lines.append(f"- **Bayesian Convergence**: {'✅ SUCCESS' if bayes_status == 'SUCCESS' else '❌ FAILED/UNKNOWN'}")
    
    # Calibration
    cal_passed = cal_data.get("passed", False)
    lines.append(f"- **Calibration Test**: {'✅ PASSED' if cal_passed else '❌ FAILED'}")
    
    # VIF Stability
    max_vif = vif_data.get("max_vif", 0)
    vif_stable = max_vif <= 5.0
    lines.append(f"- **VIF Stability (Max VIF: {max_vif:.2f})**: {'✅ STABLE' if vif_stable else '⚠️ UNSTABLE (>5)'}")
    
    lines.append("")
    lines.append("All mandatory gates (II, IV, VI) were evaluated against the final artifacts.")
    return "\n".join(lines)

def generate_limitations_section(vif_data: dict, power_data: dict, cal_data: dict) -> str:
    """Generate Limitations section."""
    lines = []
    lines.append("### Limitations")
    lines.append("")
    
    # VIF
    max_vif = vif_data.get("max_vif", 0)
    if max_vif > 5.0:
        lines.append(f"- **Multicollinearity**: The VIF analysis detected a maximum VIF of {max_vif:.2f}, indicating potential multicollinearity among predictors. This may affect the interpretability of individual coefficients.")
    else:
        lines.append("- **Multicollinearity**: VIF scores were within acceptable limits (<= 5), suggesting no severe multicollinearity.")

    # Power
    achieved_power = power_data.get("achieved_power", "N/A")
    lines.append(f"- **Statistical Power**: The achieved power for the effect size was estimated at {achieved_power}. If below 0.8, the study may be underpowered to detect small effects.")

    # Calibration
    if not cal_data.get("passed", False):
        max_dev = cal_data.get("max_deviation", "N/A")
        lines.append(f"- **Calibration**: The model probabilities showed a maximum deviation of {max_dev} from observed frequencies, exceeding the tolerance threshold. Probabilities should be interpreted with caution.")
    else:
        lines.append("- **Calibration**: The model probabilities were well-calibrated within the defined tolerance.")

    lines.append("")
    return "\n".join(lines)

def generate_results_section(lrt_data: dict, auc_data: dict, vif_data: dict) -> str:
    """Generate Results section."""
    lines = []
    lines.append("### Results")
    lines.append("")
    
    # LRT
    lrt_p = lrt_data.get("p_value", 0)
    lrt_sig = "significant" if lrt_p < 0.05 else "not significant"
    lines.append(f"- **Likelihood-Ratio Test**: The full model showed a {lrt_sig} improvement over the null model (p = {lrt_p:.4f}).")
    
    # AUC Delta
    auc_full = auc_data.get("auc_full", 0)
    auc_base = auc_data.get("auc_baseline", 0)
    delta = auc_data.get("delta", 0)
    ci = auc_data.get("ci_95", [0, 0])
    p_val = auc_data.get("p_value", 1)
    
    lines.append(f"- **AUC Delta**: The full model achieved an AUC of {auc_full:.4f} compared to the baseline {auc_base:.4f} (Δ = {delta:.4f}).")
    lines.append(f"  - 95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]")
    lines.append(f"  - Statistical Significance: p = {p_val:.4f}")
    
    # VIF
    max_vif = vif_data.get("max_vif", 0)
    lines.append(f"- **Multicollinearity (VIF)**: Maximum VIF observed was {max_vif:.2f}.")
    
    lines.append("")
    return "\n".join(lines)

def generate_executive_summary(lrt_data: dict, auc_data: dict) -> str:
    """Generate Executive Summary."""
    lines = []
    lines.append("## Executive Summary")
    lines.append("")
    
    hypothesis_supported = False
    if lrt_data.get("p_value", 1) < 0.05 and auc_data.get("delta", 0) > 0.05:
        hypothesis_supported = True
    
    if hypothesis_supported:
        lines.append("The analysis **supports** the hypothesis that flavor and functional role predict ingredient compatibility beyond mere co-occurrence frequency.")
    else:
        lines.append("The analysis **does not support** the hypothesis that flavor and functional role predict ingredient compatibility beyond mere co-occurrence frequency.")
        
    lines.append("")
    lines.append("Key findings:")
    lines.append(f"- Likelihood-Ratio Test p-value: {lrt_data.get('p_value', 0):.4f}")
    lines.append(f"- AUC Improvement (Delta): {auc_data.get('delta', 0):.4f}")
    lines.append("")
    return "\n".join(lines)

def generate_methodology_section(power_data: dict) -> str:
    """Generate Methodology section."""
    lines = []
    lines.append("## Methodology")
    lines.append("")
    lines.append("This study utilized a two-stage modeling approach:")
    lines.append("1.  **Data Preprocessing**: Ingredient names were normalized using Levenshtein distance (threshold=2) against the FlavorDB canonical list. Co-occurrence matrices were constructed via streaming, and functional roles were derived via orthogonalization.")
    lines.append("2.  **Model Fitting**: A regularized Logistic Regression (L2) and a Hierarchical Bayesian model were fitted to predict compatibility labels.")
    lines.append("3.  **Validation**: Model performance was evaluated using AUC, Likelihood-Ratio Tests, and Bootstrap permutation tests for AUC delta significance.")
    lines.append(f"- **Sample Size**: Target N determined by power analysis: {power_data.get('N_unified', 'N/A')}")
    lines.append("")
    return "\n".join(lines)

def main():
    """Main entry point for T044."""
    print("Generating Final Report (T044)...")
    
    # Load all dependencies
    gate_data = load_gate_validation()
    sensitivity_data = load_sensitivity_analysis()
    power_data = load_power_analysis()
    vif_data = load_vif_test_set()
    cal_data = load_calibration_results()
    auc_data = load_auc_delta()
    bayes_data = load_bayesian_convergence()
    lrt_data = load_lrt_vif_corrected()
    final_val_data = load_final_validation_report()
    
    # Generate sections
    sections = []
    sections.append("# Final Report: Statistical Analysis of Recipe Data")
    sections.append(f"*Generated: {datetime.now().isoformat()}*")
    sections.append("")
    
    sections.append(generate_executive_summary(lrt_data, auc_data))
    sections.append(generate_methodology_section(power_data))
    sections.append(generate_results_section(lrt_data, auc_data, vif_data))
    sections.append(generate_constitution_compliance_section(gate_data, bayes_data, vif_data, cal_data))
    sections.append(generate_limitations_section(vif_data, power_data, cal_data))
    
    # Conclusion
    sections.append("## Conclusion")
    sections.append("")
    if lrt_data.get("p_value", 1) < 0.05:
        sections.append("The statistical evidence indicates that incorporating flavor similarity and functional role significantly improves the prediction of ingredient compatibility compared to a frequency-only baseline.")
    else:
        sections.append("The statistical evidence does not indicate a significant improvement in prediction accuracy when incorporating flavor and role features over the frequency baseline.")
    sections.append("")
    
    # Write to file
    output_path = Path("docs/final_report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = "\n".join(sections)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Final report generated at: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
