"""
Runtime Fallback Logic Implementation (Task 0.4 / T002b).

This module implements the logic to determine the final sample size (N_final)
based on the power analysis requirements (N_required) and the estimated runtime.

It enforces the constraint that if the estimated runtime for N_required exceeds
the 6-hour threshold (21600 seconds), the sample size is reduced to a fallback
value, and the status is marked as 'INCONCLUSIVE' regarding the full power target.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports from sibling modules if needed
# Assuming this script runs from the project root or is invoked via python -m
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Constants
RUNTIME_THRESHOLD_SECONDS = 21600  # 6 hours
POWER_ANALYSIS_INPUT_PATH = DATA_RESULTS_DIR / "power_analysis.json"
OUTPUT_PATH = DATA_RESULTS_DIR / "runtime_fallback.json"

# Estimated processing rate (samples per second)
# This is a heuristic estimate based on VAE encoding + OCR + Classifier overhead on CPU.
# Adjust if T002 (Memory Budget) provided a more specific rate.
# Assuming ~0.5 seconds per sample for the full pipeline (conservative CPU estimate).
ESTIMATED_SECONDS_PER_SAMPLE = 0.5


def load_power_analysis() -> Dict[str, Any]:
    """
    Loads the power analysis results from the previous step (T000).
    """
    if not POWER_ANALYSIS_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {POWER_ANALYSIS_INPUT_PATH}. "
            "Ensure T000 (Power Analysis) has been completed successfully."
        )
    
    with open(POWER_ANALYSIS_INPUT_PATH, 'r') as f:
        return json.load(f)


def estimate_runtime_for_n(n_samples: int) -> float:
    """
    Estimates the total runtime for a given number of samples.
    """
    return n_samples * ESTIMATED_SECONDS_PER_SAMPLE


def run_runtime_fallback_logic() -> Dict[str, Any]:
    """
    Executes the runtime fallback logic.
    
    Logic:
    1. Load N_required from power_analysis.json.
    2. Estimate runtime for N_required.
    3. If estimated_runtime > 21600s:
       - Calculate N_fallback such that runtime ~ 21600s (or slightly under).
       - Set N_final = N_fallback.
       - Set status = "INCONCLUSIVE" (regarding the full power target).
       - Set reason explaining the reduction.
    4. Else:
       - Set N_final = N_required.
       - Set status = "PASS".
       - Set reason explaining it fits the budget.
    
    Returns:
        Dictionary containing the results to be saved.
    """
    power_data = load_power_analysis()
    n_required = power_data.get("N_required")
    
    if n_required is None:
        raise ValueError("N_required not found in power analysis results.")

    estimated_runtime = estimate_runtime_for_n(n_required)

    if estimated_runtime > RUNTIME_THRESHOLD_SECONDS:
        # Calculate fallback N to fit within the threshold
        # We aim for 95% of the threshold to be safe
        safe_runtime_budget = RUNTIME_THRESHOLD_SECONDS * 0.95
        n_fallback = int(safe_runtime_budget / ESTIMATED_SECONDS_PER_SAMPLE)
        
        # Ensure we don't go below a minimum viable sample size (e.g., 100)
        # If even 100 exceeds the budget (unlikely with current constants), cap it.
        if n_fallback < 100:
            n_fallback = 100
            # Recalculate runtime for this forced minimum
            estimated_fallback_runtime = estimate_runtime_for_n(n_fallback)
            # If it still exceeds, we are truly constrained, but we proceed with the min.
            if estimated_fallback_runtime > RUNTIME_THRESHOLD_SECONDS:
                # This implies the processing is extremely slow or budget is tiny.
                # We proceed but flag the runtime as exceeding.
                pass
            else:
                estimated_fallback_runtime = estimate_runtime_for_n(n_fallback)
        else:
            estimated_fallback_runtime = estimate_runtime_for_n(n_fallback)

        result = {
            "N_required": n_required,
            "N_final": n_fallback,
            "estimated_runtime_seconds": estimated_fallback_runtime,
            "status": "INCONCLUSIVE",
            "reason": (
                f"N_required ({n_required}) exceeds 6h runtime budget. "
                f"Reduced to N_final ({n_fallback}) to fit within threshold. "
                f"Full power target may not be achievable within time constraints."
            )
        }
    else:
        result = {
            "N_required": n_required,
            "N_final": n_required,
            "estimated_runtime_seconds": estimated_runtime,
            "status": "PASS",
            "reason": (
                f"N_required ({n_required}) fits within 6h runtime budget. "
                f"Estimated runtime: {estimated_runtime:.2f}s."
            )
        }

    return result


def main():
    """
    Entry point for the script.
    """
    print("Starting Runtime Fallback Logic (T002b)...")
    
    # Ensure output directory exists
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = run_runtime_fallback_logic()
        
        # Write output
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Runtime Fallback Logic completed successfully.")
        print(f"Output written to: {OUTPUT_PATH}")
        print(f"Status: {result['status']}")
        print(f"N_final: {result['N_final']}")
        print(f"Estimated Runtime: {result['estimated_runtime_seconds']:.2f}s")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid data in input file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()