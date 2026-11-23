"""
Numerical stability checks and divergence detection for spin simulations.

This module implements the mandatory edge case handling for simulation divergence:
- Detects when energy values exceed significantly elevated levels
- Aborts the run immediately upon detection
- Logs the event via the logging infrastructure
- Flags the result as [SIMULATION_DIVERGENCE]
- NO retry or recovery logic is permitted
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from code.src.utils.logging import log_metric, init_logging
from code.src.utils.config import load_config

# Configuration constants for divergence detection
DIVERGENCE_THRESHOLD = 1e6  # Energy values exceeding this are considered divergent
MAX_ENERGY_DENSITY = 1e4    # Maximum allowed energy density per node
NUMERICAL_STABILITY_TOLERANCE = 1e-10  # Tolerance for numerical operations


class SimulationDivergenceError(Exception):
    """Exception raised when simulation diverges due to numerical instability."""
    def __init__(self, message: str, run_id: str, step: int, energy_value: float):
        super().__init__(message)
        self.run_id = run_id
        self.step = step
        self.energy_value = energy_value
        self.tag = "[SIMULATION_DIVERGENCE]"


def check_numerical_stability(
    energy_values: List[float],
    step: int,
    run_id: str,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if energy values indicate numerical divergence.
    
    Args:
        energy_values: List of energy values from the current simulation step
        step: Current simulation step number
        run_id: Unique identifier for this simulation run
        logger: Optional logger instance
        
    Returns:
        Tuple of (is_stable, error_message)
        - is_stable: True if all values are within acceptable bounds
        - error_message: None if stable, otherwise contains divergence details
        
    Raises:
        SimulationDivergenceError: If divergence is detected (no retry logic)
    """
    if not energy_values:
        return True, None
    
    max_energy = max(abs(e) for e in energy_values)
    avg_energy_density = sum(abs(e) for e in energy_values) / len(energy_values)
    
    # Check for absolute divergence threshold
    if max_energy > DIVERGENCE_THRESHOLD:
        error_msg = (
            f"Divergence detected at step {step}: "
            f"max_energy={max_energy:.2e} exceeds threshold {DIVERGENCE_THRESHOLD:.2e}. "
            f"Run aborted. {SimulationDivergenceError('').tag}"
        )
        return False, error_msg
    
    # Check for energy density per node
    if avg_energy_density > MAX_ENERGY_DENSITY:
        error_msg = (
            f"Divergence detected at step {step}: "
            f"avg_energy_density={avg_energy_density:.2e} exceeds limit {MAX_ENERGY_DENSITY:.2e}. "
            f"Run aborted. {SimulationDivergenceError('').tag}"
        )
        return False, error_msg
    
    # Check for NaN or Inf values
    for i, val in enumerate(energy_values):
        if not (val == val):  # NaN check
            error_msg = (
                f"Divergence detected at step {step}: "
                f"NaN value at index {i}. Run aborted. {SimulationDivergenceError('').tag}"
            )
            return False, error_msg
        if abs(val) == float('inf'):
            error_msg = (
                f"Divergence detected at step {step}: "
                f"Infinite value at index {i}. Run aborted. {SimulationDivergenceError('').tag}"
            )
            return False, error_msg
    
    return True, None


