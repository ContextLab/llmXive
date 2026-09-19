"""
T047c: Execute and validate thermo_extrapolator.py on a sample set of missing parameters.

This script demonstrates the functionality of the thermo_extrapolator module by:
1. Generating a synthetic sample of CALPHAD parameters with missing temperature points.
2. Running the linear extrapolation logic.
3. Validating the output against expected mathematical behavior.
4. Writing the results to data/processed/extrapolation_validation.json.

Note: The 'missing' parameters are simulated here to test the extrapolator logic
without requiring a full real-world CALPHAD database load, but the logic
operates on the same data structures as the real data.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.services.thermo_extrapolator import linear_extrapolate_missing_params
from code.config import get_logger, PROCESSED_PATH

logger = get_logger(__name__)

def generate_sample_missing_params() -> List[Dict[str, Any]]:
    """
    Generates a deterministic sample of CALPHAD parameters with intentionally
    missing temperature points to test the extrapolation logic.
    """
    # Base parameters for a fictional binary interaction (e.g., Fe-Cr)
    # We simulate L0, L1, L2 parameters with temperature dependence: G = A + B*T
    samples = []

    # Define a range of temperatures where data exists
    known_temps = [500, 600, 700, 800]
    # Define a target temperature that is "missing" (900 K)
    target_temp = 900

    # Create a parameter set for L0
    l0_params = {
        "system": "Fe-Cr",
        "parameter_type": "L0",
        "element_A": "Fe",
        "element_B": "Cr",
        "known_points": [
            {"T": 500, "value": -10000.0},
            {"T": 600, "value": -10500.0},
            {"T": 700, "value": -11000.0},
            {"T": 800, "value": -11500.0},
        ],
        "missing_temps": [900],
        "extrapolation_method": "linear"
    }
    samples.append(l0_params)

    # Create a parameter set for L1 with a different slope
    l1_params = {
        "system": "Fe-Cr",
        "parameter_type": "L1",
        "element_A": "Fe",
        "element_B": "Cr",
        "known_points": [
            {"T": 500, "value": 2000.0},
            {"T": 600, "value": 2200.0},
            {"T": 700, "value": 2400.0},
            {"T": 800, "value": 2600.0},
        ],
        "missing_temps": [900],
        "extrapolation_method": "linear"
    }
    samples.append(l1_params)

    return samples

def validate_extrapolation(sample: Dict[str, Any], result: Dict[str, Any]) -> bool:
    """
    Validates that the extrapolation result is mathematically consistent
    with linear extrapolation of the known points.
    """
    known = sample["known_points"]
    missing_temps = sample["missing_temps"]
    
    if not known:
        return False

    # Extract T and V for regression check
    T_vals = np.array([p["T"] for p in known])
    V_vals = np.array([p["value"] for p in known])

    # Fit a simple line to check slope
    # y = mx + c
    # m = (y2 - y1) / (x2 - x1) using first and last points for simplicity in this test
    # Since the data is perfectly linear in our generator, this is robust.
    m = (V_vals[-1] - V_vals[0]) / (T_vals[-1] - T_vals[0])
    c = V_vals[0] - m * T_vals[0]

    all_valid = True
    for missing_T in missing_temps:
        expected_val = m * missing_T + c
        # Find the result for this temperature
        res_entry = next((r for r in result["extrapolated_values"] if r["T"] == missing_T), None)
        if res_entry is None:
            logger.error(f"Missing extrapolated value for T={missing_T}")
            all_valid = False
            continue

        actual_val = res_entry["value"]
        
        # Check closeness (allow small float epsilon)
        if not np.isclose(actual_val, expected_val, rtol=1e-5):
            logger.error(f"Extrapolation mismatch for T={missing_T}: expected {expected_val}, got {actual_val}")
            all_valid = False
    
    return all_valid

def main():
    logger.info("Starting T047c: Execute and validate thermo_extrapolator")
    
    # Ensure output directory exists
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_PATH / "extrapolation_validation.json"

    try:
        # 1. Generate sample data
        sample_data = generate_sample_missing_params()
        logger.info(f"Generated {len(sample_data)} sample parameter sets with missing data.")

        # 2. Run extrapolation
        results = []
        for i, sample in enumerate(sample_data):
            logger.info(f"Processing sample {i+1}/{len(sample_data)}: {sample['parameter_type']}")
            result = linear_extrapolate_missing_params(sample)
            results.append(result)

            # 3. Validate immediately
            if not validate_extrapolation(sample, result):
                raise ValueError(f"Validation failed for sample {i+1}")

        # 4. Write results to disk
        output_data = {
            "status": "success",
            "task_id": "T047c",
            "samples_processed": len(results),
            "results": results
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Validation successful. Results written to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Task T047c failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())