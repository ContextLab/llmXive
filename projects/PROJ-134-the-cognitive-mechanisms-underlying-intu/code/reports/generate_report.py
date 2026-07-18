import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Add project root to path to allow relative imports during execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging_utils import get_logger, log_pipeline_step
from analysis.validation import check_parameter_recovery, apply_bonferroni_correction
from analysis.model_comparison import calculate_aic_waic

# Configure logger for this module
logger = get_logger("generate_report")

def load_json_result(filepath: str) -> Dict[str, Any]:
    """
    Load the final model/regression results from a JSON file.
    Expects the output of the regression pipeline (T030/T031).
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Result file not found: {filepath}")
    
    with open(path, 'r') as f:
        return json.load(f)

def determine_pipeline_status(results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if the pipeline validation passed or failed based on:
    1. Parameter Recovery (Ground Truth within CI)
    2. Statistical Significance (Interaction term p-value < alpha after correction)
    3. Model Comparison (Delta AIC > threshold if applicable)
    
    Returns: (passed: bool, reason: str)
    """
    passed = True
    reasons = []

    # 1. Check Parameter Recovery
    recovery = results.get("parameter_recovery", {})
    recovered = recovery.get("is_recovered", False)
    if not recovered:
        passed = False
        reasons.append(f"Parameter Recovery Failed: {recovery.get('message', 'Unknown')}")
    
    # 2. Check Interaction Significance (Bonferroni corrected)
    regression = results.get("regression_results", {})
    interaction = regression.get("interaction_term", {})
    p_val = interaction.get("p_value_corrected", 1.0)
    is_significant = interaction.get("is_significant", False)
    
    if not is_significant:
        # In simulation mode, we expect significance if ground truth is strong.
        # If not significant, it's a validation failure unless ground truth was 0.
        gt = results.get("ground_truth_effect", 0.0)
        if abs(gt) > 0.01:
            passed = False
            reasons.append(f"Interaction not significant (p={p_val:.4f}) despite non-zero ground truth ({gt})")
        else:
            reasons.append("Interaction not significant (expected for zero ground truth)")

    # 3. Check Model Comparison (Delta AIC)
    comparison = results.get("model_comparison", {})
    delta_aic = comparison.get("delta_aic", 0.0)
    # Threshold for 'strong' evidence is often 10, but for pipeline validation we check if it's positive
    # and consistent with the hypothesis.
    if delta_aic < 0:
        passed = False
        reasons.append(f"Model comparison failed: Delta AIC ({delta_aic:.2f}) < 0 (Salience model worse than baseline)")

    if passed:
        return True, "All validation metrics passed."
    else:
        return False, "; ".join(reasons)

def generate_report_content(
    results: Dict[str, Any],
    status: bool,
  status_reason: str,
    output_path: Path
) -> str:
    """
    Generate the final text report content.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_mode = results.get("run_mode", "simulation")
    ground_truth = results.get("ground_truth_effect", "N/A")
    
    # Extract specific metrics for the report
    recovery_info = results.get("parameter_recovery", {})
    reg_info = results.get("regression_results", {})
    comp_info = results.get("model_comparison", {})

    report_lines = [
        "=" * 80,
        "PIPELINE VALIDATION REPORT",
        "=" * 80,
        f"Generated: {timestamp}",
        f"Run Mode: {run_mode}",
        f"Ground Truth Effect: {ground_truth}",
        "-" * 80,
        "1. PARAMETER RECOVERY",
        f"   Recovered: {recovery_info.get('is_recovered', False)}",
        f"   Message: {recovery_info.get('message', 'N/A')}",
        "-" * 80,
        "2. STATISTICAL VALIDATION (Mixed-Effects Regression)",
        f"   Interaction Term (Salience x Foundation):",
        f"      Coefficient: {reg_info.get('interaction_term', {}).get('coef', 'N/A')}",
        f"      P-value (Bonferroni): {reg_info.get('interaction_term', {}).get('p_value_corrected', 'N/A')}",
        f"      Significant: {reg_info.get('interaction_term', {}).get('is_significant', False)}",
        "-" * 80,
        "3. MODEL COMPARISON",
        f"   Delta AIC (Salience vs Baseline): {comp_info.get('delta_aic', 'N/A')}",
        f"   WAIC Difference: {comp_info.get('delta_waic', 'N/A')}",
        "-" * 80,
        "4. FINAL VALIDATION STATUS",
        f"   STATUS: {'PASSED' if status else 'FAILED'}",
        f"   REASON: {status_reason}",
        "-" * 80,
    ]

    # Add specific note about simulation mode vs scientific claims
    if run_mode == "simulation":
        report_lines.append("NOTE: This is a PIPELINE VALIDATION ONLY.")
        report_lines.append("Evidence strength (Delta AIC) calculated but scientific claims are deferred")
        report_lines.append("to Phase 4 as per the Staged Implementation Authorization.")
        report_lines.append("The primary goal was to verify that the pipeline recovers the known ground truth.")
    else:
        report_lines.append("NOTE: This report reflects analysis on REAL data.")
        report_lines.append("Scientific claims regarding the effect of perceptual salience on moral judgments")
        report_lines.append("are supported by the validation metrics above.")

    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)

def main():
    """
    Main entry point for generating the final report.
    Expects the regression pipeline output to be at:
    data/processed/regression_results.json
    
    Writes the final report to:
    reports/validation_report.txt
    """
    # Ensure directories exist
    ensure_directories()
    
    input_file = Path("data/processed/regression_results.json")
    output_file = Path("reports/validation_report.txt")
    
    if not input_file.exists():
        logger.error(f"Input result file not found: {input_file}")
        # Create a failure report if input is missing
        error_report = f"VALIDATION FAILED\nReason: Input file {input_file} not found."
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(error_report)
        return 1

    try:
        # Load results
        logger.info(f"Loading results from {input_file}")
        results = load_json_result(str(input_file))
        
        # Determine status
        passed, reason = determine_pipeline_status(results)
        
        # Generate content
        report_text = generate_report_content(results, passed, reason, output_file)
        
        # Write report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Report generated successfully: {output_file}")
        print(report_text)
        
        # Update state if needed (optional, but good practice)
        # This task focuses on the report generation itself.
        
        return 0 if passed else 1

    except Exception as e:
        logger.exception(f"Error generating report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())