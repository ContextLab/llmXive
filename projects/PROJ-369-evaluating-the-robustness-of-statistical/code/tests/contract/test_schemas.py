"""
Contract tests for data schemas.

Verifies that the data schemas (TimeSeries, SyntheticData, TestResult, ErrorRateSummary)
are correctly defined, can be instantiated, and support serialization/deserialization.
"""
import pytest
import sys
import os
import numpy as np
from datetime import datetime
from dataclasses import fields

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.schemas import TimeSeries, SyntheticData, TestResult, ErrorRateSummary


class TestTimeSeriesSchema:
    """Tests for the TimeSeries schema."""

    def test_time_series_creation(self):
        """Test that a TimeSeries object can be created with required fields."""
        ts = TimeSeries(
            source_name="NOAA",
            dataset_id="test_001",
            timestamp=datetime.now(),
            frequency="H",
            length=100,
            has_missing=False,
            is_stationary=True,
            preprocessing_method="none",
            data=np.array([1.0, 2.0, 3.0])
        )
        
        assert ts.source_name == "NOAA"
        assert ts.dataset_id == "test_001"
        assert ts.length == 100
        assert ts.is_stationary is True
        assert np.array_equal(ts.data, np.array([1.0, 2.0, 3.0]))

    def test_time_series_to_dict(self):
        """Test serialization of TimeSeries to dictionary."""
        ts = TimeSeries(
            source_name="Yahoo",
            dataset_id="stock_AAPL",
            timestamp=datetime(2023, 1, 1),
            frequency="D",
            length=365,
            has_missing=True,
            is_stationary=False,
            preprocessing_method="diff",
            data=np.array([100.0, 101.0, 102.0])
        )
        
        data_dict = ts.to_dict()
        
        assert isinstance(data_dict, dict)
        assert data_dict["source_name"] == "Yahoo"
        assert data_dict["dataset_id"] == "stock_AAPL"
        assert data_dict["timestamp"] == "2023-01-01T00:00:00"
        assert "data" in data_dict
        assert isinstance(data_dict["data"], list)

    def test_time_series_from_dict(self):
        """Test deserialization of TimeSeries from dictionary."""
        input_data = {
            "source_name": "UK_Grid",
            "dataset_id": "load_2023",
            "timestamp": "2023-06-15T12:00:00",
            "frequency": "H",
            "length": 8760,
            "has_missing": False,
            "is_stationary": True,
            "preprocessing_method": "detrend",
            "data": [1.0, 2.0, 3.0, 4.0],
            "metadata": {"region": "London"}
        }
        
        ts = TimeSeries.from_dict(input_data)
        
        assert ts.source_name == "UK_Grid"
        assert ts.dataset_id == "load_2023"
        assert ts.length == 8760
        assert ts.metadata["region"] == "London"
        assert len(ts.data) == 4


class TestSyntheticDataSchema:
    """Tests for the SyntheticData schema."""

    def test_synthetic_data_creation(self):
        """Test that a SyntheticData object can be created with required fields."""
        sd = SyntheticData(
            generation_id="synth_001",
            timestamp=datetime.now(),
            process_type="fGn",
            hurst_exponent=0.8,
            mean=0.0,
            length=1000,
            seed=42,
            data=np.random.randn(1000)
        )
        
        assert sd.process_type == "fGn"
        assert sd.hurst_exponent == 0.8
        assert sd.seed == 42
        assert len(sd.data) == 1000

    def test_synthetic_data_metrics(self):
        """Test that metrics can be stored in SyntheticData."""
        sd = SyntheticData(
            generation_id="synth_002",
            timestamp=datetime.now(),
            process_type="ARFIMA",
            hurst_exponent=0.7,
            mean=0.0,
            length=500,
            seed=123,
            data=np.random.randn(500),
            metrics={"acf_lag1": 0.5, "hurst_est": 0.69}
        )
        
        assert sd.metrics["acf_lag1"] == 0.5
        assert sd.metrics["hurst_est"] == 0.69

    def test_synthetic_data_serialization(self):
        """Test round-trip serialization of SyntheticData."""
        original = SyntheticData(
            generation_id="synth_003",
            timestamp=datetime(2023, 5, 20),
            process_type="fGn",
            hurst_exponent=0.9,
            mean=0.0,
            length=200,
            seed=999,
            data=np.array([0.1, 0.2, 0.3]),
            is_shuffled=True
        )
        
        data_dict = original.to_dict()
        restored = SyntheticData.from_dict(data_dict)
        
        assert restored.generation_id == original.generation_id
        assert restored.hurst_exponent == original.hurst_exponent
        assert restored.is_shuffled is True
        assert np.array_equal(restored.data, original.data)


