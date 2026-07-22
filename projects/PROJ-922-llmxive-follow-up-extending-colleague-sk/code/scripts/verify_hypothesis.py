"""
Script to verify the primary hypothesis and the non-inferiority margin check.

This script implements the logic required by SC-002 and T042:
1. Checks if the 'Separated Tracks' condition has a lower Hallucination Rate 
   than the 'Monolithic' condition (Separated < Monolithic).
2. Checks if the 'Separated Tracks' condition is non-inferior to 'Monolithic' 
   for Style Consistency, using a predefined margin of 0.05.

Inputs:
    data/processed/glm_results.json (Output from T028/T029)

Outputs:
    data/processed/hypothesis_verification.json
    data/processed/final_results.csv (updated with verification status)
"""
import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_data_dir, ensure_dir
from utils.logging import get_logger, log_info, log_error, log_warning

# Constants defined in T004b / SC-002
NON_INFERIORITY_MARGIN = 0.05

logger = get_logger("verify_hypothesis")

def load_glm_results() -> Optional[Dict[str, Any]]:
    """Load the GLM results from the processed directory."""
    results_path = get_data_dir() / "processed" / "glm_results.json"
    if not results_path.exists():
        log_error(f"GLM results file not found: {results_path}")
        return None
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse GLM results JSON: {e}")
        return None

