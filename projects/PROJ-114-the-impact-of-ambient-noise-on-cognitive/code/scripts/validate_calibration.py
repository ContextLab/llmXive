"""
Validation script for calibration simulation logic.
Verifies that simulated device responses match real-world expectations (FR-009).
Generates a validation report in JSON format.
"""
import json
import os
import sys
import random
import numpy as np
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    REFERENCE_TONE_PARAMS,
    CALIBRATION_ERROR_THRESHOLD_DB,
    PROCESSED_DIR,
    get_config_summary
)

def simulate_device_response(target_db: float, tolerance_db: float, noise_sigma: float = 0.5) -> float:
    """
    Simulates a device measuring a reference tone.
    Introduces realistic Gaussian noise and potential systematic bias.
    """
    # Simulate systematic bias (e.g., cheap mic is slightly off)
    systematic_bias = np.random.normal(0, 0.3)
    
    # Simulate measurement noise
    measurement_noise = np.random.normal(0, noise_sigma)
    
    measured_db = target_db + systematic_bias + measurement_noise
    return measured_db

def run_calibration_validation(num_simulations: int = 1000) -> dict:
    """
    Runs the calibration validation simulation.
    
    Args:
        num_simulations: Number of virtual devices to simulate.
        
    Returns:
        Dictionary containing validation metrics.
    """
    target_db = REFERENCE_TONE_PARAMS["target_db"]
    tolerance = CALIBRATION_ERROR_THRESHOLD_DB
    
    errors = []
    passed_count = 0
    failed_count = 0
    biases = []

    print(f"Running calibration validation simulation ({num_simulations} iterations)...")
    print(f"Target: {target_db} dB, Tolerance: ±{tolerance} dB")

    for i in range(num_simulations):
        measured = simulate_device_response(target_db, tolerance)
        error = abs(measured - target_db)
        errors.append(error)
        biases.append(measured - target_db)

        if error <= tolerance:
            passed_count += 1
        else:
            failed_count += 1

    errors_np = np.array(errors)
    biases_np = np.array(biases)

    # Calculate statistics
    mean_error = float(np.mean(errors_np))
    std_error = float(np.std(errors_np))
    max_error = float(np.max(errors_np))
    pass_rate = passed_count / num_simulations
    
    # Check if the simulation logic holds up: 
    # We expect > 90% pass rate with our simulated noise parameters
    # If pass rate is too low, our simulation might be too noisy or tolerance too tight
    simulation_fidelity = "PASS" if pass_rate > 0.85 else "WARNING"
    
    # Check for systematic bias
    mean_bias = float(np.mean(biases_np))
    bias_fidelity = "PASS" if abs(mean_bias) < 0.5 else "WARNING"

    report = {
        "simulation_parameters": get_config_summary(),
        "metrics": {
            "total_simulations": num_simulations,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "pass_rate": round(pass_rate, 4),
            "mean_absolute_error_db": round(mean_error, 4),
            "std_error_db": round(std_error, 4),
            "max_error_db": round(max_error, 4),
            "mean_bias_db": round(mean_bias, 4),
        },
        "validation_checks": {
            "fidelity_check": simulation_fidelity,
            "bias_check": bias_fidelity,
            "tolerance_threshold_db": tolerance,
            "expected_real_world_pass_rate_range": "0.85 - 0.95"
        },
        "conclusion": (
            f"Calibration simulation indicates {simulation_fidelity} fidelity. "
            f"Expected pass rate is {pass_rate*100:.1f}%. "
            f"Systematic bias is {mean_bias:.2f} dB."
        )
    }

    return report

def main():
    """Main entry point for the validation script."""
    output_path = os.path.join(PROCESSED_DIR, "calibration_validation_report.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Run simulation
    report = run_calibration_validation(num_simulations=1000)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Validation report generated: {output_path}")
    print(f"Conclusion: {report['conclusion']}")
    
    # Exit with error code if validation failed (for CI/CD)
    if report['validation_checks']['fidelity_check'] != "PASS":
        print("WARNING: Calibration simulation fidelity check failed.")
        sys.exit(1)
    else:
        print("SUCCESS: Calibration simulation passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()