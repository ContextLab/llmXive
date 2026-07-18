import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from evaluation.report import (
    load_metrics_from_disk,
    load_vif_results,
    load_lrt_results,
    map_lrt_to_sc001,
    map_vif_to_sc003,
    run_sensitivity_analysis
)
from data.verify import verify_data_sources
from models.diagnostics import post_hoc_power_validation

def load_json_safe(path: Path) -> dict:
    """Load JSON file safely, returning empty dict if missing."""
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def load_gate_validation(path: Path) -> dict:
    """Load the gate validation report from T056."""
    return load_json_safe(path)

def load_sensitivity_analysis(path: Path) -> dict:
    """Load sensitivity analysis results from T048."""
    return load_json_safe(path)

def load_power_analysis(path: Path) -> dict:
    """Load power analysis results."""
    return load_json_safe(path)

def load_vif_test_set(path: Path) -> dict:
    """Load VIF test set results from T053."""
    return load_json_safe(path)

def load_calibration_results(path: Path) -> dict:
    """Load calibration test results from T054."""
    return load_json_safe(path)

def load_auc_delta(path: Path) -> dict:
    """Load AUC delta metrics from T030."""
    return load_json_safe(path)

def load_bayesian_convergence(path: Path) -> dict:
    """Load Bayesian convergence log from T025."""
    return load_json_safe(path)

def load_lrt_vif_corrected(path: Path) -> dict:
    """Load LRT results with VIF correction from T040."""
    return load_json_safe(path)

def load_final_validation_report(path: Path) -> dict:
    """Load the final validation report from T043d."""
    return load_json_safe(path)

def generate_constitution_compliance_section(gate_report: dict, bayesian_log: dict, calibration_log: dict, vif_initial: dict) -> str:
    """Generate the Constitution Compliance section based on T056 gates."""
    lines = []
    lines.append("## Constitution Compliance")
    lines.append("")
    lines.append("This section verifies that all execution gates (Constitution Principles II, IV, VI) have been satisfied.")
    lines.append("")

    # Gate II: Verified Accuracy (Data Verification)
    verification_passed = gate_report.get("checks", {}).get("verification", False)
    lines.append(f"**Gate II (Verified Accuracy):** {'PASSED' if verification_passed else 'FAILED'}")
    if not verification_passed:
        lines.append("- Data source verification failed. The pipeline did not confirm the integrity of the raw data sources.")
    lines.append("")

    # Gate IV: Single Source of Truth (Bayesian Convergence)
    bayesian_passed = gate_report.get("checks", {}).get("bayesian", False)
    lines.append(f"**Gate IV (Single Source of Truth / Convergence):** {'PASSED' if bayesian_passed else 'FAILED'}")
    if not bayesian_passed:
        lines.append("- Bayesian model convergence checks failed (R-hat > 1.05 or ESS < 200). Results may be unreliable.")
    lines.append("")

    # Gate VI: Statistical Independence (Calibration & VIF)
    calibration_passed = gate_report.get("checks", {}).get("calibration", False)
    vif_exists = gate_report.get("checks", {}).get("vif", False)
    lines.append(f"**Gate VI (Statistical Independence):** {'PASSED' if (calibration_passed and vif_exists) else 'FAILED'}")
    if not calibration_passed:
        lines.append("- Calibration test failed. Model probability estimates deviate significantly from observed frequencies.")
    if not vif_exists:
        lines.append("- VIF scores missing or indicate multicollinearity issues.")
    lines.append("")

    # Specific VIF Stability Check (T053)
    vif_test_set = load_vif_test_set(Path("data/vif_test_set_scores.json"))
    if vif_test_set:
        max_test_vif = vif_test_set.get("max_vif", 0)
        if max_test_vif > 5:
            lines.append(f"**Warning:** Out-of-sample VIF check (T053) detected multicollinearity on the test set (Max VIF: {max_test_vif:.2f}).")
            lines.append("This suggests predictor independence may not hold for unseen data, potentially affecting generalization.")
    lines.append("")

    return "\n".join(lines)

