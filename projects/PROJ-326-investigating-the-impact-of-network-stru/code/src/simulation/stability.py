"""
Stability checks and runtime monitoring for spin simulations.
Implements divergence detection, numerical stability checks, and runtime logging.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from code.src.utils.logging import log_metric, get_run_log, log_run
from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)


class StabilityError(Exception):
    """Custom exception for stability check failures."""
    pass


def check_for_nan_inf(values: np.ndarray, context: str = "simulation") -> bool:
    """
    Check if values contain NaN or Inf.

    Args:
        values: Array of values to check
        context: Context for logging (default: "simulation")

    Returns:
        True if NaN/Inf found, False otherwise
    """
    if np.any(np.isnan(values)) or np.any(np.isinf(values)):
        logger.error(f"[{context}] NaN or Inf detected in values")
        return True
    return False


def check_value_bounds(
    values: np.ndarray,
    min_val: float = -1e10,
    max_val: float = 1e10,
    context: str = "simulation"
) -> bool:
    """
    Check if values are within acceptable bounds.

    Args:
        values: Array of values to check
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
        context: Context for logging

    Returns:
        True if values out of bounds, False otherwise
    """
    if np.any(values < min_val) or np.any(values > max_val):
        logger.warning(f"[{context}] Values out of bounds: [{values.min()}, {values.max()}]")
        return True
    return False


def check_spatial_variance_stability(
    variance_history: List[float],
    threshold: float = 1e6,
    context: str = "simulation"
) -> bool:
    """
    Check if spatial variance is growing unreasonably.

    Args:
        variance_history: List of variance values over time
        threshold: Maximum acceptable variance
        context: Context for logging

    Returns:
        True if variance is unstable, False otherwise
    """
    if not variance_history:
        return False

    max_variance = max(variance_history)
    if max_variance > threshold:
        logger.warning(f"[{context}] Spatial variance exceeded threshold: {max_variance} > {threshold}")
        return True
    return False


def check_energy_density_stability(
    energy_history: List[float],
    initial_energy: float,
    max_deviation_factor: float = 1e3,
    context: str = "simulation"
) -> bool:
    """
    Check if energy density is within acceptable deviation from initial.

    Args:
        energy_history: List of energy values over time
        initial_energy: Initial energy value
        max_deviation_factor: Maximum allowed deviation factor
        context: Context for logging

    Returns:
        True if energy is unstable, False otherwise
    """
    if not energy_history or initial_energy == 0:
        return False

    max_energy = max(abs(e) for e in energy_history)
    deviation = max_energy / abs(initial_energy)

    if deviation > max_deviation_factor:
        logger.warning(f"[{context}] Energy deviation exceeded: {deviation:.2e} > {max_deviation_factor:.2e}")
        return True
    return False


def detect_divergence(
    metrics: Dict[str, Any],
    initial_energy: float,
    variance_history: List[float],
    energy_history: List[float]
) -> bool:
    """
    Detect if simulation has diverged based on multiple criteria.

    Args:
        metrics: Current simulation metrics
        initial_energy: Initial energy value
        variance_history: History of spatial variance
        energy_history: History of energy values

    Returns:
        True if divergence detected, False otherwise
    """
    # Check for NaN/Inf
    if check_for_nan_inf(np.array(list(metrics.values())), "divergence"):
        logger.error("[SIMULATION_DIVERGENCE] NaN/Inf detected in metrics")
        return True

    # Check variance stability
    if check_spatial_variance_stability(variance_history, threshold=1e6, context="divergence"):
        logger.error("[SIMULATION_DIVERGENCE] Spatial variance instability detected")
        return True

    # Check energy stability
    if check_energy_density_stability(energy_history, initial_energy, max_deviation_factor=1e3, context="divergence"):
        logger.error("[SIMULATION_DIVERGENCE] Energy density instability detected")
        return True

    return False


def run_full_stability_check(
    metrics: Dict[str, Any],
    initial_energy: float,
    variance_history: List[float],
    energy_history: List[float],
    threshold: float = 1e6
) -> Tuple[bool, str]:
    """
    Run comprehensive stability checks.

    Args:
        metrics: Current simulation metrics
        initial_energy: Initial energy value
        variance_history: History of spatial variance
        energy_history: History of energy values
        threshold: Variance threshold

    Returns:
        Tuple of (is_stable, status_message)
    """
    is_divergent = detect_divergence(metrics, initial_energy, variance_history, energy_history)

    if is_divergent:
        return False, "[SIMULATION_DIVERGENCE]"

    # Additional checks
    if check_for_nan_inf(np.array(list(metrics.values())), "stability"):
        return False, "[STABILITY_NAN_INF]"

    if check_value_bounds(np.array(list(metrics.values())), context="stability"):
        return False, "[STABILITY_BOUNDS]"

    return True, "STABLE"


def validate_metrics_stability(metrics: Dict[str, Any]) -> bool:
    """
    Validate that metrics are numerically stable.

    Args:
        metrics: Metrics dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    logger.error(f"Invalid metric value for {key}: {value}")
                    return False
        return True
    except Exception as e:
        logger.error(f"Error validating metrics: {e}")
        return False


