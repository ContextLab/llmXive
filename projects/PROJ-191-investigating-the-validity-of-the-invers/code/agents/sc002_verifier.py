"""
SC-002 Verification: Single Source of Truth & Bayes Factor Comparison.

This module computes the Bayes-factor comparison metric required for SC-002.
It performs two critical checks:
1. Compares the primary Bayes factor K against the null-simulation baseline
   to ensure the result is not a systematic artifact.
2. Compares K against the Kass–Raftery scale (K > 3 indicates substantial
   evidence for the Yukawa model).

The script reads outputs from T026 (null_simulation) and T023/T024 (inference),
then writes a detailed report to data/results/sc002_verification.json.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path if running as script
if "code" not in sys.path:
    code_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(code_root))

from config import get_logger, ProjectConfig

logger = get_logger("SC002_VERIFIER")

# Constants
KASS_RAFTERY_THRESHOLD = 3.0  # Log Bayes Factor threshold for "substantial evidence"
NULL_BAYES_FACTOR_THRESHOLD = 3.0  # Threshold to consider false positive in null sim

def load_json_safe(path: Path, default: dict = None) -> dict:
    """Load JSON file safely, returning default if missing or invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}. Returning default.")
        return default if default is not None else {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return default if default is not None else {}

def compute_sc002_verification() -> dict:
    """
    Perform SC-002 verification checks.

    Returns:
        dict: Verification results including PASS/FAIL status and detailed metrics.
    """
    config = ProjectConfig()
    results_dir = config.results_dir
    processed_dir = config.processed_dir

    # 1. Load Primary Bayes Factor (from Nested Sampling output)
    # Expected output from T024 (nested.py) or T023 (mcmc.py) usually in data/results/
    # We look for the latest nested sampling result or a specific summary file.
    # Assuming T024 writes to data/results/nested_sampling_results.json
    nested_results_path = results_dir / "nested_sampling_results.json"
    nested_data = load_json_safe(nested_results_path, {})

    # Extract Bayes Factor K (log_K or K depending on format, usually log_K in dynesty)
    # If T024 outputs log_Bayes_Factor, we use that. If it outputs K directly, we use that.
    # Standard convention in this project seems to be log_Bayes_Factor.
    log_k_primary = nested_data.get("log_Bayes_Factor")
    
    # If log_K is not found, try to find K directly
    k_primary = nested_data.get("Bayes_Factor")
    
    # Normalize to log scale for comparison
    if log_k_primary is not None:
        log_k_val = log_k_primary
    elif k_primary is not None:
        import math
        log_k_val = math.log(k_primary) if k_primary > 0 else float('-inf')
    else:
        logger.error("Could not find Bayes Factor in nested sampling results.")
        log_k_val = None

    # 2. Load Null Simulation Baseline (from T026)
    null_baseline_path = results_dir / "null_baseline_report.json"
    null_data = load_json_safe(null_baseline_path, {})

    false_positive_detected = null_data.get("false_positive_detected", False)
    bayes_factor_null = null_data.get("bayes_factor_K") # This might be log_K or K
    
    # Determine if null simulation indicates a problem
    # If the null simulation produced a Bayes Factor > 3 (substantial evidence for Yukawa when alpha=0),
    # then our method is prone to false positives.
    is_null_problematic = False
    if bayes_factor_null is not None:
        # If stored as log_K
        if isinstance(bayes_factor_null, float) and bayes_factor_null > KASS_RAFTERY_THRESHOLD:
            is_null_problematic = True
        # If stored as K
        elif isinstance(bayes_factor_null, float) and bayes_factor_null > math.exp(KASS_RAFTERY_THRESHOLD):
            is_null_problematic = True

    # 3. Perform Checks
    check_1_pass = True
    check_1_reason = "Null simulation baseline is acceptable."
    
    if is_null_problematic:
        check_1_pass = False
        check_1_reason = "Null simulation detected false positive (Bayes Factor > 3 when alpha=0). Primary result may be a systematic artifact."

    check_2_pass = False
    check_2_reason = "Insufficient evidence for Yukawa model (K <= 3)."
    
    if log_k_val is not None:
        if log_k_val > KASS_RAFTERY_THRESHOLD:
            check_2_pass = True
            check_2_reason = f"Bayes Factor (log_K={log_k_val:.2f}) exceeds Kass-Raftery threshold ({KASS_RAFTERY_THRESHOLD}). Substantial evidence for Yukawa model."
        else:
            check_2_reason = f"Bayes Factor (log_K={log_k_val:.2f}) does not exceed Kass-Raftery threshold ({KASS_RAFTERY_THRESHOLD})."

    # Final SC-002 Status
    # SC-002 requires BOTH checks to pass? Or at least the baseline check to pass and then interpretation?
    # The prompt says: "PASS/FAIL status if K <= 3 (insufficient evidence) OR if the baseline comparison fails"
    # So FAIL if (K <= 3) OR (baseline fails).
    sc002_pass = check_1_pass and check_2_pass

    report = {
        "task_id": "T038",
        "check_1_baseline_valid": check_1_pass,
        "check_1_reason": check_1_reason,
        "check_2_kass_raftery_valid": check_2_pass,
        "check_2_reason": check_2_reason,
        "primary_log_bayes_factor": log_k_val,
        "null_baseline_log_bayes_factor": bayes_factor_null,
        "null_false_positive_detected": is_null_problematic,
        "sc002_pass": sc002_pass,
        "sc002_status": "PASS" if sc002_pass else "FAIL",
        "timestamp": ProjectConfig().get_timestamp()
    }

    return report

def main():
    """Main entry point for T038."""
    logger.info("Starting SC-002 Verification (T038)...")
    
    try:
        report = compute_sc002_verification()
        
        # Write report to data/results
        config = ProjectConfig()
        output_path = config.results_dir / "sc002_verification.json"
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"SC-002 Verification complete. Report saved to: {output_path}")
        logger.info(f"Status: {report['sc002_status']}")
        
        if not report['sc002_pass']:
            logger.warning("SC-002 verification failed. Review results for systematic artifacts or insufficient evidence.")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during SC-002 Verification: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
