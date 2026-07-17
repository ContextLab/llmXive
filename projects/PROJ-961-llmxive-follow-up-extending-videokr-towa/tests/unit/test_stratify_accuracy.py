"""
Unit tests for accuracy calculation logic in code/analysis/stratify_accuracy.py.

This module tests the core functionality of calculating accuracy rates for
different hop bins (1-hop, 2-hop, 3+ hops) as required by FR-003.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.stratify_accuracy import (
    calculate_accuracy_by_bin,
    load_annotated_data,
    validate_min_bin_size,
    bin_hop_to_category
)


class TestBinHopToCategory:
    """Tests for the bin_hop_to_category helper function."""

    def test_hop_1(self):
        assert bin_hop_to_category(1) == "1-hop"

    def test_hop_2(self):
        assert bin_hop_to_category(2) == "2-hop"

    def test_hop_3(self):
        assert bin_hop_to_category(3) == "3+ hops"

    def test_hop_4(self):
        assert bin_hop_to_category(4) == "3+ hops"

    def test_hop_10(self):
        assert bin_hop_to_category(10) == "3+ hops"

    def test_hop_0(self):
        # Edge case: 0 hops should still be categorized
        assert bin_hop_to_category(0) == "1-hop"


class TestCalculateAccuracyByBin:
    """Tests for the main accuracy calculation logic."""

    def test_basic_accuracy_calculation(self):
        """Test basic accuracy calculation with known values."""
        data = pd.DataFrame({
            'chain_length': [1, 1, 1, 2, 2, 3, 3, 3],
            'correctness': [True, True, False, True, False, True, True, True]
        })

        result = calculate_accuracy_by_bin(data)

        # 1-hop: 2/3 = 0.666...
        # 2-hop: 1/2 = 0.5
        # 3+ hops: 3/3 = 1.0
        assert result.loc[result['bin'] == '1-hop', 'accuracy'].iloc[0] == pytest.approx(2/3, rel=1e-3)
        assert result.loc[result['bin'] == '2-hop', 'accuracy'].iloc[0] == pytest.approx(0.5, rel=1e-3)
        assert result.loc[result['bin'] == '3+ hops', 'accuracy'].iloc[0] == pytest.approx(1.0, rel=1e-3)

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        data = pd.DataFrame(columns=['chain_length', 'correctness'])
        result = calculate_accuracy_by_bin(data)
        assert len(result) == 0

    def test_single_bin_only(self):
        """Test with data that only falls into one bin."""
        data = pd.DataFrame({
            'chain_length': [1, 1, 1],
            'correctness': [True, False, True]
        })

        result = calculate_accuracy_by_bin(data)
        assert len(result) == 1
        assert result['bin'].iloc[0] == '1-hop'
        assert result['accuracy'].iloc[0] == pytest.approx(2/3, rel=1e-3)

    def test_all_correct(self):
        """Test when all records are correct."""
        data = pd.DataFrame({
            'chain_length': [1, 2, 3, 4],
            'correctness': [True, True, True, True]
        })

        result = calculate_accuracy_by_bin(data)
        assert all(result['accuracy'] == 1.0)

    def test_all_incorrect(self):
        """Test when all records are incorrect."""
        data = pd.DataFrame({
            'chain_length': [1, 2, 3],
            'correctness': [False, False, False]
        })

        result = calculate_accuracy_by_bin(data)
        assert all(result['accuracy'] == 0.0)

    def test_missing_chain_length_column(self):
        """Test handling of missing required column."""
        data = pd.DataFrame({'correctness': [True, False]})
        with pytest.raises(KeyError):
            calculate_accuracy_by_bin(data)

    def test_missing_correctness_column(self):
        """Test handling of missing required column."""
        data = pd.DataFrame({'chain_length': [1, 2, 3]})
        with pytest.raises(KeyError):
            calculate_accuracy_by_bin(data)

    def test_non_boolean_correctness(self):
        """Test handling of non-boolean correctness values (0/1)."""
        data = pd.DataFrame({
            'chain_length': [1, 1, 2, 2],
            'correctness': [1, 0, 1, 1]
        })

        result = calculate_accuracy_by_bin(data)
        # 1-hop: 1/2 = 0.5
        # 2-hop: 2/2 = 1.0
        assert result.loc[result['bin'] == '1-hop', 'accuracy'].iloc[0] == pytest.approx(0.5, rel=1e-3)
        assert result.loc[result['bin'] == '2-hop', 'accuracy'].iloc[0] == pytest.approx(1.0, rel=1e-3)


class TestValidateMinBinSize:
    """Tests for minimum bin size validation."""

    def test_all_bins_above_threshold(self):
        """Test when all bins meet the minimum size requirement."""
        bin_counts = {'1-hop': 100, '2-hop': 50, '3+ hops': 75}
        result = validate_min_bin_size(bin_counts, min_size=50)
        assert result is True

    def test_one_bin_below_threshold(self):
        """Test when one bin is below the minimum size."""
        bin_counts = {'1-hop': 100, '2-hop': 40, '3+ hops': 75}
        result = validate_min_bin_size(bin_counts, min_size=50)
        assert result is False

    def test_empty_bins(self):
        """Test with empty bins."""
        bin_counts = {'1-hop': 100, '2-hop': 0, '3+ hops': 75}
        result = validate_min_bin_size(bin_counts, min_size=50)
        assert result is False

    def test_threshold_zero(self):
        """Test with zero threshold (always passes)."""
        bin_counts = {'1-hop': 100, '2-hop': 0, '3+ hops': 75}
        result = validate_min_bin_size(bin_counts, min_size=0)
        assert result is True


class TestLoadAnnotatedData:
    """Tests for data loading functionality."""

    def test_load_from_real_file(self, tmp_path):
        """Test loading from a real CSV file."""
        # Create a temporary CSV file
        csv_path = tmp_path / "test_annotated.csv"
        data = {
            'chain_length': [1, 1, 2, 2, 3],
            'correctness': [True, False, True, True, False],
            'question': ['q1', 'q2', 'q3', 'q4', 'q5']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        loaded_df = load_annotated_data(str(csv_path))

        assert len(loaded_df) == 5
        assert 'chain_length' in loaded_df.columns
        assert 'correctness' in loaded_df.columns
        assert loaded_df['chain_length'].iloc[0] == 1

    def test_load_from_nonexistent_file(self):
        """Test handling of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_annotated_data("nonexistent.csv")

    def test_load_with_missing_columns(self, tmp_path):
        """Test loading file with missing required columns."""
        csv_path = tmp_path / "test_missing_cols.csv"
        data = {
            'chain_length': [1, 2, 3],
            'question': ['q1', 'q2', 'q3']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        with pytest.raises(ValueError):
            load_annotated_data(str(csv_path))


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_pipeline(self, tmp_path):
        """Test the full pipeline from loading data to calculating accuracy."""
        # Create test data
        csv_path = tmp_path / "test_full.csv"
        data = {
            'chain_length': [1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3],
            'correctness': [True, True, False, True, True, False, True, True, True, False, True, True]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Load and process
        loaded_data = load_annotated_data(str(csv_path))
        accuracy_results = calculate_accuracy_by_bin(loaded_data)

        # Verify results
        assert len(accuracy_results) == 3
        
        # 1-hop: 3/4 = 0.75
        hop1_acc = accuracy_results.loc[accuracy_results['bin'] == '1-hop', 'accuracy'].iloc[0]
        assert hop1_acc == pytest.approx(0.75, rel=1e-3)

        # 2-hop: 2/3 = 0.666...
        hop2_acc = accuracy_results.loc[accuracy_results['bin'] == '2-hop', 'accuracy'].iloc[0]
        assert hop2_acc == pytest.approx(2/3, rel=1e-3)

        # 3+ hops: 4/5 = 0.8
        hop3_acc = accuracy_results.loc[accuracy_results['bin'] == '3+ hops', 'accuracy'].iloc[0]
        assert hop3_acc == pytest.approx(0.8, rel=1e-3)

        # Verify bin sizes
        assert accuracy_results.loc[accuracy_results['bin'] == '1-hop', 'count'].iloc[0] == 4
        assert accuracy_results.loc[accuracy_results['bin'] == '2-hop', 'count'].iloc[0] == 3
        assert accuracy_results.loc[accuracy_results['bin'] == '3+ hops', 'count'].iloc[0] == 5

    def test_edge_case_small_bins(self, tmp_path):
        """Test with very small bin sizes."""
        csv_path = tmp_path / "test_small.csv"
        data = {
            'chain_length': [1, 2, 3],
            'correctness': [True, False, True]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        loaded_data = load_annotated_data(str(csv_path))
        accuracy_results = calculate_accuracy_by_bin(loaded_data)

        assert len(accuracy_results) == 3
        assert all(accuracy_results['count'] == 1)
        assert set(accuracy_results['accuracy']) == {0.0, 1.0}