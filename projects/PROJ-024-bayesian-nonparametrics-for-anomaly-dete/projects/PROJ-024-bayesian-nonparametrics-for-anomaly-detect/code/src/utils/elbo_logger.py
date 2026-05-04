"""ELBO Convergence Logging Utility for DPGMM Training.

Implements Constitution Principle VI: All training runs must log ELBO
convergence to enable reproducibility and hyperparameter tuning analysis.

Logs are stored in logs/elbo/ with JSON format for programmatic analysis.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ELBOHistory:
    """ELBO convergence history for a single training run."""
    run_id: str
    timestamp: str
    elbo_values: List[float] = field(default_factory=list)
    iteration_counts: List[int] = field(default_factory=list)
    stopping_reason: Optional[str] = None
    final_elbo: Optional[float] = None
    convergence_threshold: Optional[float] = None
    max_iterations: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_elbo(self, iteration: int, elbo_value: float) -> None:
        """Record an ELBO value at a given iteration."""
        self.iteration_counts.append(iteration)
        self.elbo_values.append(float(elbo_value))
        self.final_elbo = float(elbo_value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'ELBOHistory':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class ELBOLogger:
    """ELBO convergence logger for DPGMM training runs.

    Logs ELBO values at each iteration to enable:
    - Convergence verification (stopping criteria)
    - Hyperparameter tuning analysis
    - Reproducibility auditing (Constitution Principle VI)

    Output format: logs/elbo/{run_id}_{timestamp}.json
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        run_id: Optional[str] = None,
        convergence_threshold: float = 1e-3,
        min_iterations: int = 10,
        max_iterations: int = 1000
    ):
        """Initialize ELBO logger.

        Args:
            log_dir: Directory for ELBO logs. Defaults to logs/elbo/
            run_id: Unique identifier for this training run.
            convergence_threshold: ELBO change threshold for convergence.
            min_iterations: Minimum iterations before convergence check.
            max_iterations: Maximum iterations allowed.
        """
        if log_dir is None:
            log_dir = Path("logs/elbo")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = run_id
        self.timestamp = datetime.now().isoformat()

        self.convergence_threshold = convergence_threshold
        self.min_iterations = min_iterations
        self.max_iterations = max_iterations

        self.history = ELBOHistory(
            run_id=self.run_id,
            timestamp=self.timestamp,
            convergence_threshold=convergence_threshold,
            max_iterations=max_iterations
        )

        self._consecutive_changes: List[float] = []
        self._last_elbo: Optional[float] = None
        self._converged: bool = False
        self._convergence_iteration: Optional[int] = None

    def log_iteration(self, iteration: int, elbo_value: float) -> Dict[str, Any]:
        """Log ELBO value at a training iteration.

        Args:
            iteration: Current iteration number.
            elbo_value: ELBO value at this iteration.

        Returns:
            Dict with logging status and convergence information.
        """
        # Record the ELBO value
        self.history.add_elbo(iteration, elbo_value)

        # Track convergence
        elbo_value = float(elbo_value)
        if self._last_elbo is not None:
            change = abs(elbo_value - self._last_elbo)
            self._consecutive_changes.append(change)

            # Check convergence after minimum iterations
            if iteration >= self.min_iterations:
                recent_changes = self._consecutive_changes[-self.min_iterations:]
                avg_change = np.mean(recent_changes)

                if avg_change < self.convergence_threshold:
                    self._converged = True
                    self._convergence_iteration = iteration
                    self.history.stopping_reason = f"converged_at_iter_{iteration}"
                    logger.info(
                        f"ELBO converged at iteration {iteration} "
                        f"(avg change: {avg_change:.6e} < {self.convergence_threshold:.6e})"
                    )
        else:
            self._consecutive_changes = []

        self._last_elbo = elbo_value

        # Check max iterations
        if iteration >= self.max_iterations and not self._converged:
            self._converged = True
            self.history.stopping_reason = f"max_iterations_{self.max_iterations}"
            logger.info(
                f"ELBO reached max iterations {self.max_iterations} "
                f"(final ELBO: {elbo_value:.4f})"
            )

        return {
            "iteration": iteration,
            "elbo": elbo_value,
            "converged": self._converged,
            "convergence_iteration": self._convergence_iteration,
            "should_stop": self._converged
        }

    def get_history(self) -> ELBOHistory:
        """Get the complete ELBO history."""
        return self.history

    def get_elbo_array(self) -> np.ndarray:
        """Get ELBO values as numpy array."""
        return np.array(self.history.elbo_values)

    def get_iteration_array(self) -> np.ndarray:
        """Get iteration numbers as numpy array."""
        return np.array(self.history.iteration_counts)

    def save(self, filename: Optional[str] = None) -> Path:
        """Save ELBO history to JSON file.

        Args:
            filename: Optional filename. Defaults to {run_id}_{timestamp}.json

        Returns:
            Path to saved file.
        """
        if filename is None:
            filename = f"{self.run_id}_{self.timestamp.replace(':', '-')}.json"

        filepath = self.log_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.history.to_json())

        logger.info(f"ELBO history saved to {filepath}")
        return filepath

    def save_csv(self, filename: Optional[str] = None) -> Path:
        """Save ELBO history to CSV file for quick inspection.

        Args:
            filename: Optional filename. Defaults to {run_id}_{timestamp}.csv

        Returns:
            Path to saved file.
        """
        if filename is None:
            filename = f"{self.run_id}_{self.timestamp.replace(':', '-')}.csv"

        filepath = self.log_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("iteration,elbo,converged\n")
            for i, (iter_num, elbo) in enumerate(
                zip(self.history.iteration_counts, self.history.elbo_values)
            ):
                converged = (
                    "true"
                    if self._converged and self._convergence_iteration == iter_num
                    else "false"
                )
                f.write(f"{iter_num},{elbo:.6f},{converged}\n")

        logger.info(f"ELBO history saved to {filepath}")
        return filepath

    def plot_convergence(
        self,
        filename: Optional[str] = None,
        save: bool = True,
        show: bool = False
    ) -> Optional[Path]:
        """Plot ELBO convergence curve.

        Args:
            filename: Optional filename for saved plot.
            save: Whether to save the plot to file.
            show: Whether to display the plot.

        Returns:
            Path to saved plot file, or None if not saved.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not available, skipping ELBO plot")
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        iterations = self.get_iteration_array()
        elbos = self.get_elbo_array()

        ax.plot(iterations, elbos, 'b-', linewidth=2, label='ELBO')
        ax.set_xlabel('Iteration', fontsize=12)
        ax.set_ylabel('ELBO Value', fontsize=12)
        ax.set_title(f'ELBO Convergence - {self.run_id}', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()

        if self._converged and self._convergence_iteration is not None:
            ax.axvline(
                x=self._convergence_iteration,
                color='r',
                linestyle='--',
                label=f'Converged (iter {self._convergence_iteration})'
            )
            ax.legend()

        if save:
            if filename is None:
                filename = f"{self.run_id}_{self.timestamp.replace(':', '-')}_elbo.png"
            filepath = self.log_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            logger.info(f"ELBO plot saved to {filepath}")
            plt.close(fig)
            return filepath

        if show:
            plt.show()

        plt.close(fig)
        return None


def create_elbo_logger(
    log_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
    **kwargs
) -> ELBOLogger:
    """Factory function to create an ELBO logger.

    Args:
        log_dir: Directory for ELBO logs.
        run_id: Unique identifier for this training run.
        **kwargs: Additional arguments passed to ELBOLogger.

    Returns:
        Configured ELBOLogger instance.
    """
    return ELBOLogger(log_dir=log_dir, run_id=run_id, **kwargs)


def load_elbo_history(filepath: Path) -> ELBOHistory:
    """Load ELBO history from JSON file.

    Args:
        filepath: Path to ELBO history JSON file.

    Returns:
        ELBOHistory instance.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return ELBOHistory.from_json(f.read())


