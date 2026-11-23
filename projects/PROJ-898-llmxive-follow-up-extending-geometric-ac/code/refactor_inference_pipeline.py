"""
Refactored inference pipeline for llmXive.
Orchestrates the encode -> solve -> decode -> simulate loop.
"""
import logging
import time
import os
import sys
from typing import Dict, Optional, Any, List, Tuple

import numpy as np

from config import load_config, Config
from gfm_wrapper import GFMWrapper
from symbolic_solver import SymbolicSolver, TimeoutError as SolverTimeoutError
from latent_drift import LatentDriftDetector, load_reference_stats
from trial_log_schema import TrialLogger, TrialLogEntry
from timeout_handler import TimeoutHandler

logger = logging.getLogger(__name__)

class InferencePipeline:
    """
    Orchestrates the symbolic-latent inference pipeline.
    """

    def __init__(self, config_path: str = "code/config.yaml"):
        """
        Initialize the pipeline.

        Args:
            config_path: Path to the configuration YAML file.
        """
        self.config: Config = load_config(config_path)
        self.gfm_wrapper = GFMWrapper()
        self.solver = SymbolicSolver(
            timeout_limit=self.config.solver.timeout_limits
        )
        self.drift_detector = LatentDriftDetector(
            threshold=self._load_drift_threshold()
        )
        self.timeout_handler = TimeoutHandler(
            timeout_seconds=self.config.solver.timeout_limits
        )

        # Initialize trial logger
        self.trial_logger = TrialLogger(
            output_path="data/results/trial_log.csv"
        )

    def _load_drift_threshold(self) -> float:
        """Load drift threshold from validation file."""
        try:
            stats = load_reference_stats("data/raw/drift_threshold_validation.json")
            return stats.get("threshold", 11.07)  # Default to 95th percentile of Chi2(5)
        except Exception as e:
            logger.warning(f"Could not load drift threshold: {e}. Using default.")
            return 11.07

    def run_trial(
        self,
        trial_id: str,
        observation: Dict[str, Any],
        target_zone: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a single inference trial.

        Args:
            trial_id: Unique identifier for the trial.
            observation: Input observation dictionary.
            target_zone: Target zone configuration.

        Returns:
            Dictionary containing trial results.
        """
        start_time = time.time()
        result = {
            "trial_id": trial_id,
            "success": False,
            "timeout": False,
            "infeasible": False,
            "drift_flagged": False,
            "latency_ms": 0.0,
            "error": None
        }

        try:
            # 1. Encode observation to latent space
            latent_vector = self.gfm_wrapper.encode(observation)

            # 2. Check for latent drift
            drift_score = self.drift_detector.compute_distance(latent_vector)
            if drift_score > self.drift_detector.threshold:
                result["drift_flagged"] = True
                logger.warning(f"Trial {trial_id}: Latent drift detected (score={drift_score:.2f})")
                # Continue anyway but flag for review

            # 3. Solve constraints in latent space
            try:
                with self.timeout_handler:
                    optimized_latent = self.solver.solve(
                        latent_vector=latent_vector,
                        target_zone=target_zone
                    )
            except SolverTimeoutError:
                result["timeout"] = True
                result["error"] = "Solver timeout"
                logger.error(f"Trial {trial_id}: Solver timed out")
                self._log_trial(trial_id, result, start_time)
                return result

            # 4. Decode optimized latent to action
            action = self.gfm_wrapper.decode(optimized_latent)

            # 5. Simulate and verify (simplified for pipeline)
            success = self._verify_action(action, target_zone)
            result["success"] = success

        except Exception as e:
            result["error"] = str(e)
            logger.exception(f"Trial {trial_id} failed with exception: {e}")

        finally:
            result["latency_ms"] = (time.time() - start_time) * 1000
            self._log_trial(trial_id, result, start_time)

        return result

    def _verify_action(
        self,
        action: np.ndarray,
        target_zone: Dict[str, Any]
    ) -> bool:
        """
        Verify if an action satisfies target zone constraints.

        Args:
            action: Decoded action vector.
            target_zone: Target zone configuration.

        Returns:
            True if action is valid, False otherwise.
        """
        # Simplified verification logic
        # In a real implementation, this would involve PyBullet simulation
        target_center = np.array(target_zone["center"])
        target_radius = target_zone["radius"]

        # Check if action brings object within target radius
        distance = np.linalg.norm(action[:3] - target_center)
        return distance < target_radius

    def _log_trial(
        self,
        trial_id: str,
        result: Dict[str, Any],
        start_time: float
    ) -> None:
        """Log trial results to CSV."""
        entry = TrialLogEntry(
            trial_id=trial_id,
            approach="Symbolic",
            success=result["success"],
            latency_ms=result["latency_ms"],
            timeout=result["timeout"],
            infeasible=result["infeasible"],
            drift_flagged=result.get("drift_flagged", False),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            error=result.get("error")
        )
        self.trial_logger.log(entry)

    def run_batch(
        self,
        trials: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run a batch of trials.

        Args:
            trials: List of trial configurations.

        Returns:
            List of trial results.
        """
        results = []
        for trial in trials:
          # Check global CI time limit (6 hours)
          if time.time() - self._start_time > 6 * 3600:
              logger.critical("Global CI time limit exceeded (6 hours)")
              break
          
          result = self.run_trial(
              trial_id=trial["trial_id"],
              observation=trial["observation"],
              target_zone=self.config.experiment.target_zone
          )
          results.append(result)
        return results

def main():
    """Main entry point for the inference pipeline."""
    logging.basicConfig(level=logging.INFO)
    pipeline = InferencePipeline()
    
    # Example usage: run a single test trial
    # In production, this would load from data/generated/physics_states.json
    test_observation = {
        "joint_angles": np.zeros(10),
        "object_position": np.array([0.0, 0.0, 0.0])
    }
    
    result = pipeline.run_trial(
        trial_id="test_001",
        observation=test_observation,
        target_zone=pipeline.config.experiment.target_zone
    )
    
    logger.info(f"Test trial result: {result}")

if __name__ == "__main__":
    main()