def check_hallucination_hypothesis(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that Separated < Monolithic for Hallucination Rate.
    
    SC-002 Requirement: Verify direction of effect aligns with hypothesis.
    """
    log_info("Checking Hallucination Rate hypothesis (Separated < Monolithic)...")
    
    # The results structure is expected to contain fixed effects or summary stats.
    # Based on T028, we expect 'p_values', 'effect_sizes', and potentially 'non_inferiority_margin_check'.
    # We need to extract the estimated means or coefficients for the conditions.
    
    # Assumption: The GLM results contain a summary of fixed effects where we can compare conditions.
    # If the model used 'Monolithic' as reference, the coefficient for 'Separated' should be negative.
    # Or, if it provides means, we compare them directly.
    
    # Fallback to a generic check if specific keys vary:
    # We look for a structure like: { "metrics": { "hallucination_rate": { "monolithic": X, "separated": Y } } }
    # OR we look at effect sizes if available.
    
    hallucination_data = results.get("metrics", {}).get("hallucination_rate", {})
    
    # Attempt to find explicit means if available
    monolithic_hr = hallucination_data.get("monolithic_mean")
    separated_hr = hallucination_data.get("separated_mean")
    
    passed = False
    details = "Could not determine means from results."
    
    if monolithic_hr is not None and separated_hr is not None:
        if separated_hr < monolithic_hr:
            passed = True
            details = f"Separated ({separated_hr:.4f}) < Monolithic ({monolithic_hr:.4f})"
        else:
            details = f"Separated ({separated_hr:.4f}) >= Monolithic ({monolithic_hr:.4f})"
    else:
        # Fallback: Check effect size sign if means are not explicitly stored but coefficients are
        # Assuming 'Separated' is the comparison and 'Monolithic' is baseline
        effect_size = results.get("fixed_effects", {}).get("hallucination_rate", {}).get("separated_effect")
        if effect_size is not None:
            if effect_size < 0:
                passed = True
                details = f"Effect size {effect_size:.4f} indicates reduction."
            else:
                details = f"Effect size {effect_size:.4f} does not indicate reduction."
        else:
            log_warning("Could not find explicit means or effect sizes for Hallucination Rate.")
            # If we have p-values for the difference, we might infer, but strictly we need the direction.
            # For this implementation, we assume if the p-value is significant and the direction is expected,
            # but without the mean, we cannot confirm the direction.
            details = "Missing data to confirm direction."

    return {
        "metric": "hallucination_rate",
        "hypothesis": "Separated < Monolithic",
        "passed": passed,
        "details": details,
        "monolithic_value": monolithic_hr,
        "separated_value": separated_hr
    }

def check_style_consistency_non_inferiority(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify non-inferiority for Style Consistency.
    
    SC-002 Requirement: Verify non-inferiority margin (0.05) for Style Consistency.
    Logic: Separated >= Monolithic - Margin (or |Separated - Monolithic| <= Margin if looking for equivalence,
    but non-inferiority usually implies Separated is not worse than Monolithic by more than margin).
    
    Since higher Style Consistency is better, Non-Inferiority means:
    Separated >= Monolithic - Margin
    OR
    (Monolithic - Separated) <= Margin
    """
    log_info(f"Checking Style Consistency non-inferiority (Margin = {NON_INFERIORITY_MARGIN})...")
    
    style_data = results.get("metrics", {}).get("style_consistency", {})
    
    monolithic_sc = style_data.get("monolithic_mean")
    separated_sc = style_data.get("separated_mean")
    
    passed = False
    margin_check_result = "UNKNOWN"
    details = "Could not determine means."
    
    if monolithic_sc is not None and separated_sc is not None:
        diff = monolithic_sc - separated_sc  # Positive if Monolithic is better
        
        # Non-inferiority: Separated is not worse than Monolithic by more than Margin
        # i.e., (Monolithic - Separated) <= Margin
        if diff <= NON_INFERIORITY_MARGIN:
            passed = True
            margin_check_result = "PASS"
            details = f"Difference ({diff:.4f}) <= Margin ({NON_INFERIORITY_MARGIN})"
        else:
            margin_check_result = "FAIL"
            details = f"Difference ({diff:.4f}) > Margin ({NON_INFERIORITY_MARGIN})"
    else:
        # Fallback to pre-calculated check if available in results
        existing_check = results.get("non_inferiority_margin_check", {}).get("style_consistency")
        if existing_check:
            margin_check_result = existing_check.get("status", "UNKNOWN")
            passed = (margin_check_result == "PASS")
            details = existing_check.get("details", "Pre-calculated check found but missing details.")
        else:
            log_warning("Missing data to confirm non-inferiority.")

    return {
        "metric": "style_consistency",
        "hypothesis": f"Non-Inferiority (Separated >= Monolithic - {NON_INFERIORITY_MARGIN})",
        "passed": passed,
        "margin": NON_INFERIORITY_MARGIN,
        "margin_check_result": margin_check_result,
        "details": details,
        "monolithic_value": monolithic_sc,
        "separated_value": separated_sc
    }

def main():
    """Main entry point for hypothesis verification."""
    log_info("Starting Hypothesis Verification (T042)...")
    
    results = load_glm_results()
    if not results:
        log_error("Failed to load GLM results. Exiting.")
        sys.exit(1)
    
    hallucination_check = check_hallucination_hypothesis(results)
    style_check = check_style_consistency_non_inferiority(results)
    
    overall_status = "PASS" if (hallucination_check["passed"] and style_check["passed"]) else "FAIL"
    
    verification_report = {
        "status": overall_status,
        "checks": [hallucination_check, style_check],
        "timestamp": str(Path(__file__).stat().st_mtime),
        "margin_used": NON_INFERIORITY_MARGIN
    }
    
    # Save report
    output_dir = get_data_dir() / "processed"
    ensure_dir(output_dir)
    output_path = output_dir / "hypothesis_verification.json"
    
    with open(output_path, 'w') as f:
        json.dump(verification_report, f, indent=2)
    
    log_info(f"Verification report saved to {output_path}")
    log_info(f"Overall Status: {overall_status}")
    
    if overall_status == "PASS":
        log_info("Hypothesis verification PASSED: Separated tracks reduce hallucination and maintain style consistency within margin.")
    else:
        log_warning("Hypothesis verification FAILED. Review details in report.")
    
    # Update final_results.csv if it exists to include the status
    final_results_path = output_dir / "final_results.csv"
    if final_results_path.exists():
        # Read, append status column if missing, or update
        rows = []
        with open(final_results_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                return
            
            if "verification_status" not in fieldnames:
                fieldnames = list(fieldnames) + ["verification_status"]
            
            for row in reader:
                row["verification_status"] = overall_status
                rows.append(row)
        
        with open(final_results_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log_info(f"Updated {final_results_path} with verification status.")
    
    return 0 if overall_status == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())