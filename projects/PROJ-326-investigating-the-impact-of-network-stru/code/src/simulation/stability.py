"""
Stability checks and runtime abort mechanisms for spin simulations.
"""
import logging
import signal
import threading
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from code.src.utils.logging import log_metric
from code.src.utils.config import get_global_config

logger = logging.getLogger(__name__)


class SimulationTimeoutError(Exception):
    """Raised when a simulation exceeds the configured time limit."""
    pass


class SimulationDivergenceError(Exception):
    """Raised when numerical divergence is detected in simulation dynamics."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout events."""
    raise SimulationTimeoutError("Simulation exceeded maximum allowed runtime.")


def setup_timeout_handler(timeout_seconds: int):
    """
    Configure a hard timeout for the current process using signal.alarm (Unix).
    
    Args:
        timeout_seconds: Maximum allowed runtime in seconds.
    """
    if hasattr(signal, 'alarm'):
        # Unix systems
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_seconds)
        logger.info(f"Timeout handler set to {timeout_seconds} seconds (Unix).")
    else:
        # Windows or non-Unix systems: use threading.Timer as fallback
        # Note: threading.Timer cannot interrupt arbitrary code, but we will
        # rely on cooperative checking in the simulation loop or raise an error
        # if the timer fires before the simulation completes.
        logger.warning("signal.alarm not available; using threading.Timer fallback.")
        timer = threading.Timer(timeout_seconds, lambda: exec("raise SimulationTimeoutError('Simulation exceeded time limit.')"))
        timer.daemon = True
        timer.start()
        logger.info(f"Timeout handler set to {timeout_seconds} seconds (Thread Timer).")


def cancel_timeout_handler():
    """Cancel any active timeout handler."""
    if hasattr(signal, 'alarm'):
        signal.alarm(0)
    # For threading.Timer, we cannot easily cancel if we didn't keep a reference,
    # but in typical usage, we will clear it explicitly if we have the reference.
    # If a timer fired, the exception would have already been raised.


def check_numerical_stability(energy_profile: list, threshold: float = 1e6) -> bool:
    """
    Check if the energy profile shows signs of numerical divergence.
    
    Args:
        energy_profile: List of energy values over time steps.
        threshold: Maximum allowed absolute energy value.
    
    Returns:
        True if stable, False if divergence detected.
    """
    if not energy_profile:
        return True
    
    max_energy = max(abs(e) for e in energy_profile)
    if max_energy > threshold:
        logger.error(f"Numerical divergence detected: max energy {max_energy} exceeds threshold {threshold}")
        return False
    return True


def validate_energy_conservation(energy_profile: list, tolerance: float = 1e-3) -> bool:
    """
    Validate that energy is conserved within a specified tolerance.
    
    Args:
        energy_profile: List of energy values over time steps.
        tolerance: Maximum allowed relative change in energy.
    
    Returns:
        True if conserved, False otherwise.
    """
    if len(energy_profile) < 2:
        return True
    
    initial_energy = energy_profile[0]
    if abs(initial_energy) < 1e-9:
        # Avoid division by zero; check absolute difference instead
        max_diff = max(abs(e - initial_energy) for e in energy_profile)
        return max_diff < tolerance
    
    max_relative_change = max(abs((e - initial_energy) / initial_energy) for e in energy_profile)
    return max_relative_change <= tolerance


def log_simulation_runtime(
    run_id: str,
    seed: int,
    duration_seconds: float,
    status: str = "completed",
    event_type: str = "simulation_end"
):
    """
    Log simulation runtime metrics to the run log.
    
    Args:
        run_id: Unique identifier for the simulation run.
        seed: Random seed used for the run.
        duration_seconds: Actual runtime duration.
        status: Status of the run (e.g., 'completed', 'timeout', 'divergence').
        event_type: Type of log event.
    """
    log_metric(
        event_type=event_type,
        run_id=run_id,
        seed=seed,
        status=status,
        duration_seconds=duration_seconds,
        extra_fields={"runtime_duration_seconds": duration_seconds}
    )


def run_with_timeout(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    timeout_seconds: Optional[int] = None,
    run_id: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a simulation function with a hard timeout and logging.
    
    Args:
        func: The simulation function to run.
        args: Positional arguments for func.
        kwargs: Keyword arguments for func.
        timeout_seconds: Maximum allowed runtime. If None, reads from config.
        run_id: Run ID for logging.
        seed: Seed for logging.
    
    Returns:
        Dictionary containing simulation results and runtime metadata.
    
    Raises:
        SimulationTimeoutError: If the simulation exceeds the time limit.
        SimulationDivergenceError: If numerical divergence is detected.
    """
    if kwargs is None:
        kwargs = {}
    
    # Get timeout from config if not provided
    if timeout_seconds is None:
        config = get_global_config()
        timeout_seconds = config.get("simulation_params", {}).get("timeout_seconds", 3600)
    
    start_time = time.time()
    result = None
    status = "completed"
    
    try:
        # Set up timeout handler
        setup_timeout_handler(timeout_seconds)
        
        # Run the simulation
        result = func(*args, **kwargs)
        
        # Cancel timeout on success
        cancel_timeout_handler()
        
    except SimulationTimeoutError as e:
        status = "timeout"
        logger.error(f"Simulation timed out after {timeout_seconds} seconds: {e}")
        cancel_timeout_handler()
        raise
    
    except SimulationDivergenceError as e:
        status = "divergence_detected"
        logger.error(f"Simulation diverged: {e}")
        raise
    
    except Exception as e:
        status = "error"
        logger.error(f"Simulation failed with unexpected error: {e}")
        raise
    
    finally:
        duration = time.time() - start_time
        
        # Log runtime metrics
        if run_id is not None and seed is not None:
            log_simulation_runtime(
                run_id=run_id,
                seed=seed,
                duration_seconds=duration,
                status=status
            )
        
        # Attach runtime info to result if available
        if result is not None and isinstance(result, dict):
            result["runtime_duration_seconds"] = duration
            result["status"] = status
        
    return result
