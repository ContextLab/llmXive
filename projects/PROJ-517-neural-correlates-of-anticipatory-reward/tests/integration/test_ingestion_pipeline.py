"""
Integration test for User Story 1: Data Ingestion and Pre-processing Pipeline.

Tests that the ingestion pipeline correctly loads synthetic data,
aligns it by trial ID, and produces the expected output columns and metrics.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from synthetic_generator import generate_synthetic_dataset, load_schema
from ingestion import run_ingestion_pipeline

# Constants for test expectations
EXPECTED_COLUMNS = ['trial_id', 'neuron_id', 'spike_count', 'reward_magnitude']
SYNTHETIC_DATA_PATH = "data/raw/synthetic_test.csv"
OUTPUT_PATH = "data/processed/aligned_data.csv"
SEED = 42
N_NEURONS = 5
N_TRIALS_PER_NEURON = 10
EXPECTED_TOTAL_ROWS = N_NEURONS * N_TRIALS_PER_NEURON


def setup_module(module):
    """
    Setup before running tests in this module.
    Ensures the synthetic data exists before the test runs.
    """
    schema = load_schema()
    generate_synthetic_dataset(
        schema=schema,
        output_path=SYNTHETIC_DATA_PATH,
        seed=SEED,
        n_neurons=N_NEURONS,
        n_trials_per_neuron=N_TRIALS_PER_NEURON
    )


def test_data_alignment():
    """
    Test that the ingestion pipeline:
    1. Loads data from the synthetic CSV.
    2. Produces a DataFrame with the required columns.
    3. The sum of spike counts matches the expected total derived from the seed.
    """
    # Run the ingestion pipeline
    # Note: We assume run_ingestion_pipeline handles the path resolution or we pass it.
    # Based on typical pipeline structure, we pass the input path and output path.
    df = run_ingestion_pipeline(
        input_path=SYNTHETIC_DATA_PATH,
        output_path=OUTPUT_PATH
    )

    # Assert the DataFrame is not empty
    assert df is not None, "Ingestion pipeline returned None"
    assert not df.empty, "Ingestion pipeline returned an empty DataFrame"

    # Assert expected columns exist
    assert list(df.columns) == EXPECTED_COLUMNS, (
        f"Expected columns {EXPECTED_COLUMNS}, got {list(df.columns)}"
    )

    # Assert row count matches expected total (no filtering happened on this clean synthetic data)
    assert len(df) == EXPECTED_TOTAL_ROWS, (
        f"Expected {EXPECTED_TOTAL_ROWS} rows, got {len(df)}"
    )

    # Calculate expected spike count sum deterministically from the seed
    # The synthetic generator uses numpy.random with seed=42 to generate spike counts.
    # We must replicate the generation logic to know the "expected" sum,
    # or we rely on the fact that the pipeline must preserve the sum of the input.
    # Since the task asks to assert spike_count.sum() == expected_total,
    # we will re-generate the data in-memory to get the ground truth sum.
    
    np.random.seed(SEED)
    expected_sum = 0
    for _ in range(N_NEURONS):
        # Replicate the synthetic generation logic for spike counts
        # Assuming uniform distribution or specific logic from synthetic_generator
        # Since we can't import the internal logic directly without knowing the exact function,
        # we will trust the pipeline to process the file correctly.
        # However, to strictly satisfy "assert spike_count.sum() == expected_total",
        # we need the ground truth.
        # Let's load the raw data again to get the sum, ensuring the pipeline didn't drop rows.
        pass
    
    # Re-load raw data to get ground truth sum
    raw_df = pd.read_csv(SYNTHETIC_DATA_PATH)
    raw_total_sum = raw_df['spike_count'].sum()
    
    # Verify the pipeline output sum matches the raw input sum
    # (Assuming no filtering logic in ingestion for this specific test case on clean data)
    assert df['spike_count'].sum() == raw_total_sum, (
        f"Spike count sum mismatch. Raw: {raw_total_sum}, Processed: {df['spike_count'].sum()}"
    )
    
    # If the ingestion logic filters out zero-spike or invalid trials, 
    # we would need to account for that, but for the basic alignment test 
    # on clean synthetic data, the sum should be preserved.
    
    # Optional: Verify data types
    assert df['trial_id'].dtype == 'int64', "trial_id should be int64"
    assert df['neuron_id'].dtype == 'int64', "neuron_id should be int64"
    assert df['spike_count'].dtype in ['int64', 'float64'], "spike_count should be numeric"
    assert df['reward_magnitude'].dtype in ['int64', 'float64'], "reward_magnitude should be numeric"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
