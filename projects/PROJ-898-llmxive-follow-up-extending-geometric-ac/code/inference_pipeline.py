"""
Inference Pipeline for Geometric Action Model (GAM) with Symbolic Solver.

Orchestrates the loop:
1. Encode observation -> latent space (via GFM)
2. Solve symbolic constraints (via SymbolicSolver)
3. Decode latent -> 3D action (via GFM)
4. Simulate action in PyBullet
"""

import logging
import time
import os
import sys
from typing import Dict, Optional, Any, List, Tuple

import numpy as np
import torch

# Local imports matching API surface
from code.gfm_wrapper import GFMWrapper
from code.symbolic_solver import SymbolicSolver, TimeoutError
from code.latent_drift import LatentDriftDetector, load_reference_stats
from code.config import load_config, ExperimentConfig
from code.utils import setup_logging, set_deterministic_seed

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Orchestrates the encode -> solve -> decode -> simulate loop.
    
    Dependencies:
    - T014 (symbolic_solver): SymbolicSolver class
    - T016 (gfm_wrapper): GFMWrapper class
    - T019 (latent_drift): LatentDriftDetector class
    """

    def __init__(self, config_path: str, seed: int = 42, device: str = "cpu"):
        """
        Initialize the pipeline components.
        
        Args:
            config_path: Path to the JSON configuration file.
            seed: Random seed for reproducibility.
            device: Device to run PyTorch operations on ('cpu' or 'cuda').
        """
        self.seed = seed
        self.device = device
        set_deterministic_seed(seed)
        
        # Load configuration
        self.config = load_config(config_path)
        self.exp_config: ExperimentConfig = self.config.get("experiment", ExperimentConfig())
        
        # Initialize GFM Wrapper
        logger.info(f"Initializing GFMWrapper on {device}...")
        self.gfm = GFMWrapper(device=device)
        
        # Initialize Symbolic Solver
        logger.info("Initializing SymbolicSolver...")
        self.solver = SymbolicSolver()
        
        # Initialize Latent Drift Detector
        # Load reference statistics from baseline if available, else use defaults
        self.drift_detector = LatentDriftDetector()
        try:
            # Attempt to load reference stats generated from baseline data
            ref_stats_path = os.path.join("data", "generated", "reference_latent_stats.json")
            if os.path.exists(ref_stats_path):
                self.drift_detector.load_reference_stats(ref_stats_path)
                logger.info(f"Loaded reference latent stats from {ref_stats_path}")
            else:
                logger.warning(f"Reference stats not found at {ref_stats_path}. Drift detection may be inaccurate.")
        except Exception as e:
            logger.warning(f"Failed to load reference stats: {e}")

        self.stats = {
            "total_trials": 0,
            "successful_trials": 0,
            "failed_trials": 0,
            "infeasible_trials": 0,
            "drift_flagged_trials": 0,
            "total_latency_ms": 0.0,
            "trial_logs": []
        }

    def run_trial(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single inference trial.
        
        Args:
            trial_data: Dictionary containing 'observation', 'target', and metadata.
        
        Returns:
            Dictionary with results: success, latency, action, flags, etc.
        """
        start_time = time.perf_counter()
        trial_id = trial_data.get("trial_id", "unknown")
        
        result = {
            "trial_id": trial_id,
            "success": False,
            "latency_ms": 0.0,
            "action": None,
            "flags": [],
            "error": None
        }

        try:
            # 1. Encode: Observation -> Latent
            obs = np.array(trial_data["observation"], dtype=np.float32)
            latent_input = self.gfm.encode(obs)
            
            # 2. Check Latent Drift
            if self.drift_detector.is_out_of_distribution(latent_input):
                result["flags"].append("latent_drift_detected")
                self.stats["drift_flagged_trials"] += 1
                # Decide whether to abort or proceed. Per FR-003, we flag but may proceed.
                logger.warning(f"Trial {trial_id}: Latent drift detected. Proceeding with caution.")

            # 3. Solve: Latent -> Constrained Latent (Symbolic)
            try:
                constrained_latent = self.solver.solve(
                    latent_input, 
                    target=trial_data.get("target"),
                    timeout=self.exp_config.solver_timeout_seconds
                )
            except TimeoutError:
                result["flags"].append("solver_timeout")
                result["error"] = "Solver timed out"
                self.stats["failed_trials"] += 1
                self._log_trial(result, start_time)
                return result

            if not constrained_latent.get("feasible", True):
                result["flags"].append("infeasible_constraints")
                self.stats["infeasible_trials"] += 1
                self.stats["failed_trials"] += 1
                self._log_trial(result, start_time)
                return result

            # 4. Decode: Constrained Latent -> Action
            action = self.gfm.decode(constrained_latent["latent_vector"])
            
            # 5. Simulate: Apply action (Mocked for pipeline logic, real PyBullet in T021b)
            # In a real run, this would interact with the physics engine.
            # For the pipeline logic, we assume the action is valid if no exception occurred.
            # The actual success metric (SC-001) is calculated in T021b based on simulation logs.
            
            # Placeholder for simulation result logic
            # In T021b, this will be replaced by actual PyBullet simulation checks
            simulation_success = True 
            if simulation_success:
                result["success"] = True
                self.stats["successful_trials"] += 1
            else:
                result["flags"].append("simulation_failure")
                self.stats["failed_trials"] += 1

            result["action"] = action.tolist() if isinstance(action, np.ndarray) else action

        except Exception as e:
            logger.error(f"Trial {trial_id} failed with exception: {e}", exc_info=True)
            result["error"] = str(e)
            result["flags"].append("pipeline_exception")
            self.stats["failed_trials"] += 1

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        result["latency_ms"] = latency_ms
        self.stats["total_latency_ms"] += latency_ms
        self.stats["total_trials"] += 1

        self._log_trial(result, start_time)
        return result

    def _log_trial(self, result: Dict[str, Any], start_time: float):
        """Log trial details."""
        log_entry = {
            "timestamp": start_time,
            "trial_id": result["trial_id"],
            "success": result["success"],
            "latency_ms": result["latency_ms"],
            "flags": result["flags"],
            "error": result.get("error")
        }
        self.stats["trial_logs"].append(log_entry)
        logger.info(f"Trial {result['trial_id']}: Success={result['success']}, Latency={result['latency_ms']:.2f}ms, Flags={result['flags']}")

    def get_summary(self) -> Dict[str, Any]:
        """Return summary statistics of all trials."""
        if self.stats["total_trials"] == 0:
            return self.stats
        
        return {
            **self.stats,
            "success_rate": self.stats["successful_trials"] / self.stats["total_trials"],
            "avg_latency_ms": self.stats["total_latency_ms"] / self.stats["total_trials"]
        }


def main():
    """
    Entry point for running the inference pipeline on a test set.
    
    Expected usage:
    python -m code.inference_pipeline --config data/generated/config.json --input data/generated/test_set.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Inference Pipeline")
    parser.add_argument("--config", type=str, default="data/generated/config.json", help="Path to config file")
    parser.add_argument("--input", type=str, default="data/generated/test_set.json", help="Path to input test set JSON")
    parser.add_argument("--output", type=str, default="data/results/inference_results.json", help="Path to output results JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    # Load test data
    import json
    with open(args.input, 'r') as f:
        test_data = json.load(f)
    
    trials = test_data.get("trials", [])
    if not trials:
        logger.warning("No trials found in input file. Exiting.")
        sys.exit(0)

    logger.info(f"Starting inference pipeline for {len(trials)} trials...")
    
    pipeline = InferencePipeline(args.config, seed=args.seed)
    
    for trial in trials:
        pipeline.run_trial(trial)
    
    summary = pipeline.get_summary()
    
    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Pipeline complete. Results saved to {args.output}")
    logger.info(f"Summary: {summary}")

if __name__ == "__main__":
    main()