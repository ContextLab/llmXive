"""
Calibration script to validate codecarbon power draw detection.
Runs a CPU-bound load loop (not matrix multiply) to stress the CPU.
The script validates that codecarbon can detect power draw changes.
It exits with code 1 if the deviation from expected baseline behavior
exceeds 10% (interpreted here as a failure to detect non-zero emissions
or a crash in the tracking mechanism).

FR-010 Compliance: Validates CPU-bound load loop detection.
"""
import time
import math
import sys
import os
from codecarbon import EmissionsTracker

# Configuration for the calibration run
CALIBRATION_DURATION_SECONDS = 10
MAX_ALLOWED_DEVIATION_PERCENT = 10.0

# Expected baseline behavior for a real CPU load in a standard environment.
# Since we cannot measure "true" power without a hardware meter, we define
# a logical baseline: a CPU load of this duration on a standard modern CPU
# should produce a non-zero emission value.
# In a virtualized environment (CI), the value might be very low, but > 0.
# We define a "theoretical minimum" based on the duration and a conservative
# power estimate (e.g., 10W for 10s = 100J = 0.0000277 kWh).
# If the measured value is 0, the deviation from "expected > 0" is 100%.
# We will implement a check that ensures the value is non-zero and consistent
# with a load being present.

# To strictly satisfy the "10% deviation" requirement, we will run the loop
# twice. If the two runs differ by more than 10%, we assume instability/failure.
# However, a single run comparison against a "zero" baseline is the most robust
# check for "detection".
# Let's implement a dual-run consistency check:
# Run 1 and Run 2. If |Run1 - Run2| / max(Run1, Run2) > 0.10, then deviation > 10%.
# If either is 0, deviation is 100% (if the other is > 0) or undefined (if both 0).

def cpu_load_loop(duration_seconds: int) -> float:
    """
    Generates a sustained CPU-bound load using math operations.
    This avoids matrix multiplication (which might be offloaded to GPU/accelerators
    or optimized differently) and ensures the CPU is the primary load source.
    
    Args:
        duration_seconds: How long to run the load loop.
        
    Returns:
        A float result derived from the loop to prevent compiler/interpreter optimization.
    """
    end_time = time.time() + duration_seconds
    x = 1.0
    # Perform a chaotic-ish math operation to prevent loop unrolling/optimization
    while time.time() < end_time:
        x = math.sin(x) * math.cos(x)
        # Ensure the value changes and doesn't converge to a constant
        if abs(x) > 1e-10:
            x += 0.00013
        else:
            x = 0.5
    return x

def get_emissions_value(tracker: EmissionsTracker) -> float:
    """
    Extracts the emissions value from the tracker.
    """
    emissions = tracker.finalize()
    if hasattr(emissions, 'emissions'):
        return float(emissions.emissions)
    elif isinstance(emissions, (int, float)):
        return float(emissions)
    else:
        print(f"Warning: Unexpected emissions type: {type(emissions)}")
        return 0.0

def main():
    print("Starting CodeCarbon calibration test (T006)...")
    print(f"Running CPU-bound load loop for {CALIBRATION_DURATION_SECONDS} seconds (x2 runs)...")
    print("This validates that codecarbon detects power draw changes.")

    emissions_values = []
    
    try:
        # Run two consecutive calibration loops to check for consistency (deviation)
        for i in range(2):
            print(f"\n--- Run {i+1} of 2 ---")
            with EmissionsTracker(save_to_file=False, save_to_api=False, 
                                  measure_power_secs=1.0) as tracker:
                # Execute the load
                result = cpu_load_loop(duration_seconds=CALIBRATION_DURATION_SECONDS)
                # Use the result to ensure it's not optimized away
                _ = result + 1.0
            
            val = get_emissions_value(tracker)
            emissions_values.append(val)
            print(f"Run {i+1} Emissions: {val:.6f} kgCO2eq")

        if len(emissions_values) != 2:
            print("CRITICAL: Could not complete two runs.")
            sys.exit(1)

        val1, val2 = emissions_values

        # Validation Logic for FR-010:
        # 1. Check for non-zero detection (Baseline check)
        if val1 <= 0 or val2 <= 0:
            print(f"CRITICAL: Emissions detected as {val1} and {val2}.")
            print("The tracker failed to detect CPU load (Deviation from expected > 10%).")
            print("Expected: > 0 kgCO2eq. Got: 0 or negative.")
            sys.exit(1)

        # 2. Check for consistency (Deviation check)
        # Calculate percentage deviation between the two runs
        # Formula: |val1 - val2| / max(val1, val2)
        max_val = max(val1, val2)
        deviation = abs(val1 - val2) / max_val
        deviation_percent = deviation * 100.0

        print(f"\n--- Calibration Analysis ---")
        print(f"Run 1: {val1:.6f} kgCO2eq")
        print(f"Run 2: {val2:.6f} kgCO2eq")
        print(f"Max Value: {max_val:.6f} kgCO2eq")
        print(f"Absolute Difference: {abs(val1 - val2):.6f} kgCO2eq")
        print(f"Calculated Deviation: {deviation_percent:.2f}%")

        if deviation_percent > MAX_ALLOWED_DEVIATION_PERCENT:
            print(f"CRITICAL: Deviation ({deviation_percent:.2f}%) exceeds allowed threshold ({MAX_ALLOWED_DEVIATION_PERCENT}%).")
            print("The power measurement is unstable or codecarbon is not functioning correctly.")
            sys.exit(1)

        print(f"Calibration successful: CodeCarbon detected CPU load with {deviation_percent:.2f}% deviation (within {MAX_ALLOWED_DEVIATION_PERCENT}%).")
        sys.exit(0)

    except Exception as e:
        print(f"CRITICAL ERROR during calibration: {e}")
        print("Deviation from expected execution flow > 10% (Exception raised).")
        sys.exit(1)

if __name__ == "__main__":
    main()