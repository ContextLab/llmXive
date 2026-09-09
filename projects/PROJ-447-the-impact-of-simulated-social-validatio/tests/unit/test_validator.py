"""
Unit tests for code/data/validator.py (T013).

Tests:
1. Empty dataset raises DataGapError.
2. Small dataset (0 < N < 100) raises InsufficientSampleError.
3. Missing required columns raises ValueError.
4. Invalid longitudinal ordering raises ValueError.
5. Valid data passes validation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.exceptions import DataGapError, InsufficientSampleError
from utils.constants import get_min_sample_size
from code.data.validator import validate_data, REQUIRED_COLUMNS


def create_mock_dataframe(n_rows: int, valid_order: bool = True) -> pd.DataFrame:
    """Helper to create a mock DataFrame with required columns."""
    base_date = datetime(2023, 1, 1)
    data = {
        "engagement_count": np.random.randint(1, 100, n_rows),
        "sentiment_score": np.random.uniform(-1, 1, n_rows),
        "self_esteem_score": np.random.uniform(10, 50, n_rows),
        "perceived_social_validation": np.random.uniform(0, 1, n_rows),
    }

    if valid_order:
        # Engagement happens 1-5 days before self report
        eng_times = [base_date + timedelta(days=np.random.randint(1, 30)) for _ in range(n_rows)]
        rep_times = [t + timedelta(days=np.random.randint(1, 5)) for t in eng_times]
    else:
        # Invalid: Self report happens before or at same time as engagement
        rep_times = [base_date + timedelta(days=np.random.randint(1, 30)) for _ in range(n_rows)]
        eng_times = [t + timedelta(days=np.random.randint(1, 5)) for t in rep_times]

    data["engagement_timestamp"] = eng_times
    data["self_report_timestamp"] = rep_times

    return pd.DataFrame(data)


class TestValidator:
    def test_empty_dataset_raises_data_gap_error(self):
        """Test that N=0 raises DataGapError."""
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        with pytest.raises(DataGapError) as exc_info:
            validate_data(df)
        assert "empty" in str(exc_info.value).lower()

    def test_small_dataset_raises_insufficient_sample_error(self):
        """Test that 0 < N < 100 raises InsufficientSampleError."""
        min_sample = get_min_sample_size()
        small_n = min_sample - 1
        df = create_mock_dataframe(small_n)
        with pytest.raises(InsufficientSampleError) as exc_info:
            validate_data(df)
        assert "insufficient" in str(exc_info.value).lower()

    def test_missing_columns_raises_value_error(self):
        """Test that missing required columns raises ValueError."""
        df = create_mock_dataframe(150)
        # Drop a required column
        df = df.drop(columns=["sentiment_score"])
        with pytest.raises(ValueError) as exc_info:
            validate_data(df)
        assert "missing" in str(exc_info.value).lower()

    def test_invalid_longitudinal_order_raises_value_error(self):
        """Test that engagement >= self_report raises ValueError."""
        df = create_mock_dataframe(150, valid_order=False)
        with pytest.raises(ValueError) as exc_info:
            validate_data(df)
        assert "longitudinal" in str(exc_info.value).lower()

    def test_valid_data_passes_validation(self):
        """Test that a valid dataset returns the DataFrame."""
        df = create_mock_dataframe(150, valid_order=True)
        result = validate_data(df)
        assert result is df
        assert len(result) == 150