def generate_limitations_section(sensitivity_results: dict, vif_test_set: dict, power_analysis: dict) -> str:
    """Generate the Limitations section."""
    lines = []
    lines.append("## Limitations")
    lines.append("")
    
    # Sensitivity Analysis Limitations
    if sensitivity_results:
        lines.append("### Sensitivity Analysis Findings")
        if sensitivity_results.get("auc_delta_variance", 0) > 0.01:
            lines.append("- **Preprocessing Sensitivity:** The AUC delta shows high variance across different imputation and binning strategies.")
            lines.append("  This indicates that the model's performance gain is sensitive to specific data cleaning choices.")
        else:
            lines.append("- **Robustness:** The model performance appears robust to variations in imputation and role binning strategies.")
        lines.append("")

    # VIF Stability Limitations
    if vif_test_set and vif_test_set.get("max_vif", 0) > 5:
        lines.append("### Multicollinearity on Test Set")
        lines.append(f"- The 'Functional Role' predictor exhibited VIF > 5 on the held-out test set (Max VIF: {vif_test_set.get('max_vif', 0):.2f}).")
        lines.append("  While the training set passed, this suggests the correlation structure between predictors may differ in the population,")
        lines.append("  potentially inflating standard errors for role coefficients in future applications.")
        lines.append("")

    # Power Analysis Limitations
    if power_analysis:
        achieved_power = power_analysis.get("achieved_power", 0)
        if achieved_power < 0.8:
            lines.append("### Statistical Power")
            lines.append(f"- The post-hoc power analysis indicates an achieved power of {achieved_power:.2f}, which is below the target of 0.80.")
            lines.append("  This suggests the sample size may be insufficient to reliably detect effect sizes of 0.1 for smaller effects.")
            lines.append("")

    # Data Source Limitations (General)
    lines.append("### Data Source Constraints")
    lines.append("- The analysis is limited to the Recipe1M and FlavorDB datasets. Ingredients not present in FlavorDB's chemical vector space")
    lines.append("  were excluded, potentially biasing the sample towards common, well-studied ingredients.")
    lines.append("- Streaming constraints limited the depth of co-occurrence analysis to a sampled subset of the full Recipe1M corpus.")
    lines.append("")

    return "\n".join(lines)

def generate_results_section(lrt_results: dict, vif_initial: dict, auc_delta: dict, calibration_log: dict, bayesian_log: dict) -> str:
    """Generate the Results section."""
    lines = []
    lines.append("## Results")
    lines.append("")

    # Likelihood Ratio Test
    lines.append("### Likelihood Ratio Test (LRT)")
    if lrt_results:
        p_value = lrt_results.get("p_value", 0)
        significant = p_value < 0.05
        lines.append(f"- **P-value:** {p_value:.4f}")
        lines.append(f"- **Conclusion:** {'Significant' if significant else 'Not Significant'} (p < 0.05)")
        lines.append(f"- **Interpretation:** The full model (frequency + flavor + role) provides a statistically {'significant' if significant else 'non-significant'} improvement over the null model (frequency only).")
    else:
        lines.append("- LRT results unavailable.")
    lines.append("")

    # VIF Scores
    lines.append("### Multicollinearity (VIF)")
    if vif_initial:
        predictors = vif_initial.get("predictors", {})
        max_vif = vif_initial.get("max_vif", 0)
        lines.append(f"- **Maximum VIF:** {max_vif:.2f}")
        if max_vif > 5:
            lines.append("- **Status:** Flagged. High multicollinearity detected.")
        else:
            lines.append("- **Status:** Acceptable. No severe multicollinearity detected.")
        lines.append("- **Predictor VIFs:**")
        for name, score in predictors.items():
            lines.append(f"  - {name}: {score:.2f}")
    else:
        lines.append("- VIF scores unavailable.")
    lines.append("")

    # AUC Delta
    lines.append("### Model Comparison (AUC Delta)")
    if auc_delta:
        delta = auc_delta.get("delta", 0)
        ci = auc_delta.get("ci_95", [0, 0])
        p_val = auc_delta.get("p_value", 1)
        lines.append(f"- **Delta AUC:** {delta:.4f} (95% CI: [{ci[0]:.4f}, {ci[1]:.4f}])")
        lines.append(f"- **Bootstrap P-value:** {p_val:.4f}")
        lines.append(f"- **Threshold:** 0.05")
        if delta >= 0.05 and p_val < 0.05:
            lines.append("- **Conclusion:** The full model demonstrates a meaningful and statistically significant improvement over the baseline.")
        else:
            lines.append("- **Conclusion:** The full model does not demonstrate a meaningful improvement over the baseline.")
    else:
        lines.append("- AUC delta metrics unavailable.")
    lines.append("")

    # Calibration
    lines.append("### Calibration")
    if calibration_log:
        passed = calibration_log.get("passed", False)
        max_dev = calibration_log.get("max_deviation", 0)
        lines.append(f"- **Status:** {'PASSED' if passed else 'FAILED'}")
        lines.append(f"- **Max Deviation:** {max_dev:.4f}")
        if not passed:
            lines.append("- **Warning:** Probability estimates are not well-calibrated.")
    else:
        lines.append("- Calibration results unavailable.")
    lines.append("")

    # Bayesian Convergence
    lines.append("### Bayesian Model Convergence")
    if bayesian_log:
        status = bayesian_log.get("status", "UNKNOWN")
        lines.append(f"- **Status:** {status}")
        if status == "SUCCESS":
            lines.append("- The hierarchical Bayesian model converged successfully.")
        else:
            lines.append("- **Warning:** The hierarchical Bayesian model failed convergence checks.")
    else:
        lines.append("- Bayesian convergence log unavailable.")
    lines.append("")

    return "\n".join(lines)

