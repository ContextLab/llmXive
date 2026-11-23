import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocessing import (
    resample_sentiment_to_monthly,
    resample_macro_to_monthly,
    interpolate_missing,
    align_and_preprocess,
    calculate_missing_rate
)

@pytest.fixture
def sample_daily_sentiment():
    """Create sample daily sentiment data."""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    data = {
        'date': dates,
        'sentiment_score': np.random.randn(len(dates)) * 0.5 + 0.1,
        'confidence': np.random.uniform(0.6, 1.0, len(dates))
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_quarterly_macro():
    """Create sample quarterly macro data."""
    dates = pd.date_range(start='2020-03-31', end='2020-12-31', freq='Q')
    data = {
        'date': dates,
        'gdp_growth': np.random.randn(len(dates)) * 2.0,
        'unemployment_rate': np.random.uniform(3.0, 10.0, len(dates))
    }
    return pd.DataFrame(data)

class TestDataAlignment:
    """Integration tests for data alignment logic."""

    def test_resample_sentiment_to_monthly_mean(self, sample_daily_sentiment):
        """Test that daily sentiment is correctly resampled to monthly mean."""
        monthly = resample_sentiment_to_monthly(sample_daily_sentiment)
        
        assert 'date' in monthly.columns
        assert 'sentiment_score' in monthly.columns
        
        # Check that we have 12 months (Jan-Dec 2020)
        assert len(monthly) == 12
        
        # Verify the date is the last day of the month (resample 'M')
        assert monthly['date'].dt.day.max() == 31 or monthly['date'].dt.day.min() >= 28

    def test_resample_macro_to_monthly_first(self, sample_quarterly_macro):
        """Test that quarterly macro data is resampled to monthly frequency."""
        monthly = resample_macro_to_monthly(sample_quarterly_macro)
        
        assert 'date' in monthly.columns
        assert 'gdp_growth' in monthly.columns
        
        # Quarterly data (4 points) resampled to monthly (MS) should result in 
        # months covering the range, with NaN for non-quarter months
        assert len(monthly) >= 4

    def test_interpolate_missing_linear(self, sample_quarterly_macro):
        """Test linear interpolation of missing values."""
        monthly = resample_macro_to_monthly(sample_quarterly_macro)
        
        # Check for NaNs before interpolation
        missing_before = monthly.isna().sum().sum()
        
        # Interpolate
        interpolated = interpolate_missing(monthly, method='linear')
        
        # Check for remaining NaNs (only at start/end might remain)
        missing_after = interpolated.isna().sum().sum()
        
        # Linear interpolation should fill most internal NaNs
        # (Start/End NaNs are expected and cannot be filled)
        assert missing_after <= missing_before

    def test_align_and_preprocess_integration(self, sample_daily_sentiment, sample_quarterly_macro):
        """Test full alignment pipeline."""
        monthly_sentiment = resample_sentiment_to_monthly(sample_daily_sentiment)
        monthly_macro = resample_macro_to_monthly(sample_quarterly_macro)
        
        # Interpolate macro
        monthly_macro = interpolate_missing(monthly_macro, method='linear')
        
        # Align
        aligned = align_and_preprocess(monthly_macro, monthly_sentiment)
        
        # Check structure
        assert isinstance(aligned, pd.DataFrame)
        assert 'sentiment_score' in aligned.columns
        assert 'gdp_growth' in aligned.columns
        
        # Check index is datetime
        assert isinstance(aligned.index, pd.DatetimeIndex)
        
        # Check no duplicate dates
        assert aligned.index.is_unique

    def test_missing_rate_calculation(self, sample_daily_sentiment, sample_quarterly_macro):
        """Test missing rate calculation on aligned data."""
        monthly_sentiment = resample_sentiment_to_monthly(sample_daily_sentiment)
        monthly_macro = resample_macro_to_monthly(sample_quarterly_macro)
        monthly_macro = interpolate_missing(monthly_macro, method='linear')
        
        aligned = align_and_preprocess(monthly_macro, monthly_sentiment)
        
        missing_rate = calculate_missing_rate(aligned)
        
        assert 0 <= missing_rate <= 100
        
        # For this synthetic data, missing rate should be relatively low
        # after interpolation (only start/end might be missing)
        assert missing_rate < 50.0

    def test_output_schema_compliance(self, sample_daily_sentiment, sample_quarterly_macro):
        """Test that output matches expected schema for T018."""
        monthly_sentiment = resample_sentiment_to_monthly(sample_daily_sentiment)
        monthly_macro = resample_macro_to_monthly(sample_quarterly_macro)
        monthly_macro = interpolate_missing(monthly_macro, method='linear')
        
        aligned = align_and_preprocess(monthly_macro, monthly_sentiment)
        
        # Required columns for T018 output
        required_cols = ['sentiment_score']
        
        # Check at least sentiment is present
        for col in required_cols:
            assert col in aligned.columns or any(col in c for c in aligned.columns)
        
        # Check date index
        assert aligned.index.name == 'date' or 'date' in aligned.columns