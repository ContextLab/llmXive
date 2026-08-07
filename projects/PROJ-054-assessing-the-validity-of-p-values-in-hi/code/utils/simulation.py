"""
Simulation orchestration framework for high-dimensional p-value validity assessment.

This module provides the core infrastructure for managing simulation iterations,
seeds, parameter sweeps, and memory monitoring.
"""

from __future__ import annotations

import hashlib
import json
import logging
import multiprocessing
import random
import os
import resource
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple

import numpy as np

from utils.exceptions import SimulationError

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""
    n: int  # Sample size
    p: int  # Number of features/dimensions
    rho: float  # Correlation threshold
    seed: int  # Random seed
    distribution_type: str = "normal"  # Distribution type: "normal", "t", "skew"
    n_iterations: int = 100  # Number of simulation iterations
    t_distribution_df: int = 5  # Degrees of freedom for t-distribution (if used)
    skewness_param: float = 2.0  # Skewness parameter (if used)

    def __post_init__(self):
        if self.n <= 0 or self.p <= 0:
            raise SimulationError("n and p must be positive integers")
        if not 0 <= self.rho <= 1:
            raise SimulationError("rho must be between 0 and 1")
        if self.distribution_type not in ["normal", "t", "skew"]:
            raise SimulationError(f"Unknown distribution type: {self.distribution_type}")


@dataclass
class SyntheticDataset:
    """Represents a generated synthetic dataset with metadata."""
    seed: int
    n: int
    p: int
    rho: float
    distribution_type: str
    data: np.ndarray  # Shape (n, p)
    correlation_matrix: np.ndarray  # Shape (p, p)
    sha256: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Compute hash if not provided
        if not self.sha256:
            content = json.dumps({
                "seed": self.seed,
                "n": self.n,
                "p": self.p,
                "rho": self.rho,
                "distribution_type": self.distribution_type,
                "data_shape": list(self.data.shape)
            }, sort_keys=True)
            self.sha256 = hashlib.sha256(content.encode('utf-8')).hexdigest()


class MemoryMonitor:
    """
    Memory monitor that logs warnings if RSS exceeds a threshold.

    This is used to detect memory pressure during large simulations.
    Threshold is set to 6GB (6144 MB) as per T007 specification.
    """

    def __init__(self, threshold_mb: int = 6144):
        self.threshold_mb = threshold_mb
        self._logger = logging.getLogger(self.__class__.__name__)

    def check_memory(self) -> bool:
        """
        Check current memory usage and log a warning if exceeded.

        Returns:
            True if memory usage is within limits, False if exceeded.
        """
        try:
            # Get RSS (Resident Set Size) in bytes
            usage = resource.getrusage(resource.RUSAGE_SELF)
            rss_mb = usage.ru_maxrss / 1024  # Convert KB to MB on Linux

            if rss_mb > self.threshold_mb:
                self._logger.warning(
                    f"Memory usage ({rss_mb:.0f} MB) exceeds threshold ({self.threshold_mb} MB). "
                    "Consider reducing simulation size or increasing system memory."
                )
                return False
            return True
        except Exception as e:
            self._logger.warning(f"Could not check memory usage: {e}")
            return True


