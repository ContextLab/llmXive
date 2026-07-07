import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from data.clean import (
    standardize_iso_code,
    standardize_year,
    load_fao_data,
    load_world_bank_data,
    load_regime_data,
    merge_datasets,
    drop_missing_primary_vars,
    clean_and_merge_data,
    calculate_coverage_rate,
    apply_fr007_exclusion
)

def test_standardize_iso_code():
    """Test that ISO codes are standardized to uppercase."""
    df = pd.DataFrame({'country_code': ['us', 'gb', 'fr']})
    result = standardize_iso_code(df)
    assert all(result['country_code'] == ['US', 'GB', 'FR'])

def test_standardize_year():
    """Test that year column is converted to integer."""
    df = pd.DataFrame({'year': ['2000', '2001', '2002']})
    result = standardize_year(df)
    assert result['year'].dtype == 'Int64'
    assert list(result['year']) == [2000, 2001, 2002]

def test_load_fao_data_file_not_found():
    """Test that FileNotFoundError is raised for missing FAO data."""
    with pytest.raises(FileNotFoundError):
        load_fao_data("nonexistent.csv")

def test_load_world_bank_data_file_not_found():
    """Test that FileNotFoundError is raised for missing World Bank data."""
    with pytest.raises(FileNotFoundError):
        load_world_bank_data("nonexistent.csv")

def test_load_regime_data_file_not_found():
    """Test that FileNotFoundError is raised for missing regime data."""
    with pytest.raises(FileNotFoundError):
        load_regime_data("nonexistent.csv")

def test_merge_datasets():
    """Test merging of three datasets."""
    df_fao = pd.DataFrame({'country_code': ['US', 'GB'], 'year': [2000, 2001], 'land_use_change_rate': [1.0, 2.0]})
    df_wb = pd.DataFrame({'country_code': ['US', 'GB'], 'year': [2000, 2001], 'gdp_per_capita': [50000, 40000]})
    df_regime = pd.DataFrame({'country_code': ['US', 'GB'], 'year': [2000, 2001], 'regime_type': [1, 0]})
    
    result = merge_datasets(df_fao, df_wb, df_regime)
    assert len(result) == 2
    assert 'land_use_change_rate' in result.columns
    assert 'gdp_per_capita' in result.columns
    assert 'regime_type' in result.columns

def test_drop_missing_primary_vars():
    """Test dropping rows with missing primary variables."""
    df = pd.DataFrame({
        'country_code': ['US', 'GB', 'FR'],
        'year': [2000, 2001, 2002],
        'land_use_change_rate': [1.0, np.nan, 3.0],
        'regime_type': [1, 0, np.nan]
    })
    result = drop_missing_primary_vars(df)
    assert len(result) == 0  # All rows have at least one missing primary var

def test_calculate_coverage_rate():
    """Test coverage rate calculation."""
    assert calculate_coverage_rate(50, 100) == 0.5
    assert calculate_coverage_rate(0, 100) == 0.0
    assert calculate_coverage_rate(10, 0) == 0.0  # Avoid division by zero

def test_apply_fr007_exclusion_secondary_missing():
    """Test FR-007: Exclude rows with missing secondary variables."""
    df = pd.DataFrame({
        'country_code': ['US', 'GB', 'FR'],
        'year': [2000, 2001, 2002],
        'land_use_change_rate': [1.0, 2.0, 3.0],
        'regime_type': [1, 0, 1],
        'gdp_per_capita': [50000, np.nan, 40000],
        'population_density': [100, 200, np.nan]
    })
    result = apply_fr007_exclusion(df)
    # All rows should be excluded because each has at least one missing secondary variable
    assert len(result) == 0

def test_apply_fr007_exclusion_primary_missing_country_exclusion():
    """Test FR-007: Exclude entire country if >20% primary data missing."""
    # Create a country with 5 years, 2 missing primary (40% > 20%)
    df = pd.DataFrame({
        'country_code': ['US', 'US', 'US', 'US', 'US', 'GB', 'GB', 'GB', 'GB', 'GB'],
        'year': [2000, 2001, 2002, 2003, 2004, 2000, 2001, 2002, 2003, 2004],
        'land_use_change_rate': [1.0, np.nan, np.nan, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        'regime_type': [1, 0, 1, 0, 1, 1, 1, 1, 1, 1],
        'gdp_per_capita': [50000, 50000, 50000, 50000, 50000, 40000, 40000, 40000, 40000, 40000],
        'population_density': [100, 100, 100, 100, 100, 200, 200, 200, 200, 200]
    })
    result = apply_fr007_exclusion(df)
    # US should be excluded (40% missing), GB should remain
    assert 'US' not in result['country_code'].values
    assert len(result) == 5  # Only GB rows

def test_apply_fr007_exclusion_primary_missing_below_threshold():
    """Test FR-007: Do not exclude country if <20% primary data missing."""
    # Create a country with 10 years, 1 missing primary (10% < 20%)
    df = pd.DataFrame({
        'country_code': ['US'] * 10 + ['GB'] * 10,
        'year': list(range(2000, 2010)) + list(range(2000, 2010)),
        'land_use_change_rate': [1.0] * 9 + [np.nan] + [1.0] * 10,
        'regime_type': [1] * 10 + [1] * 10,
        'gdp_per_capita': [50000] * 20,
        'population_density': [100] * 20
    })
    result = apply_fr007_exclusion(df)
    # US should NOT be excluded (10% missing), GB should remain
    assert 'US' in result['country_code'].values
    assert len(result) == 19  # 9 US rows + 10 GB rows

def test_apply_fr007_exclusion_mixed_logic():
    """Test FR-007: Combined primary and secondary variable exclusion."""
    df = pd.DataFrame({
        'country_code': ['US', 'US', 'GB', 'GB'],
        'year': [2000, 2001, 2000, 2001],
        'land_use_change_rate': [1.0, np.nan, 2.0, 3.0],
        'regime_type': [1, 0, 1, 1],
        'gdp_per_capita': [50000, 50000, np.nan, 40000],
        'population_density': [100, 100, 200, 200]
    })
    # US has 1 missing primary (50% > 20%) -> exclude country
    # GB has 1 missing secondary -> exclude row
    result = apply_fr007_exclusion(df)
    assert 'US' not in result['country_code'].values
    assert len(result) == 1  # Only one GB row remains (the one with complete secondary data)