"""
Stability checks for simulation runs.
Implements divergence detection, runtime abort, and runtime logging.
"""
import json
import logging
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from code.src.utils.config import load_config
from code.src.utils.logging import log_run, get_run_log

class StabilityError(Exception):
    """Custom exception for stability-related failures."""
    pass

class SimulationDivergenceError(StabilityError):
    """Raised when simulation energy diverges beyond acceptable limits."""
    pass

class RuntimeExceededError(StabilityError):
    """Raised when simulation runtime exceeds the configured limit."""
    pass

logger = logging.getLogger(__name__)

def check_for_nan_inf(value: float, context: str = "Simulation value") -> None:
    """
    Check if a value is NaN or Inf.
    Raises StabilityError if invalid.
    """
    if np.isnan(value) or np.isinf(value):
        error_msg = f"{context} is invalid: {value}"
        logger.error(error_msg)
        raise StabilityError(error_msg)

def check_energy_divergence(
    current_energy: float,
    initial_energy: float,
    threshold_factor: float = 100.0
) -> bool:
    """
    Check if current energy has diverged significantly from initial.
    Returns True if divergence is detected.
    """
    if initial_energy == 0:
        # Avoid division by zero; check absolute threshold if initial is zero
        if abs(current_energy) > 1e6:
            return True
        return False

    ratio = abs(current_energy) / abs(initial_energy)
    return ratio > threshold_factor

def enforce_runtime_limit(
    start_time: float,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Check if runtime exceeds the limit defined in config.
    Raises RuntimeExceededError if limit is exceeded.
    Logs [RUNTIME_EXCEEDED] flag if triggered.
    """
    if config is None:
        config = load_config()

    # Read timeout from config.yaml under simulation_params
    timeout_seconds = config.get("simulation_params", {}).get(
        "simulation_timeout_seconds", 3600
    )

    current_time = time.time()
    runtime_duration = current_time - start_time

    if runtime_duration > timeout_seconds:
        error_msg = (
            f"Simulation runtime ({runtime_duration:.2f}s) exceeded "
            f"limit ({timeout_seconds}s). Aborting."
        )
        logger.error(error_msg)
        
        # Log the flag as per spec edge case
        log_run(
            event_type="simulation_runtime",
            run_id="runtime_exceeded",
            status="RUNTIME_EXCEEDED",
            duration_ms=int(runtime_duration * 1000)
        )
        
        raise RuntimeExceededError(error_msg)

def log_simulation_runtime(
    run_id: str,
    start_time: float,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Calculate runtime duration and log it to data/run_log.json.
    Implements FR-009: explicit runtime logging infrastructure.

    Args:
        run_id: Unique identifier for the simulation run.
        start_time: Timestamp when the simulation started (float).
        config: Optional config dict. If None, loads from default.
    """
    if config is None:
        config = load_config()

    # Calculate duration
    current_time = time.time()
    duration_seconds = current_time - start_time

    # Ensure data directory exists
    log_path = Path("data/run_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log or initialize
    log_data = get_run_log()
    if log_data is None:
        log_data = []

    # Create new entry
    entry = {
        "event_type": "simulation_runtime",
        "run_id": run_id,
        "duration_seconds": float(duration_seconds),
        "timestamp": datetime.utcnow().isoformat()
    }

    log_data.append(entry)

    # Save back to file
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"Logged runtime for run {run_id}: {duration_seconds:.4f}s")

def run_stability_checks(
    start_time: float,
    run_id: str,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Wrapper to run all stability checks including runtime logging.
    This function is called at the end of a simulation run to:
    1. Check if runtime limit was exceeded (abort if so).
    2. Log the runtime duration to data/run_log.json.

    Args:
        start_time: Timestamp when simulation started.
        run_id: Unique identifier for the run.
        config: Optional config dict.
    """
    # First, check if we exceeded the runtime limit (abort if so)
    enforce_runtime_limit(start_time, config)

    # Then, log the runtime duration (FR-009)
    log_simulation_runtime(run_id, start_time, config)

def main() -> None:
    """
    Entry point for standalone execution (e.g., testing stability checks).
    """
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    run_id = "test_stability_run"
    start = time.time()

    # Simulate some work
    time.sleep(0.1)

    # Run stability checks
    try:
        run_stability_checks(start, run_id, config)
        print(f"Stability checks passed for {run_id}")
    except RuntimeExceededError as e:
        print(f"Runtime exceeded: {e}")
        sys.exit(1)
    except StabilityError as e:
        print(f"Stability error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()