class SimulationOrchestrator:
    """
    Orchestrates simulation runs across parameter sweeps and iterations.

    Manages:
    - Iteration loops
    - Seed management
    - Parameter sweeps (n, p, rho)
    - Memory monitoring
    - Callbacks for data generation and analysis
    """

    def __init__(
        self,
        config: SimulationConfig,
        data_generator: Callable[[SimulationConfig], SyntheticDataset],
        test_runner: Callable[[SyntheticDataset], List[float]],
        trajectory_writer: Optional[Callable[[int, List[float], Dict[str, Any]], Path]] = None,
        memory_threshold_mb: int = 6144
    ):
        self.config = config
        self.data_generator = data_generator
        self.test_runner = test_runner
        self.trajectory_writer = trajectory_writer
        self.memory_monitor = MemoryMonitor(threshold_mb=memory_threshold_mb)
        self.results: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(self.__class__.__name__)

    def run_single_iteration(self, iteration_idx: int) -> Optional[Dict[str, Any]]:
        """
        Run a single simulation iteration.

        Args:
            iteration_idx: Index of the current iteration.

        Returns:
            Dictionary with iteration results, or None if failed.
        """
        try:
            # Check memory before each iteration
            if not self.memory_monitor.check_memory():
                self._logger.warning("Memory threshold exceeded, proceeding with caution.")

            # Set seed for this iteration
            iteration_seed = self.config.seed + iteration_idx
            np.random.seed(iteration_seed)
            random.seed(iteration_seed)

            # Generate data
            dataset = self.data_generator(self.config)

            # Run hypothesis tests
            pvalues = self.test_runner(dataset)

            # Validate we got exactly p p-values
            if len(pvalues) != self.config.p:
                self._logger.warning(
                    f"Iteration {iteration_idx}: Expected {self.config.p} p-values, "
                    f"got {len(pvalues)}"
                )

            # Write trajectory if writer is provided
            trajectory_path = None
            if self.trajectory_writer:
                metadata = {
                    "n": self.config.n,
                    "p": self.config.p,
                    "rho": self.config.rho,
                    "distribution_type": self.config.distribution_type,
                    "iteration": iteration_idx
                }
                trajectory_path = self.trajectory_writer(
                    seed=iteration_seed,
                    pvalues=pvalues,
                    metadata=metadata
                )

            result = {
                "iteration": iteration_idx,
                "seed": iteration_seed,
                "pvalues": pvalues,
                "n_pvalues": len(pvalues),
                "trajectory_path": str(trajectory_path) if trajectory_path else None
            }
            self.results.append(result)
            return result

        except Exception as e:
            self._logger.error(f"Iteration {iteration_idx} failed: {e}")
            return None

    def run_sweep(
        self,
        n_values: List[int],
        p_values: List[int],
        rho_values: List[float],
        n_iterations_per_config: int
    ) -> List[Dict[str, Any]]:
        """
        Run a full parameter sweep.

        Args:
            n_values: List of sample sizes to test.
            p_values: List of feature counts to test.
            rho_values: List of correlation thresholds to test.
            n_iterations_per_config: Number of iterations per configuration.

        Returns:
            List of all results from the sweep.
        """
        all_results = []

        for n in n_values:
            for p in p_values:
                for rho in rho_values:
                    self._logger.info(
                        f"Running sweep: n={n}, p={p}, rho={rho}"
                    )

                    # Update config
                    sweep_config = SimulationConfig(
                        n=n,
                        p=p,
                        rho=rho,
                        seed=self.config.seed,
                        distribution_type=self.config.distribution_type,
                        n_iterations=n_iterations_per_config
                    )

                    # Create new orchestrator for this config
                    orchestrator = SimulationOrchestrator(
                        config=sweep_config,
                        data_generator=self.data_generator,
                        test_runner=self.test_runner,
                        trajectory_writer=self.trajectory_writer,
                        memory_threshold_mb=self.memory_monitor.threshold_mb
                    )

                    # Run iterations
                    for i in range(n_iterations_per_config):
                        result = orchestrator.run_single_iteration(i)
                        if result:
                            result["config"] = {
                                "n": n,
                                "p": p,
                                "rho": rho
                            }
                            all_results.append(result)

        self.results = all_results
        return all_results

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all simulation results.

        Returns:
            Dictionary with summary statistics.
        """
        if not self.results:
            return {"total_iterations": 0, "successful_iterations": 0}

        total_iterations = len(self.results)
        successful_iterations = sum(
            1 for r in self.results if r.get("n_pvalues", 0) > 0
        )

        # Aggregate p-values
        all_pvalues = []
        for r in self.results:
            all_pvalues.extend(r.get("pvalues", []))

        return {
            "total_iterations": total_iterations,
            "successful_iterations": successful_iterations,
            "total_pvalues_collected": len(all_pvalues),
            "pvalue_range": {
                "min": min(all_pvalues) if all_pvalues else None,
                "max": max(all_pvalues) if all_pvalues else None,
                "mean": float(np.mean(all_pvalues)) if all_pvalues else None,
                "median": float(np.median(all_pvalues)) if all_pvalues else None
            }
        }


def main():
    """
    Main entry point for simulation orchestration.

    This function demonstrates the usage of the SimulationOrchestrator
    with a simple parameter sweep.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run simulation sweep for p-value validity assessment."
    )
    parser.add_argument(
        "--n-values",
        type=str,
        default="100,500,1000",
        help="Comma-separated list of sample sizes (n)."
    )
    parser.add_argument(
        "--p-values",
        type=str,
        default="50,200,500",
        help="Comma-separated list of feature counts (p)."
    )
    parser.add_argument(
        "--rho-values",
        type=str,
        default="0.0,0.3,0.7",
        help="Comma-separated list of correlation thresholds (rho)."
    )
    parser.add_argument(
        "--n-iterations",
        type=int,
        default=10,
        help="Number of iterations per configuration."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/simulation_summary.json",
        help="Path to save summary results."
    )

    args = parser.parse_args()

    # Parse inputs
    n_values = [int(x) for x in args.n_values.split(",")]
    p_values = [int(x) for x in args.p_values.split(",")]
    rho_values = [float(x) for x in args.rho_values.split(",")]

    # Create base config
    config = SimulationConfig(
        n=n_values[0],
        p=p_values[0],
        rho=rho_values[0],
        seed=args.seed,
        distribution_type="normal"
    )

    # Placeholder generators - these would be replaced with actual implementations
    def dummy_data_generator(cfg: SimulationConfig) -> SyntheticDataset:
        """Dummy data generator for demonstration."""
        data = np.random.randn(cfg.n, cfg.p)
        return SyntheticDataset(
            seed=cfg.seed,
            n=cfg.n,
            p=cfg.p,
            rho=cfg.rho,
            distribution_type=cfg.distribution_type,
            data=data,
            correlation_matrix=np.eye(cfg.p),
            sha256=""
        )

    def dummy_test_runner(dataset: SyntheticDataset) -> List[float]:
        """Dummy test runner returning uniform p-values."""
        return np.random.uniform(0, 1, size=dataset.p).tolist()

    def dummy_trajectory_writer(seed: int, pvalues: List[float], metadata: Dict) -> Path:
        """Dummy trajectory writer."""
        return Path(f"data/synthetic/trajectories/{seed}.json")

    # Run sweep
    orchestrator = SimulationOrchestrator(
        config=config,
        data_generator=dummy_data_generator,
        test_runner=dummy_test_runner,
        trajectory_writer=dummy_trajectory_writer
    )

    results = orchestrator.run_sweep(
        n_values=n_values,
        p_values=p_values,
        rho_values=rho_values,
        n_iterations_per_config=args.n_iterations
    )

    summary = orchestrator.get_summary()

    # Write summary
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Simulation complete. Summary written to {output_path}")
    logger.info(f"Total iterations: {summary['total_iterations']}")
    logger.info(f"Total p-values collected: {summary['total_pvalues_collected']}")

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    exit(main())
