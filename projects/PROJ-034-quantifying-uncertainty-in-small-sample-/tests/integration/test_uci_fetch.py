"""
Integration tests for UCI dataset fetching (T029).
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd

from validation.uci_runner import fetch_uci_concrete_dataset, subsample_stratified, UCI_CONCRETE_URL

# Ensure we are in the project root context for imports if needed
# but the test runner should handle PYTHONPATH.

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def test_fetch_uci_dataset_success(temp_data_dir):
    """Test that the UCI dataset can be fetched and saved."""
    output_path = temp_data_dir / "test_concrete.csv"

    # This might fail if network is unavailable, but in CI with internet it should pass.
    # If it fails, it should raise an error, not return a fake file.
    try:
        result_path = fetch_uci_concrete_dataset(url=UCI_CONCRETE_URL, output_path=output_path)
        
        assert result_path.exists(), "Dataset file was not created."
        assert result_path.stat().st_size > 0, "Dataset file is empty."
        
        df = pd.read_csv(result_path)
        assert len(df) > 0, "Dataset has no rows."
        assert "Concrete compressive strength (MPa)" in df.columns, "Target column missing."
        
    except RuntimeError as e:
        # If the fetch fails (e.g., network issue), we assert that the error is raised
        # This is expected behavior if the real source is unreachable.
        # In a real CI run with internet, this should pass.
        pytest.skip(f"Network fetch failed (expected in offline environments): {e}")

def test_fetch_uci_dataset_caching(temp_data_dir):
    """Test that fetching a second time uses the cached file."""
    output_path = temp_data_dir / "test_concrete_cache.csv"
    
    # First fetch
    try:
        fetch_uci_concrete_dataset(url=UCI_CONCRETE_URL, output_path=output_path)
    except RuntimeError:
        pytest.skip("Network fetch failed.")

    # Second fetch should detect cache
    result_path = fetch_uci_concrete_dataset(url=UCI_CONCRETE_URL, output_path=output_path)
    assert result_path.exists()

def test_subsample_stratified_validation(temp_data_dir):
    """Test subsample logic with a mock file if fetch fails, or real file."""
    output_path = temp_data_dir / "test_concrete.csv"
    
    try:
        fetch_uci_concrete_dataset(url=UCI_CONCRETE_URL, output_path=output_path)
        df = pd.read_csv(output_path)
        
        # Test valid N
        if len(df) > 40:
            sub_df, meta = subsample_stratified(
                output_path, 
                n_samples=40, 
                seed=42
            )
            assert len(sub_df) == 40
            assert meta["n_samples"] == 40
        else:
            pytest.skip("Dataset too small for subsampling test.")
            
    except RuntimeError:
        pytest.skip("Network fetch failed.")

def test_rank_deficiency_handling(temp_data_dir):
    """Test that rank deficiency is handled gracefully."""
    output_path = temp_data_dir / "test_concrete.csv"
    
    try:
        fetch_uci_concrete_dataset(url=UCI_CONCRETE_URL, output_path=output_path)
        
        # Try to subsample with N <= p (should raise ValueError)
        # Assuming p is around 8 for concrete dataset
        with pytest.raises(ValueError, match="Rank-deficient"):
            subsample_stratified(output_path, n_samples=5, seed=42)
            
    except RuntimeError:
        pytest.skip("Network fetch failed.")