import pytest
import pandas as pd
import numpy as np
from preprocessing import preprocess_flight_delays

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with mixed delay scenarios."""
    data = {
        'CarrierType': ['U', 'U', 'U', 'U', 'U', 'U', 'U'],
        'ArrDelay': [0, 10, -5, 1500, 15000, 0, 5],
        'DepDelay': [0, 5, -2, 100, 10000, 0, 2],
        'OtherCol': [1, 2, 3, 4, 5, 6, 7]
    }
    return pd.DataFrame(data)

def test_negative_delay_removal(sample_df):
    """Test that negative total delays are removed."""
    # Row 2: ArrDelay=-5, DepDelay=-2 -> total=-7 (should be removed)
    primary, non_zero, stats = preprocess_flight_delays(sample_df)
    
    # Check that no negative total delays exist
    assert (primary['total_delay'] < 0).sum() == 0
    # Original had 7 rows, one negative -> 6 remaining (excluding data errors later)
    # Row 4 (15000) is a data error, Row 3 (1500) is anomaly but kept in primary
    assert len(primary) == 5 # 7 - 1 (neg) - 1 (error)

def test_data_error_exclusion(sample_df):
    """Test that data errors (>10000) are excluded from primary set."""
    primary, non_zero, stats = preprocess_flight_delays(sample_df)
    
    # Row 4 (15000) should be excluded
    assert (primary['total_delay'] > 10000).sum() == 0
    assert len(primary) < len(sample_df)

def test_zero_exclusion_subset(sample_df):
    """Test that non_zero_df contains only positive delays."""
    primary, non_zero, stats = preprocess_flight_delays(sample_df)
    
    assert (non_zero['total_delay'] > 0).all()
    assert len(non_zero) < len(primary) # Should have fewer rows due to zeros

def test_zero_inflation_flagging(sample_df):
    """Test that zero-inflation flag is set correctly based on proportion."""
    # Create a dataset with high zero proportion
    high_zero_data = {
        'CarrierType': ['U'] * 10,
        'ArrDelay': [0] * 8 + [10, 20],
        'DepDelay': [0] * 8 + [5, 10]
    }
    df = pd.DataFrame(high_zero_data)
    
    # 8 zeros out of 8 valid (after neg/error removal) = 100% zero
    primary, non_zero, stats = preprocess_flight_delays(df)
    
    assert stats['is_zero_inflated'] == True
    assert stats['zero_proportion'] > 0.20

def test_retention_rate_failure():
    """Test that SystemExit is raised if retention rate < 95%."""
    # Create a dataset where most rows are invalid (e.g., negative or errors)
    bad_data = {
        'CarrierType': ['U'] * 100,
        'ArrDelay': [-1] * 50 + [10] * 50, # 50% negative
        'DepDelay': [0] * 100
    }
    df = pd.DataFrame(bad_data)
    
    with pytest.raises(SystemExit) as exc_info:
        preprocess_flight_delays(df)
    
    assert "Retention Rate Failure" in str(exc_info.value)

def test_memory_estimation_logic():
    """Test the logic for estimating memory usage based on row count and columns."""
    from preprocessing import estimate_csv_memory
    
    # Test with a hypothetical large dataset
    estimated_gb = estimate_csv_memory(1_000_000, 20)
    
    # Basic sanity check: should be a positive float
    assert isinstance(estimated_gb, float)
    assert estimated_gb > 0
    
    # Test with small dataset
    estimated_gb_small = estimate_csv_memory(100, 5)
    assert estimated_gb_small < estimated_gb

def test_anomaly_flagging_logic():
    """Test the logic for flagging anomalies (>1440 min) vs data errors (>10000 min)."""
    data = {
        'CarrierType': ['U', 'U', 'U'],
        'ArrDelay': [100, 1500, 15000],
        'DepDelay': [0, 0, 0]
    }
    df = pd.DataFrame(data)
    
    primary, non_zero, stats = preprocess_flight_delays(df)
    
    # Row 1 (1500) should be flagged as anomaly but kept in primary (unless filtered later)
    # Row 2 (15000) should be excluded as data error
    
    # Check that 15000 is NOT in primary (excluded as data error)
    assert 15000 not in primary['total_delay'].values
    
    # Check that 1500 IS in primary (anomaly, not error, so kept)
    assert 1500 in primary['total_delay'].values
    
    # Verify stats contain anomaly info if implemented
    if 'anomaly_count' in stats:
        assert stats['anomaly_count'] >= 1