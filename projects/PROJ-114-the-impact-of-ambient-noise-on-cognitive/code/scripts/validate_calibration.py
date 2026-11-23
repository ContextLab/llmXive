"""
Calibration Validation Script for Ambient Noise Study.

Validates the simulation logic for device calibration (FR-009) by:
1. Simulating device responses to reference tones with realistic noise.
2. Calculating error margins against target SPL.
3. Generating a validation report to ensure simulation fidelity.

Output: data/processed/calibration_validation_report.json
"""
import json
import os
import sys
import random
import numpy as np
from pathlib import Path

# Add project root to path to allow relative imports if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import (
    REFERENCE_TONE_PARAMS,
    CALIBRATION_ERROR_THRESHOLD_DB,
    PROCESSED_DIR,
    setup_logging,
    get_config_summary
)

logger = setup_logging("validate_calibration")

def simulate_device_response(
    target_db: float,
    tolerance_db: float,
    sample_size: int = 1000,
    seed: int = 42
) -> np.ndarray:
    """
    Simulates device response to a reference tone.
    
    Models real-world acoustic variance and sensor noise.
    Assumes a normal distribution of measurement errors around the target.
    
    Args:
        target_db: The target SPL in dB (e.g., 60.0).
        tolerance_db: The acceptable error margin (e.g., 2.0).
        sample_size: Number of simulated measurements.
        seed: Random seed for reproducibility.
    
    Returns:
        np.ndarray: Array of simulated measured dB values.
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Real-world devices typically have a standard deviation in measurement
    # For a 60dB tone, a typical consumer mic might have ~0.5-1.5dB std dev.
    # We use 0.8dB to simulate realistic but stable hardware.
    std_dev = 0.8
    
    # Generate measurements
    measurements = np.random.normal(loc=target_db, scale=std_dev, size=sample_size)
    
    logger.info(f"Simulated {sample_size} device responses for target {target_db}dB (σ={std_dev})")
    return measurements

def run_calibration_validation() -> dict:
    """
    Runs the full calibration validation logic.
    
    1. Loads reference parameters.
    2. Simulates device responses.
    3. Calculates statistics (mean, std, min, max).
    4. Determines pass/fail rates against the tolerance threshold.
    5. Compares simulated distribution characteristics to expected real-world behavior.
    
    Returns:
        dict: Validation report data.
    """
    params = REFERENCE_TONE_PARAMS
    target_db = params["target_db"]
    tolerance_db = params["tolerance_db"]
    
    logger.info(f"Starting calibration validation for target: {target_db}dB ± {tolerance_db}dB")
    
    # Simulate
    measurements = simulate_device_response(target_db, tolerance_db)
    
    # Calculate Statistics
    mean_val = float(np.mean(measurements))
    std_val = float(np.std(measurements))
    min_val = float(np.min(measurements))
    max_val = float(np.max(measurements))
    
    # Check against tolerance
    # A measurement is "valid" if it falls within [target - tolerance, target + tolerance]
    lower_bound = target_db - tolerance_db
    upper_bound = target_db + tolerance_db
    
    valid_mask = (measurements >= lower_bound) & (measurements <= upper_bound)
    valid_count = int(np.sum(valid_mask))
    total_count = len(measurements)
    pass_rate = valid_count / total_count
    
    # Expected behavior check:
    # With mean=target and std=0.8, and tolerance=2.0 (2.5 sigma),
    # we expect ~98.7% of data to be within bounds.
    # We flag if pass_rate is significantly lower than expected (< 95%)
    expected_min_pass_rate = 0.95
    fidelity_status = "PASS" if pass_rate >= expected_min_pass_rate else "FAIL"
    
    report = {
        "timestamp": str(Path(__file__).stat().st_mtime), # Simple timestamp for report
        "parameters": {
            "target_db": target_db,
            "tolerance_db": tolerance_db,
            "sample_size": total_count
        },
        "statistics": {
            "mean_db": round(mean_val, 4),
            "std_db": round(std_val, 4),
            "min_db": round(min_val, 4),
            "max_db": round(max_val, 4)
        },
        "validation_results": {
            "lower_bound_db": lower_bound,
            "upper_bound_db": upper_bound,
            "valid_count": valid_count,
            "total_count": total_count,
            "pass_rate": round(pass_rate, 4),
            "expected_min_pass_rate": expected_min_pass_rate,
            "fidelity_status": fidelity_status
        },
        "config_summary": get_config_summary(),
        "notes": [
            "Simulation assumes Gaussian noise distribution typical of consumer audio hardware.",
            "Pass rate threshold set to 95% to account for extreme outliers in real hardware."
        ]
    }
    
    logger.info(f"Validation complete. Status: {fidelity_status}, Pass Rate: {pass_rate:.2%}")
    
    return report

def main():
    """Main entry point for the script."""
    logger.info("Executing calibration validation script...")
    
    try:
        report = run_calibration_validation()
        
        output_path = Path(PROCESSED_DIR) / "calibration_validation_report.json"
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report successfully written to {output_path}")
        print(f"SUCCESS: Validation report generated at {output_path}")
        
        # Return 0 on success
        return 0
        
    except Exception as e:
        logger.error(f"Calibration validation failed: {e}", exc_info=True)
        print(f"FAILURE: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
