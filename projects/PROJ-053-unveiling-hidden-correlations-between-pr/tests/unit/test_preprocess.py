import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocess import check_sample_count, load_raw_csv, detect_missing_values

class TestSampleCountCheck:
    """Tests for T019: Sample count check (N < 50)"""

    def test_passes_with_50_samples(self):
        """Test that exactly 50 samples passes the check."""
        df = pd.DataFrame({'col': range(50)})
        # Should not raise
        check_sample_count(df, min_count=50)

    def test_passes_with_more_than_50_samples(self):
        """Test that more than 50 samples passes the check."""
        df = pd.DataFrame({'col': range(100)})
        check_sample_count(df, min_count=50)

    def test_fails_with_less_than_50_samples(self):
        """Test that less than 50 samples raises ValueError."""
        df = pd.DataFrame({'col': range(49)})
        with pytest.raises(ValueError) as exc_info:
            check_sample_count(df, min_count=50)
        
        assert "Insufficient sample size" in str(exc_info.value)
        assert "49" in str(exc_info.value)
        assert "50" in str(exc_info.value)

    def test_fails_with_empty_dataframe(self):
        """Test that an empty dataframe raises ValueError."""
        df = pd.DataFrame({'col': []})
        with pytest.raises(ValueError) as exc_info:
            check_sample_count(df, min_count=50)
        
        assert "Insufficient sample size" in str(exc_info.value)
        assert "0" in str(exc_info.value)

    def test_custom_min_count(self):
        """Test with a custom minimum count."""
        df = pd.DataFrame({'col': range(9)})
        with pytest.raises(ValueError) as exc_info:
            check_sample_count(df, min_count=10)
        
        assert "9" in str(exc_info.value)
        assert "10" in str(exc_info.value)