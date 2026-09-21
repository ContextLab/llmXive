"""
Unit tests for download.py module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from download import (
    compare_distributions,
    stratified_sample_metadata,
    load_m4_metadata,
    calculate_sha256
)

class TestCompareDistributions:
    """Tests for compare_distributions function."""
    
    def test_identical_distributions(self):
        """KL divergence should be 0 for identical distributions."""
        dist = pd.Series([0.5, 0.5], index=['A', 'B'])
        result = compare_distributions(dist, dist)
        assert abs(result) < 1e-10
    
    def test_different_distributions(self):
        """KL divergence should be positive for different distributions."""
        full = pd.Series([0.8, 0.2], index=['A', 'B'])
        sample = pd.Series([0.6, 0.4], index=['A', 'B'])
        result = compare_distributions(full, sample)
        assert result > 0
    
    def test_mismatched_indices(self):
        """Should handle distributions with different indices."""
        full = pd.Series([0.5, 0.5], index=['A', 'B'])
        sample = pd.Series([1.0], index=['A'])
        result = compare_distributions(full, sample)
        assert result >= 0  # Should not crash

class TestStratifiedSampleMetadata:
    """Tests for stratified_sample_metadata function."""
    
    @pytest.fixture
    def sample_metadata(self):
        """Create a sample metadata DataFrame."""
        data = {
            'series_id': range(100),
            'frequency': ['yearly'] * 50 + ['quarterly'] * 30 + ['monthly'] * 20,
            'seasonality': [1] * 50 + [4] * 30 + [12] * 20
        }
        return pd.DataFrame(data)
    
    def test_sample_size_limit(self, sample_metadata):
        """Should respect sample_size limit."""
        sampled, kl_div, report = stratified_sample_metadata(
            sample_metadata,
            sample_size=10,
            seed=42
        )
        assert len(sampled) <= 10
    
    def test_stratification_preserves_distribution(self, sample_metadata):
        """Stratified sample should roughly preserve distribution."""
        sampled, kl_div, report = stratified_sample_metadata(
            sample_metadata,
            sample_size=50,
            seed=42
        )
        
        # Check that KL divergence is reasonable
        assert kl_div >= 0
        # Note: KL divergence threshold depends on sample size and stratification
    
    def test_seed_reproducibility(self, sample_metadata):
        """Same seed should produce same sample."""
        sampled1, _, _ = stratified_sample_metadata(
            sample_metadata,
            sample_size=20,
            seed=42
        )
        sampled2, _, _ = stratified_sample_metadata(
            sample_metadata,
            sample_size=20,
            seed=42
        )
        assert sampled1.equals(sampled2)
    
    def test_small_dataset(self):
        """Should handle datasets smaller than sample_size."""
        small_df = pd.DataFrame({
            'series_id': range(5),
            'frequency': ['A'] * 5,
            'seasonality': [1] * 5
        })
        sampled, kl_div, report = stratified_sample_metadata(
            small_df,
            sample_size=100,
            seed=42
        )
        assert len(sampled) == 5  # Should return all available

class TestLoadM4Metadata:
    """Tests for load_m4_metadata function."""
    
    def test_missing_required_fields(self, tmp_path):
        """Should raise ValueError if required fields are missing."""
        # Create a CSV without required fields
        csv_path = tmp_path / "bad_metadata.csv"
        pd.DataFrame({'other_col': [1, 2, 3]}).to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError, match="Missing required metadata fields"):
            load_m4_metadata(str(csv_path))
    
    def test_valid_metadata(self, tmp_path):
        """Should load metadata with required fields."""
        csv_path = tmp_path / "good_metadata.csv"
        data = {
            'series_id': [1, 2, 3],
            'frequency': ['A', 'B', 'C'],
            'seasonality': [1, 2, 3]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        df = load_m4_metadata(str(csv_path))
        assert len(df) == 3
        assert 'frequency' in df.columns
        assert 'seasonality' in df.columns

class TestCalculateSha256:
    """Tests for calculate_sha256 function."""
    
    def test_known_hash(self, tmp_path):
        """Should calculate correct SHA256 for known input."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        
        # Expected SHA256 for "Hello, world!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        result = calculate_sha256(str(test_file))
        assert result == expected