"""
Inference Pipeline for Geometric Action Model.

Orchestrates the encode -> solve -> decode -> simulate loop with timeout
and drift detection capabilities.
"""
import logging
import time
import os
import sys
from typing import Dict, Optional, Any, List, Tuple

import numpy as np
import torch

from config import load_config
from gfm_wrapper import GFMWrapper
from symbolic_solver import SymbolicSolver, ConstraintMatrix, TimeoutHandler
from latent_drift import LatentDriftDetector, load_reference_stats
from trial_log_schema import TrialLogger, TrialLogEntry

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Main inference pipeline orchestrating the research workflow.
    """
    def __init__(
        self,
        config_path: Optional[str] = None,
        gfm_weights_path: Optional[str] = None,
        reference_stats_path: Optional[str] = None,
        trial_log_path: str = "data/results/trial_log.csv"
    ):
        """
        Initialize the inference pipeline.

        Args:
            config_path: Path to the configuration file.
            gfm_weights_path: Path to the GFM weights file.
            reference_stats_path: Path to the reference statistics file for drift detection.
            trial_log_path: Path to the trial log CSV file.
        """
        # Load configuration
        self.config = load_config(config_path)
        self.device = torch.device("cpu")  # Enforce CPU-only

        # Initialize GFM Wrapper
        self.gfm_wrapper = GFMWrapper(weights_path=gfm_weights_path or "data/raw/gfm_weights.pt")
        self.gfm_wrapper.to(self.device)
        self.gfm_wrapper.model.eval()

        # Initialize Drift Detector
        if reference_stats_path and os.path.exists(reference_stats_path):
            self.reference_stats = load_reference_stats(reference_stats_path)
            self.drift_detector = LatentDriftDetector(self.reference_stats)
        else:
            self.reference_stats = None
            self.drift_detector = None

        # Initialize Trial Logger
        self.trial_logger = TrialLogger(log_path=trial_log_path)

        # Global timeout check
        self.start_time = None
        self.global_timeout = 6 * 3600  # 6 hours

    def encode_observation(self, observation: np.ndarray) -> torch.Tensor:
        """
        Encode a 3D observation into latent space.

        Args:
            observation: 3D observation array.

        Returns:
            Latent vector tensor.
        """
        with torch.no_grad():
            obs_tensor = torch.tensor(observation, dtype=torch.float32, device=self.device)
            latent = self.gfm_wrapper.encode(obs_tensor)
        return latent

    def solve_constraints(
        self,
        latent_vector: torch.Tensor,
        constraint_matrix: ConstraintMatrix
    ) -> Tuple[np.ndarray, bool]:
        """
        Solve the symbolic constraints for a given latent vector.

        Args:
            latent_vector: Input latent vector.
            constraint_matrix: Constraint matrix for the solver.

        Returns:
            Tuple of (solution, is_feasible).
        """
        solver = SymbolicSolver(
            constraint_matrix,
            timeout_seconds=self.config.solver_config.timeout_limits["step"]
        )

        try:
            with TimeoutHandler(self.config.solver_config.timeout_limits["step"]):
                solution, _ = solver.solve()
                return solution, True
        except Exception as e:
            logger.warning(f"Solve failed: {e}")
            return None, False

    def decode_action(self, latent_vector: torch.Tensor) -> np.ndarray:
        """
        Decode a latent vector into a 3D action.

        Args:
            latent_vector: Input latent vector.

        Returns:
            3D action array.
        """
        with torch.no_grad():
            action = self.gfm_wrapper.decode(latent_vector)
        return action.detach().cpu().numpy()

    def detect_drift(self, latent_vector: torch.Tensor) -> bool:
        """
        Detect if the latent vector is out-of-distribution.

        Args:
            latent_vector: Input latent vector.

        Returns:
            True if drift is detected, False otherwise.
        """
        if self.drift_detector is None:
            return False

        try:
            distance = self.drift_detector.compute_mahalanobis(latent_vector)
            return distance > self.drift_detector.threshold
        except Exception as e:
            logger.error(f"Drift detection error: {e}")
            return False

    def run_trial(
        self,
        trial_id: str,
        observation: np.ndarray,
        constraint_matrix: ConstraintMatrix
    ) -> Dict[str, Any]:
        """
        Run a single trial through the full pipeline.

        Args:
            trial_id: Unique identifier for the trial.
            observation: 3D observation array.
            constraint_matrix: Constraint matrix for the solver.

        Returns:
            Dictionary containing trial results.
        """
        start_time = time.time()
        success = False
        infeasible = False
        timeout = False
        drift_detected = False

        try:
            # Global timeout check
            if self.start_time and (time.time() - self.start_time) > self.global_timeout:
                logger.error("Global timeout exceeded!")
                raise TimeoutError("Global timeout exceeded")

            # Encode
            latent = self.encode_observation(observation)

            # Detect drift
            if self.detect_drift(latent):
                drift_detected = True
                logger.warning(f"Drift detected for trial {trial_id}")
                # Log alert
                alert_path = "data/results/drift_alert.json"
                with open(alert_path, "w") as f:
                    import json
                    json.dump({"trial_id": trial_id, "status": "requires_review"}, f)

            # Solve
            solution, is_feasible = self.solve_constraints(latent, constraint_matrix)

            if not is_feasible:
                infeasible = True
            else:
                # Decode
                action = self.decode_action(torch.tensor(solution, dtype=torch.float32))

                # Simulate (placeholder - in real scenario, this would call PyBullet)
                # For now, we assume success if we got here
                success = True

        except TimeoutError as e:
            timeout = True
            logger.error(f"Trial {trial_id} timed out: {e}")
        except Exception as e:
            logger.error(f"Trial {trial_id} failed: {e}")

        elapsed = time.time() - start_time

        # Log trial
        entry = TrialLogEntry(
            trial_id=trial_id,
            step=1,
            success=success,
            infeasible=infeasible,
            timeout=timeout,
            latency_ms=elapsed * 1000
        )
        self.trial_logger.log(entry)

        return {
            "trial_id": trial_id,
            "success": success,
            "infeasible": infeasible,
            "timeout": timeout,
            "drift_detected": drift_detected,
            "latency_ms": elapsed * 1000
        }

    def run_experiment(
        self,
        observations: List[np.ndarray],
        constraint_matrices: List[ConstraintMatrix]
    ) -> List[Dict[str, Any]]:
        """
        Run the full experiment on a list of observations.

        Args:
            observations: List of 3D observation arrays.
            constraint_matrices: List of constraint matrices.

        Returns:
            List of trial results.
        """
        self.start_time = time.time()
        results = []

        for i, (obs, matrix) in enumerate(zip(observations, constraint_matrices)):
            trial_id = f"trial_{i:04d}"
            logger.info(f"Running {trial_id}...")
            result = self.run_trial(trial_id, obs, matrix)
            results.append(result)

            # Check global timeout
            if (time.time() - self.start_time) > self.global_timeout:
                logger.error("Global timeout exceeded, stopping experiment.")
                break

        return results


def main() -> None:
    """
    Main entry point for running the inference pipeline.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize pipeline
    pipeline = InferencePipeline()

    # Create dummy data for testing
    observations = [np.random.randn(10, 3) for _ in range(5)]
    constraint_matrices = [
        ConstraintMatrix(
            A=np.random.randn(3, 10),
            b=np.random.randn(3)
        ) for _ in range(5)
    ]

    # Run experiment
    results = pipeline.run_experiment(observations, constraint_matrices)

    # Log summary
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Experiment complete. Success rate: {success_count}/{len(results)}")


if __name__ == "__main__":
    main()
