"""
Convergence Logger Module.

This module structures and writes convergence data from GLM fitting operations
to a centralized JSON log file for monitoring and reporting purposes.

It is designed to be called by the GLM fitter (T016) to persist convergence
metrics such as iteration counts, tolerance values, and status flags.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from models.replication_result import ReplicationResult

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

CONVERGENCE_LOG_PATH = Path("data/aggregated/convergence_log.json")

class ConvergenceLogger:
    """
    Handles the structure and persistence of GLM convergence data.

    This class collects convergence metrics from individual GLM fits and
    aggregates them into a structured log file.
    """

    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize the ConvergenceLogger.

        Args:
            log_path: Path to the convergence log file. Defaults to
                      data/aggregated/convergence_log.json.
        """
        self.log_path = log_path or CONVERGENCE_LOG_PATH
        self._ensure_directory()
        self._entries: List[Dict[str, Any]] = []

    def _ensure_directory(self) -> None:
        """Ensure the parent directory for the log file exists."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_fit_result(
        self,
        iteration_id: str,
        paradigm_id: str,
        sample_size: int,
        kernel_size: Optional[str],
        max_iterations: int,
        tolerance: float,
        converged: bool,
        message: Optional[str] = None
    ) -> None:
        """
        Log a single GLM fit convergence result.

        Args:
            iteration_id: Unique identifier for the bootstrap iteration.
            paradigm_id: Identifier for the cognitive paradigm used.
            sample_size: Number of subjects in the sample.
            kernel_size: Smoothing kernel size used (e.g., "4mm").
            max_iterations: Maximum iterations allowed or reached.
            tolerance: Convergence tolerance threshold.
            converged: Boolean indicating if the model converged successfully.
            message: Optional message describing the convergence status.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "iteration_id": iteration_id,
            "paradigm_id": paradigm_id,
            "sample_size": sample_size,
            "kernel_size": kernel_size,
            "convergence_details": {
                "max_iterations": max_iterations,
                "tolerance": tolerance,
                "converged": converged,
                "message": message or ("Converged successfully" if converged else "Failed to converge")
            }
        }
        self._entries.append(entry)
        logger.debug(f"Logged convergence for iteration {iteration_id}: {'OK' if converged else 'FAIL'}")

    def save_log(self) -> Path:
        """
        Write the accumulated log entries to the JSON file.

        Returns:
            The path to the saved log file.
        """
        log_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_entries": len(self._entries)
            },
            "convergence_records": self._entries
        }

        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Convergence log saved to {self.log_path}")
        return self.log_path

    def get_convergence_stats(self) -> Dict[str, Any]:
        """
        Calculate basic statistics from the logged entries.

        Returns:
            A dictionary containing counts of total, successful, and failed fits.
        """
        if not self._entries:
            return {"total": 0, "converged": 0, "failed": 0}

        total = len(self._entries)
        converged = sum(1 for e in self._entries if e["convergence_details"]["converged"])
        failed = total - converged

        return {
            "total": total,
            "converged": converged,
            "failed": failed,
            "success_rate": converged / total if total > 0 else 0.0
        }

def log_glm_convergence(
    iteration_id: str,
    paradigm_id: str,
    sample_size: int,
    kernel_size: Optional[str],
    max_iterations: int,
    tolerance: float,
    converged: bool,
    message: Optional[str] = None,
    log_path: Optional[Path] = None
) -> None:
    """
    Convenience function to log a single GLM convergence event.

    This function instantiates a logger, logs the entry, and immediately saves.
    For high-frequency logging, instantiate ConvergenceLogger directly.

    Args:
        iteration_id: Unique identifier for the iteration.
        paradigm_id: Identifier for the paradigm.
        sample_size: Sample size used.
        kernel_size: Smoothing kernel size.
        max_iterations: Max iterations used/reached.
        tolerance: Tolerance used.
        converged: Whether the fit converged.
        message: Optional status message.
        log_path: Optional override for the log file path.
    """
    logger_instance = ConvergenceLogger(log_path)
    logger_instance.log_fit_result(
        iteration_id=iteration_id,
        paradigm_id=paradigm_id,
        sample_size=sample_size,
        kernel_size=kernel_size,
        max_iterations=max_iterations,
        tolerance=tolerance,
        converged=converged,
        message=message
    )
    logger_instance.save_log()

def main() -> None:
    """
    Main entry point for testing the convergence logger.

    This function demonstrates the logger by creating a few dummy entries
    and saving them to the default path.
    """
    logger.info("Running convergence logger demonstration...")

    # Create a logger instance
    conv_logger = ConvergenceLogger()

    # Simulate some log entries
    test_cases = [
        ("iter_001", "Motor", 20, "4mm", 100, 1e-4, True, "Converged normally"),
        ("iter_002", "Motor", 20, "4mm", 100, 1e-4, False, "Max iterations reached"),
        ("iter_003", "WorkingMemory", 30, "8mm", 50, 1e-5, True, "Converged normally"),
    ]

    for case in test_cases:
        conv_logger.log_fit_result(*case)

    # Save to disk
    saved_path = conv_logger.save_log()

    # Print stats
    stats = conv_logger.get_convergence_stats()
    logger.info(f"Log saved to: {saved_path}")
    logger.info(f"Convergence stats: {stats}")

    # Verify file content
    if saved_path.exists():
        with open(saved_path, 'r') as f:
            content = json.load(f)
        logger.info(f"Verified log contains {len(content['convergence_records'])} records.")
    else:
        logger.error("Log file was not created!")
        sys.exit(1)

if __name__ == "__main__":
    main()