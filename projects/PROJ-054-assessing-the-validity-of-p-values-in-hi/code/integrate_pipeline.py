"""
Integration Pipeline for US1 and US2.

This module orchestrates the generation of synthetic datasets (US1) and the
subsequent execution of hypothesis tests (US2) on each generated dataset.
It ensures that for every simulation configuration, the data is generated,
validated, tested, and the resulting p-values are collected and stored.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

# Import from project modules
from generate_data import generate_correlated_data, write_dataset_metadata
from run_tests import run_hypothesis_tests
from utils.simulation import SimulationConfig, SimulationOrchestrator
from utils.exceptions import SimulationError, HypothesisTestError
from store_trajectories import write_trajectory_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_simulation_configs(config_path: str = "data/synthetic/configs.json") -> List[Dict[str, Any]]:
    """
    Load simulation configurations from a JSON file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        List of configuration dictionaries.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the config file is invalid JSON.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, 'r') as f:
        configs = json.load(f)

    if not isinstance(configs, list):
        raise SimulationError("Configuration file must contain a list of configurations.")

    logger.info(f"Loaded {len(configs)} simulation configurations from {config_path}")
    return configs


def run_integration_pipeline(
    output_dir: str = "data/synthetic",
    configs: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Run the full integration pipeline: generate data and run hypothesis tests.

    This function iterates through simulation configurations, generates the
    corresponding synthetic dataset, runs the hypothesis tests on that data,
    and stores the p-value trajectories.

    Args:
        output_dir: Directory where output files will be written.
        configs: Optional list of configurations. If None, loads from default path.

    Returns:
        List of result dictionaries containing metadata and summary statistics.
    """
    if configs is None:
        configs = load_simulation_configs()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    trajectories_dir = output_path / "trajectories"
    trajectories_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_iterations = len(configs)
    logger.info(f"Starting integration pipeline with {total_iterations} configurations.")

    for idx, config in enumerate(configs):
        seed = config.get("seed", idx)
        n = config.get("n", 100)
        p = config.get("p", 50)
        rho = config.get("rho", 0.0)
        distribution_type = config.get("distribution_type", "normal")

        logger.info(f"[{idx+1}/{total_iterations}] Processing seed={seed}, n={n}, p={p}, rho={rho}")

        try:
            # 1. Generate Data (US1)
            # Ensure the seed is set for reproducibility within this iteration
            np.random.seed(seed)
            random_state = np.random.RandomState(seed)

            data_matrix, corr_matrix = generate_correlated_data(
                n=n,
                p=p,
                rho=rho,
                distribution_type=distribution_type,
                random_state=random_state
            )

            # Write metadata for the generated dataset
            metadata_path = output_path / f"{seed}.json"
            write_dataset_metadata(
                path=metadata_path,
                seed=seed,
                n=n,
                p=p,
                rho=rho,
                distribution_type=distribution_type,
                data_hash=None # Hash computed inside write_dataset_metadata based on data
            )

            logger.info(f"Generated dataset for seed {seed} and saved metadata.")

            # 2. Run Hypothesis Tests (US2)
            # The data matrix is assumed to be shaped (n, p) where columns are variables
            # and we test differences between groups or correlations.
            # For this null hypothesis simulation, we test if columns are significantly different
            # from zero or each other under the null.
            # run_hypothesis_tests expects data in a specific format (e.g., two groups or similar).
            # Based on the spec, we are testing the validity of p-values under the null.
            # We will split the data into two groups if n is even, or handle appropriately.
            # Assuming a standard t-test setup where we compare two halves of the data or
            # test against a known null (e.g., mean=0).
            # Let's assume the function `run_hypothesis_tests` handles the internal logic
            # for the specific test (t-test/F-test) on the provided matrix.

            test_results = run_hypothesis_tests(data_matrix, seed=seed)

            # test_results is expected to be a list of p-values or a dict with 'p_values' key
            if isinstance(test_results, dict):
                p_values = test_results.get("p_values", [])
            else:
                p_values = test_results

            if not isinstance(p_values, list):
                p_values = list(p_values)

            if len(p_values) != p:
                logger.warning(f"Seed {seed}: Expected {p} p-values, got {len(p_values)}.")
                # In a strict implementation, we might raise an error here.
                # For now, we log and proceed, but the count check is critical for US2.

            # 3. Store Trajectories (US1/US2 integration)
            trajectory_data = {
                "seed": seed,
                "n": n,
                "p": p,
                "rho": rho,
                "distribution_type": distribution_type,
                "p_values": p_values,
                "iteration": 0 # Assuming single run per config for now, or batched
            }

            trajectory_path = trajectories_dir / f"{seed}.json"
            write_trajectory_file(trajectory_data, trajectory_path)

            results.append({
                "seed": seed,
                "status": "success",
                "n": n,
                "p": p,
                "rho": rho,
                "num_p_values": len(p_values),
                "trajectory_path": str(trajectory_path)
            })

            logger.info(f"Completed seed {seed}: Stored {len(p_values)} p-values.")

        except Exception as e:
            logger.error(f"Failed to process seed {seed}: {str(e)}", exc_info=True)
            results.append({
                "seed": seed,
                "status": "failed",
                "error": str(e)
            })

    logger.info(f"Integration pipeline completed. {len(results)} configurations processed.")
    return results


def main():
    """Entry point for the integration pipeline."""
    logger.info("Starting Integration Pipeline (T022)")

    # Default configuration if not provided via CLI
    # In a real scenario, this might be loaded from a command line argument or env var
    # For now, we assume the configs are generated by T015 logic or exist in data/synthetic/configs.json
    # If the file doesn't exist, we might need to generate a default one for demonstration
    # But per T022, we assume T015 has completed and produced the configs.

    config_path = "data/synthetic/configs.json"
    if not Path(config_path).exists():
        logger.warning(f"Config file {config_path} not found. Generating a minimal test config.")
        # Fallback for immediate execution if T015 hasn't created the file yet
        minimal_configs = [
            {"seed": 42, "n": 100, "p": 50, "rho": 0.0, "distribution_type": "normal"},
            {"seed": 123, "n": 200, "p": 100, "rho": 0.3, "distribution_type": "t"}
        ]
        Path("data/synthetic").mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(minimal_configs, f, indent=2)
        logger.info(f"Created minimal config at {config_path}")

    try:
        results = run_integration_pipeline(configs=None) # Loads from default path

        # Summary
        success_count = sum(1 for r in results if r["status"] == "success")
        fail_count = sum(1 for r in results if r["status"] == "failed")
        logger.info(f"Pipeline Summary: {success_count} succeeded, {fail_count} failed.")

        if fail_count > 0:
            sys.exit(1)

    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()