def handle_divergence(
    run_id: str,
    step: int,
    energy_value: float,
    seed: int,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Handle simulation divergence by aborting and logging.
    
    This function implements the mandatory edge case behavior:
    - Aborts the run immediately
    - Logs the divergence event with event_type='divergence_detected'
    - Flags the result as [SIMULATION_DIVERGENCE]
    - NO retry or recovery logic
    
    Args:
        run_id: Unique identifier for this simulation run
        step: Current simulation step number
        energy_value: The energy value that triggered divergence
        seed: Random seed used for this run
        config: Optional configuration dictionary
        
    Raises:
        SimulationDivergenceError: Always raised to force abort
    """
    # Initialize logging if not already done
    init_logging()
    
    # Log the divergence event
    log_entry = {
        "run_id": run_id,
        "step": step,
        "energy_value": energy_value,
        "threshold": DIVERGENCE_THRESHOLD,
        "status": "aborted",
        "tag": "[SIMULATION_DIVERGENCE]"
    }
    
    log_metric({
        "timestamp": None,  # Will be set by log_metric
        "event_type": "divergence_detected",
        "run_id": run_id,
        "seed": seed,
        "status": "aborted",
        "duration_seconds": 0.0,  # Will be calculated by caller if needed
        "details": log_entry
    })
    
    # Raise exception to force abort (no retry logic)
    error = SimulationDivergenceError(
        f"Simulation diverged at step {step} with energy {energy_value:.2e}",
        run_id,
        step,
        energy_value
    )
    raise error


def validate_simulation_step(
    energy_values: List[float],
    step: int,
    run_id: str,
    seed: int,
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Validate a simulation step and handle divergence if detected.
    
    This is the main entry point for stability checking during simulation.
    It checks stability and if divergence is detected, it handles the abort
    and logging before raising an exception.
    
    Args:
        energy_values: List of energy values from the current step
        step: Current simulation step number
        run_id: Unique identifier for this simulation run
        seed: Random seed used for this run
        config: Optional configuration dictionary
        
    Returns:
        True if step is stable
        
    Raises:
        SimulationDivergenceError: If divergence is detected
    """
    is_stable, error_msg = check_numerical_stability(energy_values, step, run_id)
    
    if not is_stable:
        # Extract energy value for logging (use max if available)
        energy_value = max(abs(e) for e in energy_values) if energy_values else 0.0
        
        # Handle divergence (logs and raises)
        handle_divergence(run_id, step, energy_value, seed, config)
    
    return True


def log_simulation_runtime(
    run_id: str,
    seed: int,
    status: str,
    duration_seconds: float,
    step: Optional[int] = None,
    divergence_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log simulation runtime information including divergence events.
    
    Args:
        run_id: Unique identifier for this simulation run
        seed: Random seed used for this run
        status: Status of the run (e.g., 'completed', 'aborted', 'divergence_detected')
        duration_seconds: Total runtime in seconds
        step: Optional final step number
        divergence_info: Optional dictionary with divergence details
    """
    init_logging()
    
    log_entry = {
        "timestamp": None,  # Set by log_metric
        "event_type": "simulation_end" if status != "aborted" else "divergence_detected",
        "run_id": run_id,
        "seed": seed,
        "status": status,
        "duration_seconds": duration_seconds
    }
    
    if step is not None:
        log_entry["final_step"] = step
    
    if divergence_info:
        log_entry["divergence_details"] = divergence_info
    
    log_metric(log_entry)


def main() -> None:
    """
    Main function for testing stability checks.
    
    This function demonstrates the divergence detection and abort logic
    by simulating a scenario where energy values exceed the threshold.
    """
    import sys
    
    # Load configuration
    config = load_config()
    seed = config.get("global_seed", 42)
    
    # Initialize logging
    init_logging()
    
    # Test case 1: Normal energy values (should pass)
    print("Test 1: Normal energy values")
    normal_energies = [1.0, 2.5, -1.5, 0.5, 3.2]
    try:
        result = validate_simulation_step(normal_energies, step=10, run_id="test_normal", seed=seed, config=config)
        print(f"  Result: Stable - {result}")
    except SimulationDivergenceError as e:
        print(f"  ERROR: Unexpected divergence - {e}")
        sys.exit(1)
    
    # Test case 2: Divergent energy values (should abort)
    print("\nTest 2: Divergent energy values (should abort)")
    divergent_energies = [1.0, 2.5, 1e7, 0.5, 3.2]  # One value exceeds threshold
    try:
        result = validate_simulation_step(divergent_energies, step=15, run_id="test_divergent", seed=seed, config=config)
        print(f"  ERROR: Should have raised divergence error but got: {result}")
        sys.exit(1)
    except SimulationDivergenceError as e:
        print(f"  Correctly caught divergence: {e}")
        print(f"  Tag: {e.tag}")
    
    print("\nStability checks completed successfully.")

if __name__ == "__main__":
    main()
