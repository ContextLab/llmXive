"""
Unit Tests for Coverage Aggregator (T013d)
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.coverage_aggregator import (
    validate_dataframe_structure,
    calculate_adjusted_coverage,
    save_extended_results,
    load_coverage_intermediate
)
from config import get_artifact_path


class TestCoverageAggregatorStructure:
    """Tests for dataframe structure validation"""

    def test_valid_dataframe_structure(self):
        """Test that a valid dataframe passes validation"""
        df = pd.DataFrame({
            'dataset': ['UCI_Adult', 'UCI_Iris'],
            'statistic': ['Mean', 'Regression'],
            'epsilon': [0.1, 0.5],
            'noise_type': ['Laplace', 'Gaussian'],
            'coverage_rate': [0.94, 0.93],
            'num_simulations': [1000, 1000]
        })
        assert validate_dataframe_structure(df) is True

    def test_missing_dataset_column(self):
        """Test that missing 'dataset' column raises error"""
        df = pd.DataFrame({
            'statistic': ['Mean'],
            'epsilon': [0.1],
            'noise_type': ['Laplace'],
            'coverage_rate': [0.94]
        })
        with pytest.raises(ValueError, match="missing required columns"):
            validate_dataframe_structure(df)

    def test_missing_statistic_column(self):
        """Test that missing 'statistic' column raises error"""
        df = pd.DataFrame({
            'dataset': ['UCI_Adult'],
            'epsilon': [0.1],
            'noise_type': ['Laplace'],
            'coverage_rate': [0.94]
        })
        with pytest.raises(ValueError, match="missing required columns"):
            validate_dataframe_structure(df)

    def test_invalid_statistic_values(self):
        """Test that invalid statistic values raise error"""
        df = pd.DataFrame({
            'dataset': ['UCI_Adult'],
            'statistic': ['InvalidStat'],
            'epsilon': [0.1],
            'noise_type': ['Laplace'],
            'coverage_rate': [0.94]
        })
        with pytest.raises(ValueError, match="Invalid values found in 'statistic'"):
            validate_dataframe_structure(df)

    def test_distinct_columns_verification(self):
        """Explicitly verify 'dataset' and 'statistic' are distinct columns"""
        df = pd.DataFrame({
            'dataset': ['A', 'B'],
            'statistic': ['Mean', 'Regression'],
            'epsilon': [0.1, 0.2],
            'noise_type': ['L', 'G'],
            'coverage_rate': [0.9, 0.9]
        })
        # Check they are separate keys
        assert 'dataset' in df.columns
        assert 'statistic' in df.columns
        assert df['dataset'].tolist() != df['statistic'].tolist()
        validate_dataframe_structure(df)


class TestCoverageAggregatorCalculation:
    """Tests for coverage calculation and adjustments"""

    def test_calculate_adjusted_coverage_basic(self):
        """Test basic coverage calculation without adjustments"""
        df = pd.DataFrame({
            'dataset': ['UCI_Adult'],
            'statistic': ['Mean'],
            'epsilon': [0.1],
            'noise_type': ['Laplace'],
            'coverage_rate': [0.945]
        })
        result = calculate_adjusted_coverage(df)
        assert result['coverage_rate'].dtype == np.float64
        assert result['coverage_rate'].iloc[0] == 0.945

    def test_calculate_adjusted_coverage_with_adjustment_col(self):
        """Test handling of existing adjusted_coverage column"""
        df = pd.DataFrame({
            'dataset': ['UCI_Adult'],
            'statistic': ['Mean'],
            'epsilon': [0.1],
            'noise_type': ['Laplace'],
            'coverage_rate': [0.945],
            'adjusted_coverage': [0.950]
        })
        result = calculate_adjusted_coverage(df)
        assert result['adjusted_coverage'].dtype == np.float64


class TestCoverageAggregatorIO:
    """Tests for file I/O operations"""

    def test_save_extended_results_atomic(self):
        """Test that save_extended_results writes atomically"""
        df = pd.DataFrame({
            'dataset': ['UCI_Adult'],
            'statistic': ['Mean'],
            'epsilon': [0.1],
            'noise_type': ['Laplace'],
            'coverage_rate': [0.94]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.csv")
            saved_path = save_extended_results(df, output_path)
            
            assert saved_path == output_path
            assert os.path.exists(output_path)
            
            # Verify content
            loaded = pd.read_csv(output_path)
            assert 'dataset' in loaded.columns
            assert 'statistic' in loaded.columns
            assert len(loaded) == 1
            assert loaded['dataset'].iloc[0] == 'UCI_Adult'
            assert loaded['statistic'].iloc[0] == 'Mean'

    def test_save_extended_results_column_order(self):
        """Test that dataset and statistic are prioritized in column order"""
        df = pd.DataFrame({
            'noise_type': ['Laplace'],
            'epsilon': [0.1],
            'dataset': ['UCI_Adult'],
            'coverage_rate': [0.94],
            'statistic': ['Mean']
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.csv")
            save_extended_results(df, output_path)
            
            loaded = pd.read_csv(output_path)
            cols = loaded.columns.tolist()
            # dataset and statistic should be the first two columns
            assert cols[0] == 'dataset'
            assert cols[1] == 'statistic'