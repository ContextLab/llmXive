"""
Unit tests for T025c: apply_contaminated_mask logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.apply_contaminated_mask import apply_contaminated_mask, load_divergence_data


class TestApplyContaminatedMask:
    """Tests for the apply_contaminated_mask function."""

    def test_mask_applied_successfully(self):
        """Test that the mask is correctly applied and column is boolean."""
        df = pd.DataFrame({
            'seed_id': [1, 1, 1, 2, 2],
            'bias_type': ['A', 'A', 'A', 'B', 'B'],
            'timestep': [0, 1, 2, 0, 1],
            'G_t': [0.1, 0.2, 0.3, 0.1, 0.2],
            'dG_t': [0.01, 0.01, 0.01, 0.01, 0.01],
            'is_contaminated': [False, False, True, True, False]
        })

        result = apply_contaminated_mask(df)

        assert 'is_contaminated' in result.columns
        assert result['is_contaminated'].dtype == bool
        assert len(result) == len(df)
        assert result['is_contaminated'].sum() == 2

    def test_missing_contaminated_column_raises_error(self):
        """Test that missing 'is_contaminated' column raises ValueError."""
        df = pd.DataFrame({
            'seed_id': [1, 1],
            'bias_type': ['A', 'A'],
            'timestep': [0, 1],
            'G_t': [0.1, 0.2],
            'dG_t': [0.01, 0.01]
        })

        with pytest.raises(ValueError, match="missing 'is_contaminated' column"):
            apply_contaminated_mask(df)

    def test_all_contaminated_raises_error(self):
        """Test that all contaminated timesteps raises ValueError."""
        df = pd.DataFrame({
            'seed_id': [1, 1, 1],
            'bias_type': ['A', 'A', 'A'],
            'timestep': [0, 1, 2],
            'G_t': [0.1, 0.2, 0.3],
            'dG_t': [0.01, 0.01, 0.01],
            'is_contaminated': [True, True, True]
        })

        with pytest.raises(ValueError, match="All timesteps are marked as contaminated"):
            apply_contaminated_mask(df)

    def test_no_contamination_allowed(self):
        """Test that no contamination is valid (baseline uses all data)."""
        df = pd.DataFrame({
            'seed_id': [1, 1, 1],
            'bias_type': ['A', 'A', 'A'],
            'timestep': [0, 1, 2],
            'G_t': [0.1, 0.2, 0.3],
            'dG_t': [0.01, 0.01, 0.01],
            'is_contaminated': [False, False, False]
        })

        result = apply_contaminated_mask(df)
        
        assert result['is_contaminated'].sum() == 0
        assert len(result) == 3

    def test_sorting_by_seed_and_timestep(self):
        """Test that output is sorted by seed_id and timestep."""
        df = pd.DataFrame({
            'seed_id': [2, 1, 2, 1],
            'bias_type': ['B', 'A', 'B', 'A'],
            'timestep': [1, 2, 0, 1],
            'G_t': [0.1, 0.2, 0.3, 0.4],
            'dG_t': [0.01, 0.01, 0.01, 0.01],
            'is_contaminated': [False, False, False, False]
        })

        result = apply_contaminated_mask(df)

        # Check sorting
        expected_order = [(1, 1), (1, 2), (2, 0), (2, 1)]
        actual_order = list(zip(result['seed_id'], result['timestep']))
        assert actual_order == expected_order

    def test_integer_mask_converted_to_bool(self):
        """Test that integer mask values are converted to boolean."""
        df = pd.DataFrame({
            'seed_id': [1, 1, 1],
            'bias_type': ['A', 'A', 'A'],
            'timestep': [0, 1, 2],
            'G_t': [0.1, 0.2, 0.3],
            'dG_t': [0.01, 0.01, 0.01],
            'is_contaminated': [0, 0, 1]  # Integer values
        })

        result = apply_contaminated_mask(df)
        
        assert result['is_contaminated'].dtype == bool
        assert result['is_contaminated'].tolist() == [False, False, True]