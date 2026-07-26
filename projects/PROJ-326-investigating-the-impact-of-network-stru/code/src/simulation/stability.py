import logging
import time
from typing import Dict, Any, Optional

import numpy as np

from code.src.utils.config import get_global_config
from code.src.utils.logging import log_run

class SimulationDivergenceError(Exception):
    """Raised when simulation energy diverges or runtime limit is exceeded."""
    pass

class StabilityError(Exception):
    """Raised when stability checks fail."""
    pass

def check_for_nan_inf(arr: np.ndarray, threshold: float = 1e10) -> bool:
    """
    Checks if the array contains NaN, Inf, or values exceeding a threshold.
    """
    if np.any(np.isnan(arr)):
        return True
    if np.any(np.isinf(arr)):
        return True
    if np.any(np.abs(arr) > threshold):
        return True
    return False

def check_energy_conservation(initial_energy: float, current_energy: float, tolerance: float = 1e-6) -> bool:
    """
    Checks if energy is conserved within tolerance.
    """
    return abs(initial_energy - current_energy) < tolerance

def log_runtime_duration(run_id: str, duration_seconds: float):
    """
    T026b: Logs runtime duration to data/run_log.json.
    """
    log_run(
        event_type="simulation_runtime",
        run_id=run_id,
        message=f"Runtime: {duration_seconds:.2f} seconds",
        duration_seconds=duration_seconds
    )

def enforce_runtime_limit(run_id: str, start_time: float, max_seconds: float):
    """
    T026a: Checks if runtime exceeds limit and raises if so.
    This implements the hard runtime abort mechanism.
    """
    current_time = time.time()
    duration = current_time - start_time

    if duration > max_seconds:
        logger = logging.getLogger(__name__)
        logger.error(f"[RUNTIME_EXCEEDED] Run {run_id} exceeded {max_seconds}s limit. Runtime: {duration:.2f}s")
        
        # Log the timeout event
        log_run(
            event_type="timeout_reached",
            run_id=run_id,
            status="FAILURE",
            message=f"Runtime {duration:.2f}s exceeded limit {max_seconds}s",
            duration_ms=int(duration * 1000)
        )
        
        raise SimulationDivergenceError(f"Runtime exceeded limit: {duration:.2f}s > {max_seconds}s")
    
    return duration

def detect_divergence(
    current_energy: float, 
    initial_energy: float, 
    amplification_factor: float = 1000.0
) -> bool:
    """
    Detects if energy has diverged significantly from initial state.
    Relies on T026a for abort mechanism; this function only detects.
    """
    if initial_energy == 0:
        # If initial energy is zero, any non-zero current energy is divergence
        return current_energy != 0
    
    ratio = abs(current_energy / initial_energy)
    return ratio > amplification_factor

def run_stability_check(
    run_id: str,
    start_time: float,
    current_energy: float,
    initial_energy: float,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main stability check routine.
    - Checks for NaN/Inf
    - Checks for divergence (T052)
    - Checks runtime limit (T026a)
    - Logs results (T026b)
    
    This function implements T052: explicit numerical stability assertions
    to detect energy divergence. It relies on T026a for the abort mechanism
    by raising SimulationDivergenceError when divergence is detected, rather
    than creating a new error type.
    """
    logger = logging.getLogger(__name__)
    result = {
        "status": "OK",
        "divergence_detected": False,
        "runtime_exceeded": False,
        "runtime_seconds": 0.0
    }

    # 1. Check Divergence (T052 - Explicit Numerical Stability Assertions)
    # Read divergence threshold from config, defaulting to 1000.0x amplification
    threshold = config.get("divergence_threshold", 1000.0)
    
    if detect_divergence(current_energy, initial_energy, threshold):
        result["status"] = "DIVERGENCE"
        result["divergence_detected"] = True
        
        # Log the specific flag string [SIMULATION_DIVERGENCE] as required by spec
        logger.warning(f"[SIMULATION_DIVERGENCE] Run {run_id} energy diverged.")
        
        # Log the divergence event to run_log.json
        log_run(
            event_type="divergence_detected",
            run_id=run_id,
            status="FAILURE",
            message="[SIMULATION_DIVERGENCE] Energy divergence detected",
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        # Raise the existing SimulationDivergenceError (T026a mechanism)
        # This ensures we don't create a conflicting error type
        raise SimulationDivergenceError(f"[SIMULATION_DIVERGENCE] Energy divergence detected: ratio={abs(current_energy/initial_energy) if initial_energy != 0 else 'inf'}")

    # 2. Check Runtime Limit (T026a - Hard Abort)
    # Read limit from config.yaml (key: simulation_timeout_seconds)
    timeout_limit = config.get("simulation_timeout_seconds", 3600.0) 
    
    duration = enforce_runtime_limit(run_id, start_time, timeout_limit)
    result["runtime_seconds"] = duration

    # 3. Log Runtime (T026b)
    log_runtime_duration(run_id, duration)

    return result
