"""
Unit tests for T020: Population Mean Calculator
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Mock imports for dependencies that might be heavy or require external state
from code import population_mean_calculator as pmc
from code import config


class TestPopulationMeanCalculator:
    """Tests for the population mean calculation logic."""

    def test_calculate_population_means_basic(self):
        """Test basic mean calculation on a simple DataFrame."""
        data = {
            'A': [1.0, 2.0, 3.0, 4.0],
            'B': [10.0, 20.0, 30.0, 40.0],
            'C': ['x', 'y', 'z', 'w'] # Should be skipped
        }
        df = pd.DataFrame(data)

        result = pmc.calculate_population_means(df)

        assert 'A' in result
        assert 'B' in result
        assert 'C' not in result
        assert result['A'] == 2.5
        assert result['B'] == 25.0

    def test_calculate_population_means_with_nans(self):
        """Test that NaNs are handled (mean ignores them if dropna not called, but pandas mean does by default)."""
        data = {
            'A': [1.0, np.nan, 3.0, 4.0],
        }
        df = pd.DataFrame(data)
        # Pandas mean() ignores NaN by default
        result = pmc.calculate_population_means(df)
        assert result['A'] == (1.0 + 3.0 + 4.0) / 3.0

    def test_load_cleaned_dataset_integration_mock(self, mocker):
        """Mock the raw data loading to test the cleaning and mean logic chain."""
        # Mock raw data
        mock_raw = pd.DataFrame({
            'val1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'val2': [10.0, 20.0, 30.0, 40.0, 50.0],
            'cat': ['a', 'b', 'c', 'd', 'e']
        })

        mocker.patch.object(pmc, 'load_uci_dataset_raw', return_value=mock_raw)
        mocker.patch.object(pmc, 'identify_continuous_variables', return_value=['val1', 'val2'])

        # Mock the dropna behavior implicitly by just checking the result of the function
        # The function calls dropna() internally.
        df_clean = pmc.load_cleaned_dataset("test_ds", Path("/fake"))

        assert df_clean is not None
        assert list(df_clean.columns) == ['val1', 'val2']
        assert len(df_clean) == 5

    def test_save_population_means(self, tmp_path):
        """Test saving population means to JSON."""
        data = {
            "ds1": {"var1": 1.5, "var2": 2.5},
            "ds2": {"var1": 10.0}
        }
        output_file = tmp_path / "test_means.json"

        pmc.save_population_means(data, output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)

        assert loaded == data

    def test_run_population_mean_calculation_with_mocked_datasets(self, mocker, tmp_path):
        """Test the main runner with mocked dataset loading."""
        # Setup mock data
        mock_data = {
            "Wine": pd.DataFrame({'col1': [1.0, 2.0, 3.0], 'col2': [4.0, 5.0, 6.0]}),
            "Ionosphere": pd.DataFrame({'col1': [10.0, 20.0], 'col2': [30.0, 40.0]})
        }

        def mock_load_cleaned(dataset_id, data_dir):
            return mock_data.get(dataset_id)

        def mock_identify_vars(df):
            return list(df.columns)

        mocker.patch.object(pmc, 'load_cleaned_dataset', side_effect=mock_load_cleaned)
        mocker.patch.object(pmc, 'identify_continuous_variables', side_effect=mock_identify_vars)

        # Mock config paths
        mocker.patch.object(pmc, 'get_data_dir', return_value=tmp_path / "raw")
        mocker.patch.object(pmc, 'get_output_dir', return_value=tmp_path)

        # Create necessary directories
        (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Override output file path for test
        output_file = processed_dir / "population_means.json"

        # Run
        pmc.run_population_mean_calculation()

        assert output_file.exists()
        with open(output_file, 'r') as f:
            results = json.load(f)

        assert "Wine" in results
        assert "Ionosphere" in results
        assert "col1" in results["Wine"]
        assert results["Wine"]["col1"] == 2.0  # Mean of 1, 2, 3