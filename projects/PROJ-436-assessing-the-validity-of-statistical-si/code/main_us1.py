"""
Main entry point for User Story 1: Simulate Missing Data and Calculate Empirical Type I Error.

This script executes a single simulation condition (mechanism, rate, method)
for a specified number of iterations and outputs the aggregated results to
data/processed/us1_results.json.

It orchestrates the pipeline:
1. Load configuration (or use defaults for a single run).
2. Load real RCT dataset from OpenML.
3. Run simulation iterations (Permute -> Simulate Missing -> Analyze -> Store).
4. Aggregate results to calculate empirical Type I error rate.
5. Save results to JSON.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict
import numpy as np

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import SimulationConfig, load_config, validate_config, config_to_dict
from data_loader import load_and_validate, DataLoadError
from simulation import run_simulation_iteration, simulate_mcar, simulate_mar, simulate_mnar, permute_treatment_labels
from metrics import aggregate_results, calculate_type1_error, run_statistical_test
from configure_sweep_rates import configure_sweep_rates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration for a single run if no config file is provided
DEFAULT_CONFIG = {
    "dataset_id": 53,  # OpenML ID for a small RCT dataset (e.g., "diabetes" or similar)
    "mechanism": "MAR",
    "rate": 0.2,
    "outcome_type": "continuous",
    "iterations": 500,
    "seed": 42,
    "method": "CC"  # Complete Case for US1 baseline
}

def run_single_condition_simulation(
    config_dict: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Executes a single simulation condition defined by the config dictionary.

    Args:
        config_dict: Dictionary containing simulation parameters (mechanism, rate, iterations, etc.).
        output_path: Path where the results JSON will be saved.

    Returns:
        Dictionary containing the aggregated simulation results.
    """
    logger.info(f"Starting simulation for condition: {config_dict}")

    # 1. Validate and load config
    config = SimulationConfig(**config_dict)
    validate_config(config)
    logger.info(f"Configuration validated: {config}")

    # 2. Load real dataset
    try:
        logger.info(f"Loading dataset from OpenML ID: {config.dataset_id}")
        df, metadata = load_and_validate(config.dataset_id)
        logger.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    except DataLoadError as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # 3. Setup simulation parameters
    np.random.seed(config.seed)
    mechanism = config.mechanism
    rate = config.rate
    iterations = config.iterations
    outcome_type = config.outcome_type

    # 4. Run simulation loop
    p_values = []
    logger.info(f"Running {iterations} iterations for {mechanism} at rate {rate}...")

    for i in range(iterations):
        if (i + 1) % 100 == 0:
            logger.info(f"Iteration {i + 1}/{iterations}")

        # a. Permute treatment labels (establish null hypothesis)
        df_permuted = df.copy()
        df_permuted['treatment'] = permute_treatment_labels(df_permuted['treatment'])

        # b. Simulate missingness based on mechanism
        if mechanism == "MCAR":
            df_missing = simulate_mcar(df_permuted, rate, outcome_type)
        elif mechanism == "MAR":
            # Check if we need synthetic covariates
            df_missing = simulate_mar(df_permuted, rate, outcome_type, logger)
        elif mechanism == "MNAR":
            df_missing = simulate_mnar(df_permuted, rate, outcome_type, logger)
        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

        # c. Analyze (Complete Case by default for US1, but extensible)
        # For now, we run the statistical test on the missing data (which effectively does CC)
        # The run_statistical_test function handles the selection of t-test vs Wilcoxon
        try:
            p_val = run_statistical_test(df_missing, outcome_type)
            p_values.append(p_val)
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}. Skipping.")
            continue

    if len(p_values) == 0:
        raise RuntimeError("No valid p-values were generated in the simulation loop.")

    # 5. Aggregate results
    logger.info("Aggregating results...")
    results = aggregate_results(p_values, config)

    # 6. Add metadata
    results['config'] = config_to_dict(config)
    results['dataset_info'] = {
        "id": config.dataset_id,
        "shape": list(df.shape),
        "columns": list(df.columns)
    }

    # 7. Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results saved to {output_file}")
    return results

def main():
    """
    Main entry point for the script.
    Reads config from environment or uses defaults, runs simulation, saves output.
    """
    # Determine output path
    output_path = os.environ.get("US1_OUTPUT_PATH", "data/processed/us1_results.json")

    # Try to load config from file if provided, else use default
    config_file = os.environ.get("US1_CONFIG_FILE")
    if config_file and os.path.exists(config_file):
        logger.info(f"Loading config from {config_file}")
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
    else:
        logger.info("Using default configuration for single condition run.")
        config_dict = DEFAULT_CONFIG.copy()

    # Allow override via environment variables for specific parameters
    if "SIMULATION_MECHANISM" in os.environ:
        config_dict["mechanism"] = os.environ["SIMULATION_MECHANISM"]
    if "SIMULATION_RATE" in os.environ:
        config_dict["rate"] = float(os.environ["SIMULATION_RATE"])
    if "SIMULATION_ITERATIONS" in os.environ:
        config_dict["iterations"] = int(os.environ["SIMULATION_ITERATIONS"])
    if "SIMULATION_DATASET_ID" in os.environ:
        config_dict["dataset_id"] = int(os.environ["SIMULATION_DATASET_ID"])

    try:
        results = run_single_condition_simulation(config_dict, output_path)
        print(json.dumps(results, indent=2, default=str))
    except Exception as e:
        logger.exception("Simulation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
