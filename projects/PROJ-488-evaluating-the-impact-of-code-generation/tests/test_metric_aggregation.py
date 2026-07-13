"""
Tests for metric aggregation module (T023).
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from metric_aggregation import (
    load_metrics_for_group,
    aggregate_metrics,
    write_aggregate_csv,
    run_aggregation
)
from data_model import validate_metric_result

class TestMetricAggregation:
    """Test cases for metric aggregation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "data" / "processed"
        self.metrics_dir = Path(self.temp_dir) / "data" / "metrics"
        
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the global paths
        self.original_processed_dir = None
        self.original_metrics_dir = None

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_aggregate_metrics_basic(self):
        """Test basic aggregation of scores."""
        # Create sample data
        scores = [10.0, 12.0, 8.0, 15.0, 11.0]
        df = pd.DataFrame({"score": scores})
        
        agg = aggregate_metrics(df, "test_metric", "human_written")
        
        assert agg["count"] == 5
        assert agg["mean"] == pytest.approx(11.2)
        assert agg["median"] == pytest.approx(11.0)
        assert agg["variance"] > 0
        assert agg["min"] == 8.0
        assert agg["max"] == 15.0
        assert agg["group"] == "human_written"
        assert agg["metric_type"] == "test_metric"

    def test_aggregate_metrics_empty(self):
        """Test aggregation with no valid scores."""
        df = pd.DataFrame({"score": [None, None, None]})
        
        agg = aggregate_metrics(df, "test_metric", "human_written")
        
        assert agg["count"] == 0
        assert agg["mean"] is None
        assert agg["median"] is None
        assert agg["variance"] is None

    def test_write_aggregate_csv(self):
        """Test writing aggregates to CSV."""
        aggregates = [
            {"metric_type": "test", "group": "human", "count": 10, "mean": 5.0},
            {"metric_type": "test", "group": "llm", "count": 10, "mean": 6.0}
        ]
        
        output_path = write_aggregate_csv(aggregates, "test")
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "metric_type" in df.columns
        assert "group" in df.columns

    def test_load_metrics_for_group_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_metrics_for_group("human_written", "missing_metric")

    def test_run_aggregation_integration(self):
        """Test the full aggregation workflow with mock data."""
        # Create mock metric files
        metric_types = ["cyclomatic_complexity", "lines_of_code"]
        groups = ["human_written", "llm_generated"]
        
        for metric_type in metric_types:
            for group in groups:
                scores = np.random.rand(50) * 10
                df = pd.DataFrame({"score": scores})
                file_path = self.processed_dir / f"{group}_{metric_type}.csv"
                df.to_csv(file_path, index=False)
        
        # Patch the global paths
        with patch("metric_aggregation.PROCESSED_DIR", self.processed_dir):
            with patch("metric_aggregation.METRICS_DIR", self.metrics_dir):
                with patch("metric_aggregation.REGISTER_ARTIFACT_HASH", MagicMock()):
                    output_files = run_aggregation(metric_types)
        
        assert len(output_files) == len(metric_types)
        
        for metric_type in metric_types:
            output_path = output_files[metric_type]
            assert output_path.exists()
            df = pd.read_csv(output_path)
            assert len(df) == 2  # Two groups
            assert "mean" in df.columns
            assert "median" in df.columns
            assert "variance" in df.columns

    def test_aggregate_metrics_nan_handling(self):
        """Test that NaN values are properly handled."""
        scores = [10.0, np.nan, 12.0, np.nan, 8.0]
        df = pd.DataFrame({"score": scores})
        
        agg = aggregate_metrics(df, "test_metric", "human_written")
        
        # Should only count non-NaN values
        assert agg["count"] == 3
        assert agg["mean"] == pytest.approx(10.0)  # (10+12+8)/3

import pytest

if __name__ == "__main__":
    pytest.main([__file__, "-v"])