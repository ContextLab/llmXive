"""
Integration tests for the data ingestion pipeline (US1).
Tests that real data can be downloaded and processed correctly.
"""
import pytest
import pandas as pd
from pathlib import Path
import logging

from src.data.ingestion import (
    load_noaa_data,
    load_yahoo_finance_data,
    load_uk_national_grid_data,
    load_fred_gdp_data,
    load_world_bank_data,
    run_full_ingestion_pipeline
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def ingestion_results():
    """Run the full ingestion pipeline and return results."""
    try:
        return run_full_ingestion_pipeline()
    except Exception as e:
        pytest.fail(f"Ingestion pipeline failed: {e}")

def test_noaa_data_loads(ingestion_results):
    """Test that NOAA temperature data loads successfully."""
    assert 'noaa_temp' in ingestion_results
    df = ingestion_results['noaa_temp']
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'noaa_temp_anomaly' in df.columns
    
    # Check for missing values (should be minimal after processing)
    assert df.isnull().sum().sum() < len(df) * 0.1  # Less than 10% missing

def test_yahoo_finance_loads(ingestion_results):
    """Test that Yahoo Finance data loads successfully."""
    assert 'finance' in ingestion_results
    df = ingestion_results['finance']
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    
    # Check for expected columns (S&P 500, NASDAQ, Dow Jones)
    expected_cols = ['^GSPC', '^IXIC', '^DJI']
    for col in expected_cols:
        assert col in df.columns

def test_uk_national_grid_loads(ingestion_results):
    """Test that UK National Grid data loads successfully."""
    assert 'uk_grid' in ingestion_results
    df = ingestion_results['uk_grid']
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'uk_demand_mw' in df.columns

def test_fred_gdp_loads(ingestion_results):
    """Test that FRED GDP data loads successfully."""
    assert 'fred_gdp' in ingestion_results
    df = ingestion_results['fred_gdp']
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'us_gdp_billions' in df.columns

def test_world_bank_loads(ingestion_results):
    """Test that World Bank data loads successfully."""
    assert 'world_bank' in ingestion_results
    df = ingestion_results['world_bank']
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'global_inflation_pct' in df.columns

def test_all_datasets_have_valid_data(ingestion_results):
    """Test that all datasets have valid numeric data."""
    for name, df in ingestion_results.items():
        # Check that all columns are numeric
        for col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"Column {col} in dataset {name} is not numeric"
        
        # Check for reasonable data ranges (no infinite values)
        assert not np.isinf(df.values).any(), \
            f"Dataset {name} contains infinite values"

def test_data_has_datetime_index(ingestion_results):
    """Test that all datasets have a proper datetime index."""
    for name, df in ingestion_results.items():
        assert isinstance(df.index, pd.DatetimeIndex), \
            f"Dataset {name} does not have a DatetimeIndex"
        
        # Check that the index is sorted
        assert df.index.is_monotonic_increasing, \
            f"Dataset {name} index is not sorted"

def test_no_synthetic_fallback_used(ingestion_results):
    """
    Verify that no synthetic/fake data was used as a fallback.
    This test ensures that the 'fail loudly' requirement is met.
    """
    for name, df in ingestion_results.items():
        # Real data should have some variability
        assert df.std().sum() > 0, \
            f"Dataset {name} appears to be constant (possible synthetic fallback)"
        
        # Real data should not have suspiciously perfect patterns
        # (e.g., all zeros, all same value)
        unique_values = df.nunique().sum()
        assert unique_values > 10, \
            f"Dataset {name} has too few unique values (possible synthetic fallback)"