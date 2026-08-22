"""
Integration tests for preprocessing edge cases (T063).

Tests the full preprocessing pipeline with edge cases.
"""

import pytest
import numpy as np
import pandas as pd
import logging
from pathlib import Path
import sys
import os
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.preprocessing import preprocess_dataset, PreprocessingError
from src.utils.logging import setup_logger
from src.utils.config import get_path

# Setup logger
setup_logger(level=logging.INFO)

class TestEdgeCase2Integration:
    """Integration tests for T063: Unit root failure handling."""
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return data_dir
    
    def test_unit_root_failure_integration(self, temp_data_dir):
        """Test unit root failure in full pipeline."""
        # Create a random walk series (unit root)
        np.random.seed(42)
        n = 1000
        errors = np.random.randn(n)
        series = pd.Series(np.cumsum(errors), name="random_walk")
        
        # Save to CSV
        csv_path = temp_data_dir / "unit_root_test.csv"
        series.to_csv(csv_path, index=True)
        
        # Try to preprocess - should fail
        with pytest.raises(PreprocessingError) as exc_info:
            preprocess_dataset(csv_path, series_id="unit_root_integration")
        
        assert "Unit root failure" in str(exc_info.value)
    
    def test_trend_stationary_integration(self, temp_data_dir):
        """Test trend-stationary series in full pipeline."""
        # Create a trend-stationary series
        np.random.seed(42)
        n = 200
        x = np.arange(n)
        trend = 0.5 * x + 5
        noise = np.random.randn(n) * 0.3
        series = pd.Series(trend + noise, name="trend_stationary")
        
        # Save to CSV
        csv_path = temp_data_dir / "trend_stationary_test.csv"
        series.to_csv(csv_path, index=True)
        
        # Preprocess - should succeed
        result = preprocess_dataset(csv_path, series_id="trend_stationary_integration")
        
        assert result['status'] == 'success'
        assert result['detrending_status'] == 'success'
    
    def test_multiple_series_mixed_behavior(self, temp_data_dir):
        """Test multiple series with different behaviors."""
        results = {}
        
        # Series 1: Stationary (white noise)
        np.random.seed(42)
        series1 = pd.Series(np.random.randn(100), name="stationary")
        csv_path1 = temp_data_dir / "series1.csv"
        series1.to_csv(csv_path1, index=True)
        
        # Series 2: Trend-stationary
        x = np.arange(100)
        series2 = pd.Series(2 * x + np.random.randn(100) * 0.5, name="trend")
        csv_path2 = temp_data_dir / "series2.csv"
        series2.to_csv(csv_path2, index=True)
        
        # Series 3: Random walk (unit root)
        series3 = pd.Series(np.cumsum(np.random.randn(100)), name="random_walk")
        csv_path3 = temp_data_dir / "series3.csv"
        series3.to_csv(csv_path3, index=True)
        
        # Process all
        result1 = preprocess_dataset(csv_path1, series_id="s1")
        result2 = preprocess_dataset(csv_path2, series_id="s2")
        
        with pytest.raises(PreprocessingError):
            preprocess_dataset(csv_path3, series_id="s3")
        
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'
        assert result1['differencing_count'] == 0
        assert result2['detrending_status'] == 'success'
