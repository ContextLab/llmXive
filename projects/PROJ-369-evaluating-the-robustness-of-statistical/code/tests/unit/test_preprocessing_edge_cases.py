import pytest
import numpy as np
import pandas as pd
import logging
from pathlib import Path
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.preprocessing import (
    preprocess_series, 
    PreprocessingError, 
    MAX_DIFFERENCING_LIMIT
)

class TestUnitRootFailure:
    """Tests for T063: Unit root failure handling"""
    
    def test_max_differencing_limit_enforced(self):
        """Test that series with unresolvable unit root fails after MAX_DIFFERENCING_LIMIT"""
        # Create a series that will never become stationary (e.g., random walk with drift)
        np.random.seed(42)
        n = 1000
        errors = np.random.normal(0, 1, n)
        # Create a series with a strong unit root that won't converge
        series = pd.Series(np.cumsum(errors) + np.arange(n) * 10)  # Strong drift
        
        with pytest.raises(PreprocessingError) as exc_info:
            preprocess_series(series)
        
        assert "unit root" in str(exc_info.value).lower() or "maximum differencing" in str(exc_info.value).lower()
        assert "unresolvable" in str(exc_info.value).lower()
    
    def test_critical_error_logged(self, caplog):
        """Test that critical error is logged when unit root fails"""
        np.random.seed(42)
        n = 500
        errors = np.random.normal(0, 1, n)
        series = pd.Series(np.cumsum(errors) + np.arange(n) * 50)  # Very strong drift
        
        caplog.set_level(logging.CRITICAL)
        
        with pytest.raises(PreprocessingError):
            preprocess_series(series)
        
        # Check that critical log message was emitted
        critical_logs = [record.message for record in caplog.records if record.levelno == logging.CRITICAL]
        assert any("maximum differencing" in msg.lower() or "unit root" in msg.lower() for msg in critical_logs)
    
    def test_pipeline_halts_on_unit_root_failure(self):
        """Test that the pipeline halts (raises exception) rather than continuing"""
        np.random.seed(42)
        n = 200
        errors = np.random.normal(0, 1, n)
        series = pd.Series(np.cumsum(errors) + np.arange(n) * 20)
        
        # Should raise exception, not return a processed series
        with pytest.raises(PreprocessingError):
            result = preprocess_series(series)
            # If we get here, the test fails
            assert False, "Expected PreprocessingError to be raised"
    
    def test_differencing_count_tracked(self):
        """Test that differencing count is tracked and reported in error"""
        np.random.seed(42)
        n = 300
        errors = np.random.normal(0, 1, n)
        series = pd.Series(np.cumsum(errors) + np.arange(n) * 10)
        
        with pytest.raises(PreprocessingError) as exc_info:
            preprocess_series(series)
        
        error_msg = str(exc_info.value)
        assert str(MAX_DIFFERENCING_LIMIT) in error_msg
    
    def test_valid_stationary_series_still_works(self):
        """Regression test: ensure valid stationary series still process correctly"""
        np.random.seed(42)
        # Stationary series (AR(1) with phi < 1)
        n = 200
        errors = np.random.normal(0, 1, n)
        series = pd.Series(np.zeros(n))
        for i in range(1, n):
            series.iloc[i] = 0.5 * series.iloc[i-1] + errors[i]
        
        result = preprocess_series(series)
        
        assert result['stationarity_status'] in ['already_stationary', 'stationary_after_differencing']
        assert 'processed_series' in result
        assert len(result['processed_series']) > 0