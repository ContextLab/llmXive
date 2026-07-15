"""
Integration test for the full download and simulation pipeline (US1).

This test verifies that the pipeline correctly fetches real OpenML datasets,
simulates synthetic outcome vectors according to the configuration, and
produces the expected number of rows in the output data.

It asserts that:
1. The pipeline executes without error.
2. The output file exists at the expected path.
3. The number of rows in the output matches `config.simulation_count`.
4. The output contains the required metadata columns.
"""

import os
import sys
import pandas as pd
import pytest

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import get_config
from utils.logger import get_logger

# Import the pipeline logic that T013 and T015 implement.
# These modules are expected to exist as per the task definitions.
from data.downloader import load_openml_datasets
from data.simulators import run_simulation_pipeline

logger = get_logger(__name__)


def test_pipeline_generates_expected_rows():
    """
    Integration test: Verify the full download+simulate pipeline generates
    the expected number of rows as defined in the configuration.

    Asserts:
        len(results_df) == config.simulation_count
    """
    # Load configuration
    config = get_config()

    logger.info(f"Starting integration test with seed: {config.seed}")
    logger.info(f"Expected simulation count: {config.simulation_count}")

    # 1. Fetch real datasets (T013)
    # This will fail loudly if real data cannot be fetched, satisfying the
    # "fail loudly" constraint.
    logger.info("Fetching datasets from OpenML...")
    datasets = load_openml_datasets(
        dataset_ids=config.openml_ids,
        min_rows=100,
        min_predictors=3
    )

    assert len(datasets) == len(config.openml_ids), (
        f"Expected {len(config.openml_ids)} datasets, got {len(datasets)}"
    )
    logger.info(f"Successfully loaded {len(datasets)} datasets.")

    # 2. Run simulation pipeline (T015)
    # This generates the synthetic Y vectors and saves them to data/processed/
    logger.info("Running simulation pipeline...")
    output_path = run_simulation_pipeline(
        datasets=datasets,
        snr_levels=config.snr_levels,
        sparsity_levels=config.sparsity_levels,
        output_dir=config.output_path,
        seed=config.seed
    )

    # 3. Verify output file exists
    assert os.path.exists(output_path), f"Output file not found at {output_path}"
    logger.info(f"Output file created at: {output_path}")

    # 4. Load results and verify row count
    results_df = pd.read_parquet(output_path)
    actual_count = len(results_df)

    logger.info(f"Actual row count: {actual_count}")
    logger.info(f"Expected row count: {config.simulation_count}")

    assert actual_count == config.simulation_count, (
        f"Row count mismatch: Expected {config.simulation_count}, got {actual_count}"
    )

    # 5. Verify required columns exist (metadata integrity)
    required_columns = {
        'dataset_id', 'n_rows', 'n_predictors',
        'snr', 'sparsity', 'seed',
        'true_coefficients', 'condition_number'
    }
    existing_columns = set(results_df.columns)

    missing = required_columns - existing_columns
    assert not missing, f"Missing required columns: {missing}"

    logger.info("Integration test passed: Row count and metadata verified.")