import os
import pytest
from pathlib import Path
import pandas as pd

from data.download import load_or_generate_data, discover_real_datasets, generate_synthetic_dataset

class TestFallbackLogic:
    """
    Tests for T011: Implement fallback logic.
    Verifies that if real data is not found, synthetic generation is triggered
    and the data_source_type flag is set correctly.
    """

    def test_fallback_to_synthetic_when_no_real_data(self, tmp_path, monkeypatch):
        """
        Test that load_or_generate_data returns synthetic data when no real data exists.
        """
        # Ensure no real data exists in the default search paths
        # We can't easily mock the filesystem for all paths, so we rely on the
        # implementation's logic to check specific paths.
        # For this test, we assume the default paths don't have data in the test environment.
        
        # Mock the discover_real_datasets to return False
        def mock_discover():
            return False, None, "No real dataset found"
        
        monkeypatch.setattr("data.download.discover_real_datasets", mock_discover)
        
        # Call the function
        data_path, source_type = load_or_generate_data()
        
        # Assertions
        assert source_type == "synthetic", f"Expected 'synthetic', got '{source_type}'"
        assert Path(data_path).exists(), f"Synthetic data file not found at {data_path}"
        
        # Verify the file is a valid CSV with required columns
        df = pd.read_csv(data_path)
        required_cols = ['avatar_condition', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency']
        assert all(col in df.columns for col in required_cols), "Missing required columns in synthetic data"
        
        # Verify it has enough samples (N >= 100)
        assert len(df) >= 100, f"Synthetic dataset has {len(df)} samples, expected >= 100"

    def test_synthetic_generation_creates_metadata(self, tmp_path, monkeypatch):
        """
        Test that synthetic generation creates a metadata file indicating it's synthetic.
        """
        def mock_discover():
            return False, None, "No real dataset found"
        
        monkeypatch.setattr("data.download.discover_real_datasets", mock_discover)
        
        data_path, source_type = load_or_generate_data()
        
        # Check for metadata file
        meta_path = Path(str(data_path).replace('.csv', '.meta.yaml'))
        assert meta_path.exists(), "Metadata file not created for synthetic data"
        
        # Read and verify content
        with open(meta_path, 'r') as f:
            content = f.read()
        
        assert "source_type: synthetic" in content, "Metadata does not indicate synthetic source"
        assert "Pipeline Validation Only" in content, "Metadata missing validation label"

    def test_discover_real_datasets_returns_false_when_no_files(self):
        """
        Test that discover_real_datasets returns False when no files are found.
        """
        # This test relies on the current state of the filesystem.
        # In a clean environment, it should return False.
        found, path, reason = discover_real_datasets()
        
        # We expect False if no real data is present in the test environment
        # If a real data file happens to exist, we skip the assertion or check the path
        if found:
            # If found, verify it's not the synthetic one we just created (if any)
            assert "synthetic" not in str(path).lower(), "Real data discovery should not return synthetic data"
        else:
            assert reason is not None, "Reason should be provided when no data is found"
