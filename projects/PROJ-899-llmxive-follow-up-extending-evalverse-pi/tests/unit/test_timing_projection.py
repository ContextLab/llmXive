import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path if running standalone
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from src.models.evaluate import (
    calculate_inference_time_projection, 
    generate_timing_profile, 
    load_scaling_profile
)
from src.config import get_data_root

class TestInferenceTimeProjection:
    """Unit tests for T024 timing projection logic."""

    def test_calculate_projection_single_point(self):
        """Test projection with a single batch data point."""
        # Mock data: 100 clips took 10 seconds total
        scaling_df = pd.DataFrame({
            "batch_size": [100],
            "total_time_seconds": [10.0],
            "avg_time_per_clip": [0.1]
        })
        
        result = calculate_inference_time_projection(scaling_df, target_n=1000)
        
        assert result["target_n"] == 1000
        assert result["avg_time_per_clip_seconds"] == 0.1
        assert result["projected_total_seconds"] == 100.0
        assert result["projected_total_hours"] == 100.0 / 3600.0

    def test_calculate_projection_linear_regression(self):
        """Test projection uses linear regression for multiple points."""
        # Mock data: linear relationship
        scaling_df = pd.DataFrame({
            "batch_size": [100, 500, 1000],
            "total_time_seconds": [10.0, 50.0, 100.0],
            "avg_time_per_clip": [0.1, 0.1, 0.1]
        })
        
        result = calculate_inference_time_projection(scaling_df, target_n=10000)
        
        # Slope should be 0.1 (10/100 = 50/500 = 100/1000)
        assert result["avg_time_per_clip_seconds"] == 0.1
        assert result["projected_total_seconds"] == 1000.0
        assert result["method"] == "linear_scaling"

    def test_calculate_projection_empty_df(self):
        """Test that empty DataFrame raises error."""
        scaling_df = pd.DataFrame()
        with pytest.raises(ValueError, match="Scaling profile is empty"):
            calculate_inference_time_projection(scaling_df)

    @patch("src.models.evaluate.load_scaling_profile")
    @patch("src.models.evaluate.write_csv")
    def test_generate_timing_profile(self, mock_write_csv, mock_load_profile):
        """Test generate_timing_profile creates correct output."""
        # Mock scaling profile
        scaling_df = pd.DataFrame({
            "batch_size": [100],
            "total_time_seconds": [10.0],
            "avg_time_per_clip": [0.1]
        })
        mock_load_profile.return_value = scaling_df
        
        result = generate_timing_profile(target_n=10000)
        
        assert isinstance(result, pd.DataFrame)
        assert "projected_total_hours" in result.columns
        assert result["projected_total_hours"].iloc[0] > 0
        assert result["batch_size"].iloc[0] == 10000
        
        # Verify write_csv was called
        mock_write_csv.assert_called_once()

    def test_load_scaling_profile_missing_file(self, tmp_path):
        """Test loading when file does not exist."""
        # Temporarily patch get_data_root to return tmp_path
        with patch("src.models.evaluate.get_data_root", return_value=str(tmp_path)):
            result = load_scaling_profile()
            assert result is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])