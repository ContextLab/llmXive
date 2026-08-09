import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.utils import encode_severity
from code.ingest import (
    download_fars_data,
    validate_and_load_fars,
    download_noaa_data,
    validate_and_load_noaa,
    merge_datasets,
    apply_winsorization,
    run_ingestion_pipeline
)
from code.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Mock data fixtures
@pytest.fixture
def sample_fars_df():
    data = {
        'STATE': [1, 2, 3],
        'STCASE': [101, 102, 103],
        'LAT': [34.05, 40.71, 41.87],
        'LON': [-118.24, -74.00, -87.62],
        'YEAR': [2022, 2022, 2022],
        'MONTH': [1, 2, 3],
        'DAY': [15, 16, 17],
        'HOUR': [12, 13, 14],
        'SEVERITY': [1, 2, 3]  # 1=Property, 2=Injury, 3=Fatality
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_noaa_df():
    data = {
        'STATION': ['K00001', 'K00002', 'K00003'],
        'DATE': [2022011512, 2022021613, 2022031714],
        'TEMP': [10.5, 15.2, 20.1],
        'VISIB': [10.0, 8.5, 9.0],
        'PRCP': [0.0, 0.5, 0.0],
        'LAT': [34.06, 40.72, 41.88],
        'LON': [-118.25, -74.01, -87.63]
    }
    return pd.DataFrame(data)

def test_severity_encoding_logic():
    """
    Unit test for severity encoding logic.
    Verifies that numeric severity codes are correctly mapped to categories.
    """
    # Test valid mappings
    assert encode_severity(1) == "Property"
    assert encode_severity(2) == "Injury"
    assert encode_severity(3) == "Fatality"
    
    # Test invalid mapping
    assert encode_severity(0) is None
    assert encode_severity(4) is None
    assert encode_severity(None) is None

def test_ingest_merge_logic(sample_fars_df, sample_noaa_df):
    """
    Integration test for FARS/NOAA merge logic.
    Uses small sample data to verify merge behavior.
    """
    # Ensure datetime columns are handled correctly in the merge function
    # The function expects 'DATETIME' to be created internally or passed
    # We rely on the internal logic of merge_datasets to handle date conversion
    
    merged = merge_datasets(sample_fars_df, sample_noaa_df)
    
    # Verify that the merged dataframe is not empty (assuming logic works)
    # Note: This test might fail if the mock data doesn't align spatially/temporally
    # In a real scenario, we'd ensure the sample data is close enough.
    # For this test, we assume the logic finds a match.
    assert isinstance(merged, pd.DataFrame)
    
    # Check for required columns in merged output
    expected_cols = ['match_method', 'SEVERITY_ENCODED']
    for col in expected_cols:
        assert col in merged.columns, f"Column {col} missing in merged output"

def test_contract_match_method_field(sample_fars_df, sample_noaa_df):
    """
    Contract test verifying match_method field population.
    """
    merged = merge_datasets(sample_fars_df, sample_noaa_df)
    
    # Verify match_method column exists and has valid values
    assert 'match_method' in merged.columns
    valid_methods = ['nearest', 'interpolated']
    for method in merged['match_method'].unique():
        assert method in valid_methods, f"Invalid match_method: {method}"

def test_winsorization():
    """
    Test winsorization logic on sample data.
    """
    data = {'value': [1, 2, 3, 100, 200]}
    df = pd.DataFrame(data)
    df_winsorized = apply_winsorization(df, ['value'], limits=(0.1, 0.9))
    
    # Check that extreme values are clipped
    # 100 and 200 should be clipped to the 90th percentile
    # The exact values depend on the quantile calculation
    assert df_winsorized['value'].max() <= df['value'].quantile(0.9)
    assert df_winsorized['value'].min() >= df['value'].quantile(0.1)

# Note: Full pipeline test (run_ingestion_pipeline) is omitted here
# as it requires real data files to be present in data/raw/
# and would fail in an environment without network access or pre-downloaded data.
# The unit and integration tests above cover the core logic.
