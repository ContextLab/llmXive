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
    # Ensure directories exist
    os.makedirs(os.path.dirname(SYNTHETIC_DATA_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
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
    df = run_ingestion_pipeline(
        input_path=SYNTHETIC_DATA_PATH,
        output_path=OUTPUT_PATH
    )

    # Assert the DataFrame is not empty
    assert df is not None, "Ingestion pipeline returned None"
    assert not df.empty, "Ingestion pipeline returned an empty DataFrame"

    # Assert expected columns exist
    # Note: ingestion.py may add extra columns like 'cue_delay', 'confounded'. 
    # We check that the REQUIRED columns are present.
    for col in EXPECTED_COLUMNS:
        assert col in df.columns, f"Missing required column: {col}"

    # Assert row count matches expected total (no filtering happened on this clean synthetic data)
    assert len(df) == EXPECTED_TOTAL_ROWS, (
        f"Expected {EXPECTED_TOTAL_ROWS} rows, got {len(df)}"
    )

    # Re-load raw data to get ground truth sum
    raw_df = pd.read_csv(SYNTHETIC_DATA_PATH)
    
    # Calculate expected total by grouping by trial_id and taking the first spike_count (which is constant per trial)
    # Then sum those values.
    expected_total_sum = raw_df.groupby('trial_id')['spike_count'].first().sum()
    
    # Verify the pipeline output sum matches the raw input sum
    actual_sum = df['spike_count'].sum()
    assert actual_sum == expected_total_sum, (
        f"Spike count sum mismatch. Raw: {expected_total_sum}, Processed: {actual_sum}"
    )
    
    # Optional: Verify data types
    assert df['trial_id'].dtype in ['int64', 'object', 'string'], "trial_id should be numeric or string"
    assert df['neuron_id'].dtype in ['int64', 'object', 'string'], "neuron_id should be numeric or string"
    assert df['spike_count'].dtype in ['int64', 'float64'], "spike_count should be numeric"
    assert df['reward_magnitude'].dtype in ['int64', 'float64'], "reward_magnitude should be numeric"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
