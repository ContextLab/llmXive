import os
import sys
import json
import logging
from pathlib import Path
from config import get_logger, ProjectConfig

logger = get_logger("sc002_verifier")

def load_json_safe(path: Path) -> dict:
    """Safely load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def compute_sc002_verification():
    """
    Compute SC-002 verification metrics:
    1. Load Bayes factor K from data/results/bayes_factor.json
    2. Load null baseline from data/results/null_baseline_report.json
    3. Compute p-value of K against null distribution
    4. Write validity_report.json with pass/fail status
    """
    try:
        # 1. Load Bayes Factor
        bayes_path = Path("data/results/bayes_factor.json")
        if not bayes_path.exists():
            # Fallback if nested sampling output is in a different location or format
            # Check for generic inference results if specific file missing
            raise FileNotFoundError("Bayes factor file not found. Ensure nested sampling completed.")
        
        bayes_data = load_json_safe(bayes_path)
        k_value = bayes_data.get("bayes_factor", 0.0)
        
        # 2. Load Null Baseline
        null_path = Path("data/results/null_baseline_report.json")
        # If null simulation was skipped or not run, we might need to handle it
        # For T036, we assume T026 was run or we check if we have enough data
        if null_path.exists():
            null_data = load_json_safe(null_path)
            null_samples = null_data.get("null_samples", [])
            if null_samples:
                # Calculate p-value: fraction of null samples >= K
                p_value = sum(1 for s in null_samples if s >= k_value) / len(null_samples)
            else:
                p_value = 1.0 # No data, conservative
        else:
            # If null simulation is missing, we can't compute p-value strictly
            # We check the Kass-Rafferty criterion directly as a fallback
            logger.warning("Null baseline report missing. Using Kass-Rafferty only.")
            p_value = 0.0 # Assume significant if K is high enough? No, be conservative.
            # Actually, if null is missing, we can't verify SC_BASELINE_PASS.
            # We will set pass based on K > 3 only for this specific task if null is missing.
            p_value = 0.0 # Placeholder, logic below handles the pass flag

        # 3. Determine Pass Conditions
        # SC002_KASS_RAFTERY_PASS = (K > 3)
        kass_raftery_pass = k_value > 3.0
        
        # SC_BASELINE_PASS: p < 0.05
        # If null data is missing, we might not be able to claim this pass strictly.
        # However, for the pipeline to complete, we check if the condition is met if data exists.
        if null_path.exists() and null_data.get("null_samples"):
            baseline_pass = p_value < 0.05
        else:
            # If no null data, we assume baseline pass is True if K is very high, or False if not.
            # To be safe and realistic: if we can't verify, we fail the specific baseline check.
            baseline_pass = False 
            # Unless the task implies we should just run the check if data exists.
            # Let's set it to False if data missing to force T026 to run first.
            # But T036 depends on T026. If T026 failed, T036 should fail.
            # So we assume T026 ran. If file missing, it's an error.
            raise RuntimeError("Null baseline report missing but required for SC-002 verification.")

        overall_pass = kass_raftery_pass and baseline_pass

        # 4. Write Validity Report
        report = {
            "K_value": k_value,
            "Kass_Rafferty_Pass": kass_raftery_pass,
            "P_value": p_value,
            "Baseline_Pass": baseline_pass,
            "pass": overall_pass,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        report_path = Path("data/results/validity_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"SC-002 Verification Complete. Pass: {overall_pass}, K: {k_value}, P: {p_value}")
        return overall_pass

    except Exception as e:
        logger.error(f"SC-002 Verification failed: {e}")
        # Write a failure report
        report = {
            "pass": False,
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        report_path = Path("data/results/validity_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        return False

def main():
    compute_sc002_verification()

if __name__ == "__main__":
    main()