class RuntimeLogger:
    """
    Manages runtime duration logging for simulation runs.
    Records runtime_duration_seconds to data/run_log.json (FR-009).
    """

    def __init__(self, run_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the runtime logger.

        Args:
            run_id: Unique identifier for the simulation run
        """
        self.run_id = run_id
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_seconds: float = 0.0
        self.config = config or {}
        self.log_path = Path("data/run_log.json")

    def start(self) -> None:
        """Start the runtime timer."""
        self.start_time = time.time()
        logger.info(f"[RuntimeLogger] Run {self.run_id} started at {datetime.now().isoformat()}")

    def stop(self) -> None:
        """Stop the runtime timer and calculate duration."""
        if self.start_time is None:
            logger.warning(f"[RuntimeLogger] Attempted to stop without starting run {self.run_id}")
            return

        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        logger.info(f"[RuntimeLogger] Run {self.run_id} completed in {self.duration_seconds:.4f} seconds")

        # Log to run_log.json
        self._log_duration()

    def _log_duration(self) -> None:
        """
        Log the runtime duration to data/run_log.json.
        This implements FR-009: explicit runtime logging infrastructure.
        """
        ensure_data_directory(self.log_path)

        # Load existing log or create new
        try:
            with open(self.log_path, 'r') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_data = {"runs": []}

        # Create run entry
        run_entry = {
            "run_id": self.run_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "runtime_duration_seconds": self.duration_seconds,
            "status": "COMPLETED"
        }

        # Append to runs list
        if "runs" not in log_data:
            log_data["runs"] = []
        log_data["runs"].append(run_entry)

        # Write back
        with open(self.log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        logger.debug(f"[RuntimeLogger] Logged duration {self.duration_seconds:.4f}s for run {self.run_id} to {self.log_path}")


def log_runtime_duration(
    run_id: str,
    duration_seconds: float,
    status: str = "COMPLETED",
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Convenience function to log runtime duration directly.

    Args:
        run_id: Unique identifier for the run
        duration_seconds: Duration in seconds
        status: Status of the run (default: "COMPLETED")
    """
    ensure_data_directory(Path("data/run_log.json"))

    log_path = Path("data/run_log.json")
    try:
        with open(log_path, 'r') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"runs": []}

    run_entry = {
        "run_id": run_id,
        "runtime_duration_seconds": duration_seconds,
        "status": status,
        "logged_at": datetime.now().isoformat()
    }

    if "runs" not in log_data:
        log_data["runs"] = []
    log_data["runs"].append(run_entry)

    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"Logged runtime {duration_seconds:.4f}s for run {run_id} to {log_path}")


def main() -> None:
    """
    Main entry point for stability module testing.
    Demonstrates runtime logging functionality.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Stability module CLI")
    parser.add_argument("--run-id", type=str, default="test_run", help="Run ID for logging")
    parser.add_argument("--duration", type=float, default=1.0, help="Simulated duration in seconds")
    args = parser.parse_args()

    logger.info(f"Testing stability module with run_id={args.run_id}")

    # Test runtime logging
    logger = RuntimeLogger(args.run_id)
    logger.start()
    time.sleep(args.duration)
    logger.stop()

    print(f"Runtime logged for run {args.run_id}: {logger.duration_seconds:.4f}s")