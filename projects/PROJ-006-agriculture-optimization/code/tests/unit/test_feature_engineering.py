"""
Unit tests for feature engineering functions.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from src.data.processing.feature_engineering import (
    calculate_stability_score,
    calculate_csa_index,
    derive_village_id,
    perform_village_aggregation,
    load_linkage_validation
)

class TestStabilityScoreCalculation:
    """Tests for calculate_stability_score function."""

    def test_perfect_stability(self):
        """Test with identical NDVI values (CV=0)."""
        ndvi = pd.Series([0.5, 0.5, 0.5, 0.5])
        score = calculate_stability_score(ndvi)
        assert score == float('inf')

    def test_normal_variation(self):
        """Test with normal variation in NDVI values."""
        ndvi = pd.Series([0.4, 0.5, 0.6, 0.5])
        score = calculate_stability_score(ndvi)
        assert isinstance(score, float)
        assert score > 0

    def test_single_value(self):
        """Test with insufficient data points."""
        ndvi = pd.Series([0.5])
        score = calculate_stability_score(ndvi)
        assert np.isnan(score)

    def test_empty_series(self):
        """Test with empty series."""
        ndvi = pd.Series([])
        score = calculate_stability_score(ndvi)
        assert np.isnan(score)

    def test_zero_mean(self):
        """Test with mean NDVI of zero."""
        ndvi = pd.Series([0.0, 0.0, 0.0])
        score = calculate_stability_score(ndvi)
        assert np.isnan(score)

    def test_negative_ndvi(self):
        """Test with negative NDVI values (should use absolute mean)."""
        ndvi = pd.Series([-0.1, -0.2, -0.3])
        score = calculate_stability_score(ndvi)
        assert isinstance(score, float)
        assert score > 0

class TestCSAIndexConstruction:
    """Tests for calculate_csa_index function."""

    def test_all_practices(self):
        """Test with all practices adopted."""
        row = pd.Series({
            'practice_mixed_farming': True,
            'practice_terracing': True,
            'practice_conservation_tillage': True,
            'practice_agroforestry': True
        })
        index = calculate_csa_index(row)
        assert index == 4

    def test_no_practices(self):
        """Test with no practices adopted."""
        row = pd.Series({
            'practice_mixed_farming': False,
            'practice_terracing': False,
            'practice_conservation_tillage': False,
            'practice_agroforestry': False
        })
        index = calculate_csa_index(row)
        assert index == 0

    def test_partial_practices(self):
        """Test with some practices adopted."""
        row = pd.Series({
            'practice_mixed_farming': True,
            'practice_terracing': False,
            'practice_conservation_tillage': True,
            'practice_agroforestry': False
        })
        index = calculate_csa_index(row)
        assert index == 2

    def test_missing_columns(self):
        """Test with missing practice columns."""
        row = pd.Series({'other_column': 1})
        index = calculate_csa_index(row)
        assert index == 0

    def test_nan_values(self):
        """Test with NaN values in practice columns."""
        row = pd.Series({
            'practice_mixed_farming': np.nan,
            'practice_terracing': True,
            'practice_conservation_tillage': False,
            'practice_agroforestry': np.nan
        })
        index = calculate_csa_index(row)
        assert index == 1

class TestVillageIDDerivation:
    """Tests for derive_village_id function."""

    def test_basic_derivation(self):
        """Test basic village ID derivation."""
        village_id = derive_village_id(10.5, 20.5)
        # With default GRID_RESOLUTION_KM = 0.1
        # int(10.5 / 0.1) * 0.1 = 105 * 0.1 = 10.5
        # int(20.5 / 0.1) * 0.1 = 205 * 0.1 = 20.5
        assert village_id == "10.5_20.5"

    def test_rounding_behavior(self):
        """Test rounding to nearest grid cell."""
        village_id = derive_village_id(10.54, 20.54)
        # int(10.54 / 0.1) = int(105.4) = 105 -> 10.5
        assert village_id.startswith("10.5_")

    def test_negative_coordinates(self):
        """Test with negative coordinates."""
        village_id = derive_village_id(-10.5, -20.5)
        # int(-10.5 / 0.1) = int(-105) = -105 -> -10.5
        assert village_id == "-10.5_-20.5"

class TestVillageAggregation:
    """Tests for perform_village_aggregation function."""

    def test_basic_aggregation(self):
        """Test basic village-level aggregation."""
        df = pd.DataFrame({
            'village_id': ['10.5_20.5', '10.5_20.5', '11.0_21.0'],
            'CSA_Index': [2, 3, 1],
            'Stability_Score': [1.5, 2.5, 3.0]
        })
        
        aggregated = perform_village_aggregation(df)
        
        assert len(aggregated) == 2
        assert 'village_id' in aggregated.columns
        assert 'CSA_Index' in aggregated.columns
        assert 'Stability_Score' in aggregated.columns

    def test_null_exclusion(self):
        """Test that rows with null key metrics are excluded."""
        df = pd.DataFrame({
            'village_id': ['10.5_20.5', '10.5_20.5', '11.0_21.0'],
            'CSA_Index': [2, np.nan, 1],
            'Stability_Score': [1.5, 2.5, np.nan]
        })
        
        aggregated = perform_village_aggregation(df)
        
        # Only the third row has both non-null values
        assert len(aggregated) == 1
        assert aggregated.loc[0, 'village_id'] == '11.0_21.0'

    def test_empty_dataframe(self):
        """Test aggregation of empty dataframe."""
        df = pd.DataFrame(columns=['village_id', 'CSA_Index', 'Stability_Score'])
        aggregated = perform_village_aggregation(df)
        assert len(aggregated) == 0

class TestLinkageValidationLoading:
    """Tests for load_linkage_validation function."""

    def test_valid_json(self):
        """Test loading valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'linkage_percentage': 0.95, 'triggered_aggregation': False}, f)
            temp_path = Path(f.name)
        
        try:
            data = load_linkage_validation(temp_path)
            assert data['linkage_percentage'] == 0.95
            assert data['triggered_aggregation'] == False
        finally:
            temp_path.unlink()

    def test_missing_file(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_linkage_validation(Path('/nonexistent/path/file.json'))

    def test_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_linkage_validation(temp_path)
        finally:
            temp_path.unlink()
