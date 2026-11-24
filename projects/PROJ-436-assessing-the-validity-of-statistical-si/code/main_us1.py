"""
Main entry point for User Story 1: Simulate Missing Data and Calculate Empirical Type I Error.

This script executes a single simulation condition (mechanism, rate, method)
for a specified number of iterations and outputs the aggregated results to
`data/processed/us1_results.json`.

It fetches the required OpenML dataset (ID 42803) directly, avoiding a
dependency on the broader data‑loader (T101) which may not yet be functional.
"""

import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import openml
import pandas as pd

# Ensure the project root is on the import path when executed as a script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

# Project imports
from config import SimulationConfig, validate_config, config_to_dict
from simulation import permute_treatment_labels, simulate_mar
from analysis import run_complete_case_analysis
from metrics import aggregate_results as metrics_aggregate_results
from llmxive_toolkit import paths, get_logger

# Configure logger (console only – avoids missing directory issues)
logger = get_logger(__name__, level=logging.INFO)

# ----------------------------------------------------------------------
# Default configuration – exactly the condition required for US1
# ----------------------------------------------------------------------
DEFAULT_CONFIG = {
    "dataset_id": 42803,               # OpenML ID for the required RCT dataset
    "mechanism": "MAR",                # Missingness mechanism
    "missing_rate": 0.20,              # 20 % missingness
    "outcome_type": "continuous",      # Outcome type (continuous for this dataset)
    "n_iterations": 500,               # Number of Monte Carlo iterations
    "seed": 42,                        # Fixed random seed for reproducibility
    "analysis_method": "CC",           # Complete‑Case analysis (required)
    "alternative_hypothesis": False,
    "covariate_for_mar": "age",        # Use observed covariate `age` for MAR
}

def _load_dataset_openml(dataset_id: int) -> pd.DataFrame:
    """
    Fetch a dataset from OpenML and return it as a pandas DataFrame.
    This function fails loudly if the download cannot be performed.
    """
    logger.info(f"Downloading OpenML dataset {dataset_id}")
    try:
        oml_dataset = openml.datasets.get_dataset(dataset_id)
    except Exception as exc:
        logger.error(f"Failed to retrieve OpenML dataset {dataset_id}: {exc}")
        raise

    # Convert to DataFrame
    try:
        df, _, _, _ = oml_dataset.get_data(dataset_format="dataframe")
    except Exception as exc:
        logger.error(f"Failed to convert OpenML dataset {dataset_id} to DataFrame: {exc}")
        raise

    logger.info(f"Dataset {dataset_id} downloaded: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def run_single_condition_simulation(
    config_dict: Dict[str, Any],
    output_path: str,
) -> Dict[str, Any]:
    """
    Executes a single simulation condition defined by ``config_dict`` and
    writes the results to ``output_path``.
    """
    logger.info(f"Starting US1 simulation with config: {config_dict}")

    # 1. Validate configuration
    config = SimulationConfig(**config_dict)
    validate_config(config)
    logger.info("Configuration validated.")

    # 2. Load the required dataset (42803) directly from OpenML
    df = _load_dataset_openml(config.dataset_id)

    # The OpenML dataset 42803 uses column name ``treat`` for treatment.
    # Internally the analysis code expects the treatment column name to be
    # supplied explicitly, so we keep the original name.
    outcome_col = "outcome"
    treatment_col = "treat"  # matches the dataset schema
    covariate_col = config.covariate_for_mar or "age"

    # 3. Prepare simulation parameters
    np.random.seed(config.seed)
    mechanism = config.mechanism
    missing_rate = config.missing_rate
    iterations = config.n_iterations

    # 4. Run the Monte‑Carlo loop
    p_values: List[float] = []
    pvalue_records: List[Dict[str, Any]] = []

    for i in range(iterations):
        if (i + 1) % 100 == 0:
            logger.info(f"Iteration {i + 1}/{iterations}")

        # a. Permute treatment labels to enforce a true null hypothesis
        seed_perm = config.seed + i
        df_permuted = permute_treatment_labels(df, seed=seed_perm)

        # b. Simulate MAR missingness using the observed covariate
        seed_missing = config.seed + i + 1000
        df_missing, _ = simulate_mar(
            df_permuted,
            rate=missing_rate,
            seed=seed_missing,
            covariate_col=covariate_col,
        )

        # c. Complete‑Case analysis (CC)
        try:
            analysis_res = run_complete_case_analysis(
                df_missing,
                outcome_col=outcome_col,
                treatment_col=treatment_col,
            )
            p_val = float(analysis_res.get("p_value", 1.0))
        except Exception as exc:
            logger.warning(f"Iteration {i} failed during analysis: {exc}")
            p_val = 1.0

        p_values.append(p_val)

        # Record per‑iteration details for the p‑value distribution schema
        pvalue_records.append(
            {
                "run_id": str(uuid.uuid4()),
                "dataset_id": str(config.dataset_id),
                "mechanism": mechanism,
                "missing_rate": missing_rate,
                "method": config.analysis_method,
                "p_value": p_val,
                "is_significant": p_val < 0.05,
                "seed": seed_perm,
            }
        )

    if not p_values:
        raise RuntimeError("No p‑values were generated; all iterations failed.")

    # 5. Aggregate results (error‑metric)
    dataset_info = {
        "id": config.dataset_id,
        "shape": list(df.shape),
        "columns": list(df.columns),
    }

    agg_results = metrics_aggregate_results(
        p_values=p_values,
        config=config_to_dict(config),
        dataset_info=dataset_info,
        method=config.analysis_method,
    )

    # 6. Assemble final JSON structure
    final_results = {
        "p_value_distribution": pvalue_records,
        "error_metric": agg_results,
        "metadata": {
            "iteration_count": iterations,
            "config": config_to_dict(config),
            "dataset_info": dataset_info,
        },
    }

    # 7. Write results to disk
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, default=str)

    logger.info(f"US1 results saved to {output_file}")
    return final_results

def main() -> None:
    """
    Entry point for the script.
    """
    # Resolve output location (uses llmxive paths helper for consistency)
    default_output = paths.data("processed", "us1_results.json")
    output_path = os.getenv("US1_OUTPUT_PATH", str(default_output))

    # Load configuration from file if provided, otherwise use defaults
    config_path = os.getenv("US1_CONFIG_FILE")
    if config_path and Path(config_path).exists():
        logger.info(f"Loading configuration from {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
    else:
        logger.info("Using default US1 configuration (required condition).")
        config_dict = DEFAULT_CONFIG.copy()

    # Override defaults with environment variables if present
    env_to_cfg = [
        ("SIMULATION_DATASET_ID", "dataset_id", int),
        ("SIMULATION_MECHANISM", "mechanism", str),
        ("SIMULATION_RATE", "missing_rate", float),
        ("SIMULATION_ITERATIONS", "n_iterations", int),
        ("SIMULATION_SEED", "seed", int),
    ]
    for env_key, cfg_key, cast in env_to_cfg:
        if env_key in os.environ:
            try:
                config_dict[cfg_key] = cast(os.environ[env_key])
            except Exception as exc:
                logger.warning(f"Failed to cast env var {env_key}: {exc}")

    try:
        results = run_single_condition_simulation(config_dict, output_path)
        # Print a compact JSON to stdout for quick verification
        print(json.dumps(results, indent=2, default=str))
    except Exception as exc:
        logger.exception(f"US1 simulation failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
