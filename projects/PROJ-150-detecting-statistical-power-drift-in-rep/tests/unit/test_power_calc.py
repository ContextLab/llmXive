import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.power_calc import calculate_power_cohen_d, filter_and_log_invalid_rows
from code.logging_config import get_module_logger
import logging

class TestPowerCalcHandlesNan:
    """
    Unit test for T010: test_power_calc_handles_nan
    Verifies that power calculation handles NaN inputs gracefully (by filtering).
    """

    def test_filter_removes_nan_rows(self, tmp_path):
        """Test that rows with NaN in effect_size or sample_size are filtered out."""
        # Create a sample dataframe with NaNs
        data = {
            'study_id': [1, 2, 3, 4],
            'effect_size': [0.5, np.nan, 0.8, 0.0],
            'sample_size': [100, 200, np.nan, 50]
        }
        df = pd.DataFrame(data)
        
        # Setup a temporary logger to capture warnings
        logger = get_module_logger("test_power_calc")
        logger.setLevel(logging.WARNING)
        
        # Create a handler to capture log output
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)
        
        # Filter rows
        cleaned_df = filter_and_log_invalid_rows(df, logger)
        
        # Remove handler
        logger.removeHandler(handler)
        
        # Verify that NaN rows were removed
        assert len(cleaned_df) == 2, "Expected 2 valid rows after filtering NaNs"
        assert list(cleaned_df['study_id']) == [1, 4], "Expected study_ids 1 and 4 to remain"

    def test_calculate_power_raises_on_zero_sample(self):
        """Test that ZeroDivisionError is raised for non-positive sample size."""
        with pytest.raises(ZeroDivisionError):
            calculate_power_cohen_d(effect_size=0.5, sample_size=0)
        
        with pytest.raises(ZeroDivisionError):
            calculate_power_cohen_d(effect_size=0.5, sample_size=-10)

    def test_calculate_power_valid(self):
        """Test that power calculation returns a valid float between 0 and 1."""
        power = calculate_power_cohen_d(effect_size=0.5, sample_size=100)
        assert isinstance(power, float)
        assert 0.0 <= power <= 1.0