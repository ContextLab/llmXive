import os
import pytest
import pandas as pd
from pathlib import Path
import numpy as np

from synthetic_generator import generate_synthetic_dataset, load_schema

@pytest.fixture
def schema_path():
    return Path("contracts/dataset.schema.yaml")

@pytest.fixture
def output_path():
    return Path("data/raw/synthetic_test.csv")

def test_generate_synthetic_dataset_structure(schema_path):
    """Test that the generated dataset matches the schema structure."""
    df = generate_synthetic_dataset(n_trials=10, seed=42)
    
    # Check columns
    expected_columns = [
        "trial_id", "neuron_id", "spike_time_ms", 
        "cue_time_ms", "reward_magnitude", "snr", "isolation_distance"
    ]
    assert list(df.columns) == expected_columns, f"Columns mismatch: {list(df.columns)}"
    
    # Check types
    assert df["trial_id"].dtype == object
    assert df["neuron_id"].dtype == object
    assert df["spike_time_ms"].dtype in [np.float32, np.float64]
    assert df["cue_time_ms"].dtype in [np.float32, np.float64]
    assert df["reward_magnitude"].dtype in [np.float32, np.float64]
    assert df["snr"].dtype in [np.float32, np.float64]
    assert df["isolation_distance"].dtype in [np.float32, np.float64]

def test_generate_synthetic_dataset_no_lists(schema_path):
    """Test that no column contains list data (flat schema requirement)."""
    df = generate_synthetic_dataset(n_trials=10, seed=42)
    
    for col in df.columns:
        assert not df[col].apply(lambda x: isinstance(x, list)).any(), \
            f"Column {col} contains list data"

def test_generate_synthetic_dataset_reproducibility(schema_path):
    """Test that generation is reproducible with the same seed."""
    df1 = generate_synthetic_dataset(n_trials=10, seed=42)
    df2 = generate_synthetic_dataset(n_trials=10, seed=42)
    
    pd.testing.assert_frame_equal(df1, df2)

def test_generate_synthetic_dataset_values(schema_path):
    """Test that generated values are within expected ranges."""
    df = generate_synthetic_dataset(n_trials=100, seed=42)
    
    # Reward magnitude should be 1, 2, or 3
    assert set(df["reward_magnitude"].unique()).issubset({1.0, 2.0, 3.0})
    
    # SNR should be between 3.5 and 6.0
    assert df["snr"].min() >= 3.5
    assert df["snr"].max() <= 6.0
    
    # Isolation distance should be between 22.0 and 30.0
    assert df["isolation_distance"].min() >= 22.0
    assert df["isolation_distance"].max() <= 30.0

def test_main_creates_file(output_path, schema_path):
    """Test that main() creates the expected output file."""
    # Remove file if it exists
    if output_path.exists():
        output_path.unlink()
    
    # Run main
    import sys
    from synthetic_generator import main
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Mock sys.argv if needed, but main() doesn't take args
    main()
    
    # Check file exists
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    # Check content
    df = pd.read_csv(output_path)
    assert len(df) == 100
    assert "spike_time_ms" in df.columns

def test_schema_load(schema_path):
    """Test that the schema can be loaded."""
    if schema_path.exists():
        schema = load_schema(schema_path)
        assert "fields" in schema
        assert len(schema["fields"]) > 0
    else:
        pytest.skip("Schema file not found for this test")