class TestTestResultSchema:
    """Tests for the TestResult schema."""

    def test_test_result_creation(self):
        """Test that a TestResult object can be created with required fields."""
        tr = TestResult(
            test_id="test_001",
            dataset_id="synth_001",
            test_type="t_test",
            timestamp=datetime.now(),
            null_hypothesis="Mean is zero",
            alpha=0.05,
            statistic=1.96,
            p_value=0.05,
            rejected=False,
            true_hurst=0.5
        )
        
        assert tr.test_type == "t_test"
        assert tr.alpha == 0.05
        assert tr.rejected is False
        assert tr.true_hurst == 0.5

    def test_test_result_rejection(self):
        """Test a TestResult where null hypothesis is rejected."""
        tr = TestResult(
            test_id="test_002",
            dataset_id="synth_002",
            test_type="f_test",
            timestamp=datetime.now(),
            null_hypothesis="Variances are equal",
            alpha=0.05,
            statistic=4.5,
            p_value=0.01,
            rejected=True,
            true_hurst=0.8,
            ground_truth_label="true_alternative"
        )
        
        assert tr.rejected is True
        assert tr.p_value < tr.alpha
        assert tr.ground_truth_label == "true_alternative"

    def test_test_result_serialization(self):
        """Test round-trip serialization of TestResult."""
        original = TestResult(
            test_id="test_003",
            dataset_id="real_001",
            test_type="t_test",
            timestamp=datetime(2023, 8, 10),
            null_hypothesis="Mean is zero",
            alpha=0.01,
            statistic=2.5,
            p_value=0.012,
            rejected=False,
            is_shuffled=True
        )
        
        data_dict = original.to_dict()
        restored = TestResult.from_dict(data_dict)
        
        assert restored.test_id == original.test_id
        assert restored.is_shuffled is True
        assert restored.rejected is False


class TestErrorRateSummarySchema:
    """Tests for the ErrorRateSummary schema."""

    def test_error_rate_summary_creation(self):
        """Test that an ErrorRateSummary object can be created with required fields."""
        ers = ErrorRateSummary(
            summary_id="summary_001",
            timestamp=datetime.now(),
            configuration={"H": 0.8, "N": 1000, "test": "t_test"},
            total_trials=10000,
            total_rejections=500,
            observed_error_rate=0.05,
            expected_error_rate=0.05
        )
        
        assert ers.total_trials == 10000
        assert ers.observed_error_rate == 0.05
        assert ers.configuration["H"] == 0.8

    def test_error_rate_summary_with_ci(self):
        """Test ErrorRateSummary with confidence intervals."""
        ers = ErrorRateSummary(
            summary_id="summary_002",
            timestamp=datetime.now(),
            configuration={"H": 0.9, "N": 500},
            total_trials=5000,
            total_rejections=600,
            observed_error_rate=0.12,
            expected_error_rate=0.05,
            confidence_interval_lower=0.11,
            confidence_interval_upper=0.13,
            vif=2.5,
            n_eff=400
        )
        
        assert ers.confidence_interval_lower == 0.11
        assert ers.vif == 2.5
        assert ers.n_eff == 400

    def test_error_rate_summary_serialization(self):
        """Test round-trip serialization of ErrorRateSummary."""
        original = ErrorRateSummary(
            summary_id="summary_003",
            timestamp=datetime(2023, 9, 1),
            configuration={"H": 0.7, "N": 2000},
            total_trials=20000,
            total_rejections=1000,
            observed_error_rate=0.05,
            expected_error_rate=0.05,
            regression_slope=0.02
        )
        
        data_dict = original.to_dict()
        restored = ErrorRateSummary.from_dict(data_dict)
        
        assert restored.summary_id == original.summary_id
        assert restored.regression_slope == 0.02
        assert restored.configuration["N"] == 2000