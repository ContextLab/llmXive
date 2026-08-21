import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import apply_stratified_sampling, PowerLimitationError

class TestStratifiedSampling:
    
    def test_stratified_sampling_proportional(self):
        """Test that stratified sampling maintains proportional distribution."""
        # Create a synthetic dataset with known distribution
        # 1000 rows: 50% 'A', 30% 'B', 20% 'C'
        data = {
            'turn_label': ['A'] * 500 + ['B'] * 300 + ['C'] * 200,
            'value': list(range(1000))
        }
        df = pd.DataFrame(data)
        
        target_size = 200
        sampled = apply_stratified_sampling(df, target_size)
        
        # Check total size
        assert len(sampled) == target_size, f"Expected size {target_size}, got {len(sampled)}"
        
        # Check proportions (allow some variance due to integer rounding)
        original_props = df['turn_label'].value_counts(normalize=True).sort_index()
        sampled_props = sampled['turn_label'].value_counts(normalize=True).sort_index()
        
        # Ensure all labels are present
        assert set(sampled['turn_label'].unique()) == set(df['turn_label'].unique())
        
        # Check that proportions are roughly maintained (within 10% relative error)
        for label in original_props.index:
            if label in sampled_props.index:
                diff = abs(original_props[label] - sampled_props[label])
                assert diff < 0.1, f"Proportion mismatch for {label}: {original_props[label]} vs {sampled_props[label]}"

    def test_stratified_sampling_small_dataset(self):
        """Test sampling when requested size >= dataset size."""
        df = pd.DataFrame({
            'turn_label': ['A', 'B', 'C'],
            'value': [1, 2, 3]
        })
        
        sampled = apply_stratified_sampling(df, 10)
        
        assert len(sampled) == len(df), "Should return full dataset when requested size is larger"
        assert list(sampled['turn_label']) == list(df['turn_label'])

    def test_stratified_sampling_missing_column(self):
        """Test that ValueError is raised if 'turn_label' is missing."""
        df = pd.DataFrame({
            'other_col': [1, 2, 3]
        })
        
        with pytest.raises(ValueError, match="Column 'turn_label' not found"):
            apply_stratified_sampling(df, 2)

    def test_stratified_sampling_single_stratum(self):
        """Test sampling with only one class."""
        df = pd.DataFrame({
            'turn_label': ['A'] * 100,
            'value': range(100)
        })
        
        sampled = apply_stratified_sampling(df, 50)
        
        assert len(sampled) == 50
        assert all(sampled['turn_label'] == 'A')