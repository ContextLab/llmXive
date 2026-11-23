"""
Tests for T013: Behavioral Metrics Extraction.
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code_04_extract_behavioral_metrics import process_behavioral_data

class TestBehavioralMetrics:
    def test_outlier_exclusion(self):
        """Test that outliers (<100ms, >2000ms) are excluded."""
        data = {
            "participant_id": ["001"] * 10,
            "rt_ms": [50, 100, 150, 2000, 2500, 1000, 1500, 120, 1800, 500]
        }
        df = pd.DataFrame(data)
        metrics, exclusion = process_behavioral_data(df)

        # 50 and 2500 should be excluded.
        # Remaining: 100, 150, 2000, 1000, 1500, 120, 1800, 500 (8 trials)
        # Original: 10. Excluded: 2.
        assert metrics.loc[0, "n_trials"] == 8
        assert metrics.loc[0, "n_trials_excluded"] == 2
        
        # Check median of remaining
        expected_median = np.median([100, 150, 2000, 1000, 1500, 120, 1800, 500])
        assert metrics.loc[0, "median_rt"] == expected_median

    def test_retention_rate_exclusion(self):
        """Test that participants with <70% retention are excluded."""
        # 10 trials, 3 are valid -> 30% retention -> exclude
        data = {
            "participant_id": ["002"] * 10,
            "rt_ms": [50, 50, 50, 50, 50, 50, 50, 100, 200, 300]
        }
        df = pd.DataFrame(data)
        metrics, exclusion = process_behavioral_data(df)

        assert len(metrics) == 0
        assert len(exclusion) == 1
        assert exclusion.iloc[0]["participant_id"] == "002"
        assert "Retention rate < 70%" in exclusion.iloc[0]["reason"]

    def test_retention_rate_pass(self):
        """Test that participants with >=70% retention are kept."""
        # 10 trials, 7 are valid -> 70% retention -> keep
        data = {
            "participant_id": ["003"] * 10,
            "rt_ms": [50, 50, 50, 50, 50, 50, 50, 100, 200, 300]
        }
        # Wait, 50 is < 100, so 7 outliers. 3 valid. 30% -> exclude.
        # Let's make 7 valid.
        data = {
            "participant_id": ["004"] * 10,
            "rt_ms": [100, 100, 100, 100, 100, 100, 100, 50, 50, 50]
        }
        df = pd.DataFrame(data)
        metrics, exclusion = process_behavioral_data(df)

        assert len(metrics) == 1
        assert len(exclusion) == 0
        assert metrics.iloc[0]["n_trials"] == 7

    def test_multiple_participants(self):
        """Test processing multiple participants."""
        data = {
            "participant_id": ["001"] * 5 + ["002"] * 5,
            "rt_ms": [100, 200, 300, 400, 500] + [50, 50, 100, 200, 300]
        }
        df = pd.DataFrame(data)
        metrics, exclusion = process_behavioral_data(df)

        assert len(metrics) == 1 # Only 001 should pass (5/5 = 100%)
        assert len(exclusion) == 1 # 002 (2/5 = 40%)
        assert metrics.iloc[0]["participant_id"] == "001"
        assert exclusion.iloc[0]["participant_id"] == "002"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])