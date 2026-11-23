import pytest
import pandas as pd
import numpy as np
import tempfile
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.clean import apply_fr007_exclusion, apply_country_level_exclusion, standardize_iso_code, standardize_year

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'iso_code': ['USA', 'USA', 'USA', 'CAN', 'CAN', 'FRA', 'FRA', 'DEU'],
        'year': [2000, 2005, 2010, 2000, 2005, 2000, 2005, 2000],
        'land_use_change_rate': [0.1, 0.2, 0.3, 0.15, 0.25, 0.12, 0.18, 0.14],
        'regime_type': [1, 1, 1, 0, 0, 1, 1, 0],
        'gdp_per_capita': [50000.0, 52000.0, np.nan, 45000.0, 47000.0, 38000.0, np.nan, 42000.0],
        'population_density': [90.0, 92.0, 95.0, 4.0, 4.2, 115.0, 118.0, 230.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestDataCleaningLogic:
    """Test cases for data cleaning logic including T016 row-level exclusion."""

    def test_excludes_row_when_gdp_missing(self, sample_dataframe):
        """T016: Verify a row is excluded if GDP is null and logged correctly."""
        # Apply FR-007 exclusion
        result = apply_fr007_exclusion(sample_dataframe)
        
        # Check that the row with missing GDP is excluded
        # Row index 2 (USA, 2010) has nan in gdp_per_capita
        # Row index 6 (FRA, 2005) has nan in gdp_per_capita
        expected_rows = 6  # 8 total - 2 excluded
        assert len(result) == expected_rows, f"Expected {expected_rows} rows, got {len(result)}"
        
        # Verify no rows with missing GDP remain
        assert result['gdp_per_capita'].isna().sum() == 0, "Some rows with missing GDP remain"

    def test_excludes_country_when_primary_missing(self, sample_dataframe, temp_data_dir):
        """T016b: Verify a country is excluded if >20% of years are missing for a primary variable."""
        # Create a scenario where one country has >20% missing primary data
        data = {
            'iso_code': ['USA', 'USA', 'USA', 'CAN', 'CAN', 'CAN', 'FRA', 'FRA', 'FRA'],
            'year': [2000, 2005, 2010, 2000, 2005, 2010, 2000, 2005, 2010],
            'land_use_change_rate': [0.1, 0.2, 0.3, 0.15, 0.25, 0.35, np.nan, np.nan, np.nan],  # FRA has 100% missing
            'regime_type': [1, 1, 1, 0, 0, 0, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        
        # Apply country-level exclusion
        result, excluded_countries = apply_country_level_exclusion(df)
        
        # FRA should be excluded (100% > 20%)
        assert 'FRA' in excluded_countries, "FRA should be excluded due to missing primary data"
        assert len(result) == 6, "Should have 6 rows remaining (USA and CAN)"

    def test_standardizes_iso_code(self):
        """Test ISO code standardization."""
        data = {'iso_code': ['usa', 'can', 'fra'], 'value': [1, 2, 3]}
        df = pd.DataFrame(data)
        result = standardize_iso_code(df)
        assert all(result['iso_code'] == ['USA', 'CAN', 'FRA']), "ISO codes not standardized"

    def test_standardizes_year(self):
        """Test year standardization."""
        data = {'year': ['2000', '2005', '2010'], 'value': [1, 2, 3]}
        df = pd.DataFrame(data)
        result = standardize_year(df)
        assert all(result['year'] == [2000, 2005, 2010]), "Years not standardized"

    def test_fr007_handles_empty_dataframe(self):
        """Test FR-007 with empty DataFrame."""
        df = pd.DataFrame(columns=['iso_code', 'year', 'gdp_per_capita', 'population_density'])
        result = apply_fr007_exclusion(df)
        assert len(result) == 0, "Empty DataFrame should remain empty"

    def test_country_exclusion_handles_empty_dataframe(self):
        """Test country-level exclusion with empty DataFrame."""
        df = pd.DataFrame(columns=['iso_code', 'year', 'land_use_change_rate'])
        result, excluded = apply_country_level_exclusion(df)
        assert len(result) == 0, "Empty DataFrame should remain empty"
        assert len(excluded) == 0, "No countries should be excluded from empty DataFrame"