def generate_executive_summary(lrt_results: dict, auc_delta: dict, gate_report: dict) -> str:
    """Generate the Executive Summary."""
    lines = []
    lines.append("# Final Report: Statistical Analysis of Recipe Data for Ingredient Substitution")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    
    hypothesis_supported = False
    if lrt_results and lrt_results.get("p_value", 1) < 0.05:
        if auc_delta and auc_delta.get("delta", 0) >= 0.05 and auc_delta.get("p_value", 1) < 0.05:
            hypothesis_supported = True

    lines.append("This report evaluates the hypothesis that **flavor and functional role predict ingredient compatibility beyond mere co-occurrence frequency**.")
    lines.append("")
    
    if hypothesis_supported:
        lines.append("### Conclusion: Hypothesis Supported")
        lines.append("The analysis provides statistical evidence that incorporating flavor similarity and functional role significantly improves the prediction of ingredient compatibility.")
        lines.append("The full model outperforms the frequency-only baseline with a meaningful AUC delta and statistically significant Likelihood Ratio Test results.")
    else:
        lines.append("### Conclusion: Hypothesis Not Supported")
        lines.append("The analysis did not find sufficient evidence to support the hypothesis. The full model did not demonstrate a statistically significant or meaningful improvement over the baseline.")
    
    lines.append("")
    lines.append("### Key Findings")
    if lrt_results:
        lines.append(f"- **LRT P-value:** {lrt_results.get('p_value', 'N/A')}")
    if auc_delta:
        lines.append(f"- **AUC Delta:** {auc_delta.get('delta', 'N/A')}")
    if gate_report:
        status = "All Gates Passed" if gate_report.get("status") == "PASS" else "Gates Failed"
        lines.append(f"- **Execution Gates:** {status}")
    
    lines.append("")
    return "\n".join(lines)

def generate_methodology_section() -> str:
    """Generate the Methodology section."""
    lines = []
    lines.append("## Methodology")
    lines.append("")
    lines.append("### Data Acquisition")
    lines.append("- **Source:** Recipe1M (streamed), FlavorDB (chemical vectors), Counterfactual dataset.")
    lines.append("- **Preprocessing:** Ingredient names normalized using Levenshtein distance (threshold=2) against FlavorDB canonical list.")
    lines.append("- **Feature Engineering:**")
    lines.append("  - **Co-occurrence:** Log-transformed co-occurrence matrix ($\\log(C_{ij} + \\epsilon)$).")
    lines.append("  - **Flavor Similarity:** Cosine similarity of chemical vectors from FlavorDB.")
    lines.append("  - **Functional Role:** Orthogonalized positional rank (residuals of rank vs. log-frequency), discretized into Primary/Secondary/Garnish.")
    lines.append("")
    lines.append("### Statistical Modeling")
    lines.append("- **Models:** Regularized Logistic Regression (L2) and Hierarchical Bayesian Model (NUTS).")
    lines.append("- **Validation:** Train/Test split (seed=42), downsampling to unified power analysis size ($N \\approx 10,000$).")
    lines.append("- **Diagnostics:** Variance Inflation Factor (VIF), Likelihood Ratio Test (LRT), Calibration curves, Bootstrap AUC delta test.")
    lines.append("")
    return "\n".join(lines)

def main():
    """Generate the definitive final report."""
    print("Generating Final Report (T057)...")
    
    # Define paths
    gate_path = Path("data/gate_validation_report.json")
    lrt_path = Path("data/lrt_result_vif_corrected.json")
    vif_path = Path("data/vif_scores_initial.json")
    vif_test_path = Path("data/vif_test_set_scores.json")
    auc_delta_path = Path("data/auc_delta_metrics.json")
    calibration_path = Path("data/calibration_test_results.json")
    bayesian_path = Path("data/bayesian_convergence_log.json")
    sensitivity_path = Path("data/sensitivity_analysis_results.json")
    power_path = Path("data/power_analysis.json")
    validation_path = Path("data/final_validation_report.json")
    
    # Load artifacts
    gate_report = load_gate_validation(gate_path)
    lrt_results = load_lrt_vif_corrected(lrt_path)
    vif_initial = load_vif_results(vif_path)
    vif_test_set = load_vif_test_set(vif_test_path)
    auc_delta = load_auc_delta(auc_delta_path)
    calibration_log = load_calibration_results(calibration_path)
    bayesian_log = load_bayesian_convergence(bayesian_path)
    sensitivity_results = load_sensitivity_analysis(sensitivity_path)
    power_analysis = load_power_analysis(power_path)
    final_validation = load_final_validation_report(validation_path)

    # Construct Report
    report_parts = [
        generate_executive_summary(lrt_results, auc_delta, gate_report),
        generate_methodology_section(),
        generate_constitution_compliance_section(gate_report, bayesian_log, calibration_log, vif_initial),
        generate_results_section(lrt_results, vif_initial, auc_delta, calibration_log, bayesian_log),
        generate_limitations_section(sensitivity_results, vif_test_set, power_analysis)
    ]
    
    full_report = "\n".join(report_parts)
    
    # Write to file
    output_path = Path("docs/final_report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    print(f"Final report generated at {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())