def aggregate_elbo_runs(
    log_dir: Path,
    pattern: str = "*.json"
) -> List[ELBOHistory]:
    """Aggregate ELBO histories from multiple training runs.

    Args:
        log_dir: Directory containing ELBO history files.
        pattern: Glob pattern for matching files.

    Returns:
        List of ELBOHistory instances.
    """
    histories = []
    for filepath in log_dir.glob(pattern):
        if filepath.suffix == '.json':
            try:
                histories.append(load_elbo_history(filepath))
            except Exception as e:
                logger.warning(f"Failed to load {filepath}: {e}")
    return histories


def main():
    """Demo/test of ELBO logging functionality."""
    import sys
    from pathlib import Path

    # Create test logger
    log_dir = Path("logs/elbo")
    logger = create_elbo_logger(log_dir=log_dir, run_id="test_elbo_logging")

    # Simulate training iterations
    print("Testing ELBO logging...")
    for i in range(100):
        # Simulate ELBO convergence
        elbo = -1000 + 500 * (1 - np.exp(-i / 20)) + np.random.normal(0, 0.1)
        result = logger.log_iteration(i, elbo)

        if i % 10 == 0:
            print(f"Iter {i}: ELBO={elbo:.4f}, Converged={result['converged']}")

        if result['should_stop']:
            print(f"Training stopped at iteration {i}")
            break

    # Save results
    json_path = logger.save()
    csv_path = logger.save_csv()
    print(f"\nSaved to: {json_path}, {csv_path}")

    # Test loading
    loaded = load_elbo_history(json_path)
    print(f"Loaded run_id: {loaded.run_id}, iterations: {len(loaded.elbo_values)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
