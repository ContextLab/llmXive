import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.models import NetworkMetric, CorrelationResult, SensitivityReport

class TestMetricSchema:
    """Contract tests for metric calculation outputs."""

    def test_metric_schema_has_required_columns(self):
        """Verify NetworkMetric, CorrelationResult, and SensitivityReport have required fields."""
        
        # Test NetworkMetric
        metric = NetworkMetric(subject_id="sub-001", metric_name="global_efficiency", value=0.45)
        assert hasattr(metric, 'subject_id')
        assert hasattr(metric, 'metric_name')
        assert hasattr(metric, 'value')
        assert metric.subject_id == "sub-001"
        assert metric.metric_name == "global_efficiency"
        assert metric.value == 0.45

        # Test CorrelationResult
        corr = CorrelationResult(metric="global_efficiency", genre="rock", r=0.35, p_raw=0.02, p_adj=0.04)
        assert hasattr(corr, 'metric')
        assert hasattr(corr, 'genre')
        assert hasattr(corr, 'r')
        assert hasattr(corr, 'p_raw')
        assert hasattr(corr, 'p_adj')
        assert corr.metric == "global_efficiency"
        assert corr.genre == "rock"
        assert corr.r == 0.35
        assert corr.p_raw == 0.02
        assert corr.p_adj == 0.04

        # Test SensitivityReport
        report = SensitivityReport(window_size=30, icc=0.75)
        assert hasattr(report, 'window_size')
        assert hasattr(report, 'icc')
        assert report.window_size == 30
        assert report.icc == 0.75

    def test_metric_values_in_range(self):
        """Verify metric values fall within plausible ranges."""
        
        # Test NetworkMetric value ranges (efficiency typically 0-1, modularity 0-1)
        valid_efficiency = NetworkMetric(subject_id="sub-001", metric_name="global_efficiency", value=0.45)
        assert 0.0 <= valid_efficiency.value <= 1.0, "Efficiency should be between 0 and 1"

        # Test negative values for some metrics (e.g., z-scored connectivity)
        valid_zscore = NetworkMetric(subject_id="sub-002", metric_name="z_score", value=-1.2)
        assert valid_zscore.value < 0, "Z-score can be negative"

        # Test CorrelationResult r values (-1 to 1)
        valid_corr = CorrelationResult(metric="global_efficiency", genre="rock", r=0.85, p_raw=0.001, p_adj=0.005)
        assert -1.0 <= valid_corr.r <= 1.0, "Correlation coefficient must be between -1 and 1"
        assert 0.0 <= valid_corr.p_raw <= 1.0, "P-value must be between 0 and 1"
        assert 0.0 <= valid_corr.p_adj <= 1.0, "Adjusted p-value must be between 0 and 1"

        # Test invalid r value (should raise validation error or be caught)
        with pytest.raises(Exception):
            CorrelationResult(metric="global_efficiency", genre="rock", r=1.5, p_raw=0.001, p_adj=0.005)

        # Test SensitivityReport ICC values (typically 0-1)
        valid_icc = SensitivityReport(window_size=30, icc=0.85)
        assert 0.0 <= valid_icc.icc <= 1.0, "ICC should be between 0 and 1"

        # Test invalid ICC
        with pytest.raises(Exception):
            SensitivityReport(window_size=30, icc=1.5)

    def test_schema_serialization(self):
        """Verify models can be serialized to JSON."""
        
        metric = NetworkMetric(subject_id="sub-001", metric_name="modularity_Q", value=0.32)
        json_str = metric.model_dump_json()
        assert json_str is not None
        assert "sub-001" in json_str
        assert "modularity_Q" in json_str

        corr = CorrelationResult(metric="global_efficiency", genre="jazz", r=0.22, p_raw=0.08, p_adj=0.12)
        json_str = corr.model_dump_json()
        assert json_str is not None
        assert "jazz" in json_str

        report = SensitivityReport(window_size=40, icc=0.65)
        json_str = report.model_dump_json()
        assert json_str is not None
        assert "40" in json_str