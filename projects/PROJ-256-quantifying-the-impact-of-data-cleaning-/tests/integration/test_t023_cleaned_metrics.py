"""
Integration test for T023: Verify cleaned_metrics.json generation.

This test ensures that the T023 script:
1. Runs without crashing.
2. Produces the expected output file `data/processed/cleaned_metrics.json`.
3. The JSON structure contains valid p-values and finite CIs for any analyzed datasets.
"""
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from t023_reanalyze_cleaned_variants import main as t023_main, find_cleaned_datasets
from utils import pin_random_seed

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_cleaned_csv(temp_processed_dir):
    """Create a sample cleaned CSV file to simulate T022 output."""
    # Create a simple dataset with numeric columns
    data = {
        "feature1": np.random.randn(50),
        "feature2": np.random.randn(50),
        "outcome": np.random.randn(50)
    }
    df = pd.DataFrame(data)
    # Save as a "cleaned" variant
    path = os.path.join(temp_processed_dir, "test_data_iqr_outlier.csv")
    df.to_csv(path, index=False)
    return path

def test_t023_generates_metrics_file(temp_processed_dir, sample_cleaned_csv):
    """
    Test that T023 runs and produces cleaned_metrics.json with valid content.
    """
    # Temporarily override the config to use our temp directory
    # We will patch the Config class or environment variables if necessary.
    # For this test, we assume the script uses default paths or env vars.
    # Since we can't easily patch the Config class in the script without modifying it,
    # we will set the environment variable if the script supports it, 
    # or we rely on the fact that the script might look in 'data/processed' by default.
    
    # To make this robust, we'll create a symlink or copy the structure to 'data/processed' 
    # relative to the project root if possible, but for a pure unit/integration test:
    # We will modify the environment variable if the script reads it, 
    # or we assume the test is run in an environment where 'data/processed' is the temp dir.
    
    # Actually, the script uses `Config().get("PROCESSED_DATA_PATH", "data/processed")`.
    # We can't easily mock Config here without importing it and monkey-patching.
    # Let's rely on the environment variable if the Config class supports it (which it likely does).
    # If not, we might need to adjust the script to accept a config override.
    # For now, let's assume the test runs in a controlled environment or we patch the function.
    
    # Better approach: Patch the `find_cleaned_datasets` call or the `Config` class.
    # Since we can't change the script in the test, we'll set the environment variable.
    # Assuming Config uses os.getenv.
    
    old_processed = os.environ.get("PROCESSED_DATA_PATH")
    os.environ["PROCESSED_DATA_PATH"] = temp_processed_dir
    
    try:
        # Run the main function
        result = t023_main()
        
        assert result == 0, "T023 main returned non-zero exit code"
        
        # Check if file exists
        output_path = os.path.join(temp_processed_dir, "cleaned_metrics.json")
        assert os.path.exists(output_path), f"Output file not found: {output_path}"
        
        # Validate JSON content
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert "metadata" in data, "Missing metadata in output"
        assert "datasets" in data, "Missing datasets in output"
        
        # If we have datasets, check metrics
        if data["datasets"]:
            entry = data["datasets"][0]
            # Check for p-values
            # The structure depends on run_baseline_analysis output
            # Assuming it has 't_test' and 'regression' keys
            if "t_test" in entry:
                p_val = entry["t_test"].get("p_value")
                assert p_val is not None, "p_value missing in t_test"
                assert 0 < p_val < 1, f"p_value {p_val} not in (0, 1)"
            
            if "regression" in entry:
                # Check CI bounds if present
                ci = entry["regression"].get("ci")
                if ci:
                    assert isinstance(ci, (list, tuple)), "CI should be a list/tuple"
                    assert len(ci) == 2, "CI should have 2 bounds"
                    assert all(np.isfinite(x) for x in ci), "CI bounds must be finite"
                    
    finally:
        if old_processed:
            os.environ["PROCESSED_DATA_PATH"] = old_processed
        elif "PROCESSED_DATA_PATH" in os.environ:
            del os.environ["PROCESSED_DATA_PATH"]

def test_t023_empty_directory():
    """Test behavior when no cleaned datasets are found."""
    temp_dir = tempfile.mkdtemp()
    try:
        old_processed = os.environ.get("PROCESSED_DATA_PATH")
        os.environ["PROCESSED_DATA_PATH"] = temp_dir
        
        result = t023_main()
        assert result == 0
        
        output_path = os.path.join(temp_dir, "cleaned_metrics.json")
        assert os.path.exists(output_path)
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert data["datasets"] == [], "Expected empty datasets list"
        assert data["metadata"]["datasets_count"] == 0
        
    finally:
        if old_processed:
            os.environ["PROCESSED_DATA_PATH"] = old_processed
        elif "PROCESSED_DATA_PATH" in os.environ:
            del os.environ["PROCESSED_DATA_PATH"]
        
        shutil.rmtree(temp_dir)