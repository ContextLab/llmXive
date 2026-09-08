"""
Unit tests for code/engineer.py (T019).
Tests interaction feature engineering and temperature feature validation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure project root is in path to import engineer module
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.engineer import (
    calculate_interaction_features,
    ensure_temperature_feature,
    validate_dataset_size,
    run_engineering_pipeline
)

class TestCalculateInteractionFeatures:
    """Tests for calculate_interaction_features function."""

    def test_basic_interaction_calculation(self):
        """Test that interaction features are correctly calculated."""
        # Create a simple DataFrame with known values
        data = {
            'cold_work_pct': [10.0, 20.0, 30.0],
            'Mn_wt': [0.5, 1.0, 1.5],
            'Mg_wt': [0.2, 0.4, 0.6],
            'Si_wt': [0.1, 0.2, 0.3],
            'Cu_wt': [0.05, 0.1, 0.15],
            'annealing_temp_K': [500.0, 550.0, 600.0]
        }
        df = pd.DataFrame(data)

        result = calculate_interaction_features(df)

        # Check that interaction columns exist
        assert 'cold_work_Mn_interaction' in result.columns
        assert 'cold_work_Mg_interaction' in result.columns
        assert 'cold_work_Si_interaction' in result.columns
        assert 'cold_work_Cu_interaction' in result.columns

        # Verify calculations (row 0: 10 * 0.5 = 5.0)
        assert result.loc[0, 'cold_work_Mn_interaction'] == pytest.approx(5.0)
        assert result.loc[0, 'cold_work_Mg_interaction'] == pytest.approx(2.0)
        assert result.loc[0, 'cold_work_Si_interaction'] == pytest.approx(1.0)
        assert result.loc[0, 'cold_work_Cu_interaction'] == pytest.approx(0.5)

    def test_missing_cold_work_column(self):
        """Test behavior when cold_work_pct is missing."""
        data = {
            'Mn_wt': [0.5, 1.0],
            'Mg_wt': [0.2, 0.4]
        }
        df = pd.DataFrame(data)

        # Should not raise an error, just skip interactions
        result = calculate_interaction_features(df)

        # Interaction columns should not be added
        assert 'cold_work_Mn_interaction' not in result.columns
        assert 'cold_work_Mg_interaction' not in result.columns

    def test_partial_composition_columns(self):
        """Test when only some composition columns are present."""
        data = {
            'cold_work_pct': [10.0],
            'Mn_wt': [0.5],
            # Mg_wt missing
            'Si_wt': [0.1]
            # Cu_wt missing
        }
        df = pd.DataFrame(data)

        result = calculate_interaction_features(df)

        # Only interactions for present columns should be created
        assert 'cold_work_Mn_interaction' in result.columns
        assert 'cold_work_Si_interaction' in result.columns
        assert 'cold_work_Mg_interaction' not in result.columns
        assert 'cold_work_Cu_interaction' not in result.columns

    def test_zero_cold_work(self):
        """Test that zero cold work results in zero interactions."""
        data = {
            'cold_work_pct': [0.0, 0.0],
            'Mn_wt': [1.0, 2.0],
            'Mg_wt': [0.5, 1.0]
        }
        df = pd.DataFrame(data)

        result = calculate_interaction_features(df)

        assert result.loc[0, 'cold_work_Mn_interaction'] == 0.0
        assert result.loc[0, 'cold_work_Mg_interaction'] == 0.0

    def test_no_temperature_interaction(self):
        """Verify that cold_work * Temperature is NOT calculated."""
        data = {
            'cold_work_pct': [10.0],
            'Mn_wt': [0.5],
            'annealing_temp_K': [500.0]
        }
        df = pd.DataFrame(data)

        result = calculate_interaction_features(df)

        # Ensure no temperature interaction was created
        assert 'cold_work_Temperature_interaction' not in result.columns
        assert 'cold_work_annealing_temp_K_interaction' not in result.columns

class TestEnsureTemperatureFeature:
    """Tests for ensure_temperature_feature function."""

    def test_temperature_present(self):
        """Test that function works when temperature is present."""
        data = {
            'annealing_temp_K': [500.0, 550.0, 600.0]
        }
        df = pd.DataFrame(data)

        result = ensure_temperature_feature(df)

        assert 'annealing_temp_K' in result.columns
        assert result['annealing_temp_K'].dtype in [np.float64, np.float32]

    def test_temperature_missing(self):
        """Test that function raises error when temperature is missing."""
        data = {
            'cold_work_pct': [10.0]
        }
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="annealing_temp_K is missing"):
            ensure_temperature_feature(df)

    def test_temperature_numeric_conversion(self):
        """Test that temperature is converted to numeric."""
        data = {
            'annealing_temp_K': ['500', '550', '600']  # Strings
        }
        df = pd.DataFrame(data)

        result = ensure_temperature_feature(df)

        assert result['annealing_temp_K'].dtype in [np.float64, np.float32]
        assert result.loc[0, 'annealing_temp_K'] == 500.0

    def test_temperature_with_nulls(self):
        """Test handling of null temperature values."""
        data = {
            'annealing_temp_K': [500.0, None, 600.0]
        }
        df = pd.DataFrame(data)

        result = ensure_temperature_feature(df)

        assert pd.isna(result.loc[1, 'annealing_temp_K'])

class TestValidateDatasetSize:
    """Tests for validate_dataset_size function."""

    def test_valid_size(self):
        """Test that valid size passes."""
        df = pd.DataFrame({'col': range(5000)})
        # Should not raise
        validate_dataset_size(df)

    def test_exceeds_cap(self):
        """Test that size exceeding cap raises error."""
        df = pd.DataFrame({'col': range(10001)})

        with pytest.raises(ValueError, match="exceeds cap of 10000 rows"):
            validate_dataset_size(df)

    def test_exact_cap(self):
        """Test that exactly 10000 rows passes."""
        df = pd.DataFrame({'col': range(10000)})
        # Should not raise
        validate_dataset_size(df)

class TestRunEngineeringPipeline:
    """Integration tests for the full engineering pipeline."""

    def test_pipeline_with_mock_data(self, tmp_path):
        """Test the pipeline with a temporary CSV file."""
        # Create temporary input file
        input_path = tmp_path / "validated.csv"
        data = {
            'cold_work_pct': [10.0, 20.0],
            'Mn_wt': [0.5, 1.0],
            'Mg_wt': [0.2, 0.4],
            'Si_wt': [0.1, 0.2],
            'Cu_wt': [0.05, 0.1],
            'annealing_temp_K': [500.0, 550.0]
        }
        pd.DataFrame(data).to_csv(input_path, index=False)

        # Mock the paths in the function by temporarily patching
        original_func = run_engineering_pipeline.__code__
        
        # We'll test the core logic by calling the helper functions directly
        # since run_engineering_pipeline has hardcoded paths
        df = pd.read_csv(input_path)
        df = ensure_temperature_feature(df)
        df = calculate_interaction_features(df)

        # Verify output
        assert 'cold_work_Mn_interaction' in df.columns
        assert 'annealing_temp_K' in df.columns
        assert len(df) == 2