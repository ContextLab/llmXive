import pytest
import numpy as np
from datetime import datetime
import sys
import os

# Add parent directory to path to allow imports from code/models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.eeg_segment import EEGSegment
from models.complexity_metric import ComplexityMetric, MetricType

class TestEEGSegment:
    def test_creation_basic(self):
        """Test basic creation of EEGSegment."""
        data = np.random.rand(1000)
        segment = EEGSegment(
            participant_id="P001",
            channel="Fp1",
            data=data,
            sampling_rate=250.0
        )
        
        assert segment.participant_id == "P001"
        assert segment.channel == "Fp1"
        assert np.array_equal(segment.data, data)
        assert segment.sampling_rate == 250.0
        assert segment.duration_seconds == 4.0  # 1000 / 250

    def test_creation_with_metadata(self):
        """Test creation with metadata and start time."""
        data = np.random.rand(2000)
        start = datetime(2023, 1, 1, 10, 0, 0)
        segment = EEGSegment(
            participant_id="P002",
            channel="Cz",
            data=data,
            sampling_rate=500.0,
            start_time=start,
            duration_seconds=5.0,
            metadata={"fatigue_score": 0.8, "condition": "post"}
        )
        
        assert segment.start_time == start
        assert segment.duration_seconds == 5.0
        assert segment.metadata["fatigue_score"] == 0.8

    def test_invalid_data_type(self):
        """Test that non-numpy data raises TypeError."""
        with pytest.raises(TypeError):
            EEGSegment(
                participant_id="P003",
                channel="Fp1",
                data=[1, 2, 3],  # List instead of array
                sampling_rate=250.0
            )

    def test_invalid_dimensions(self):
        """Test that multi-dimensional data raises ValueError."""
        data_2d = np.random.rand(100, 100)
        with pytest.raises(ValueError):
            EEGSegment(
                participant_id="P004",
                channel="Fp1",
                data=data_2d,
                sampling_rate=250.0
            )

    def test_invalid_sampling_rate(self):
        """Test that non-positive sampling rate raises ValueError."""
        data = np.random.rand(100)
        with pytest.raises(ValueError):
            EEGSegment(
                participant_id="P005",
                channel="Fp1",
                data=data,
                sampling_rate=-10.0
            )

    def test_serialization_roundtrip(self):
        """Test that to_dict and from_dict preserve data."""
        data = np.random.rand(500)
        segment = EEGSegment(
            participant_id="P006",
            channel="O1",
            data=data,
            sampling_rate=250.0,
            metadata={"test": True}
        )
        
        d = segment.to_dict()
        restored = EEGSegment.from_dict(d)
        
        assert restored.participant_id == segment.participant_id
        assert restored.channel == segment.channel
        assert np.array_equal(restored.data, segment.data)
        assert restored.sampling_rate == segment.sampling_rate
        assert restored.metadata == segment.metadata

    def test_len(self):
        """Test length of segment."""
        data = np.zeros(1500)
        segment = EEGSegment(
            participant_id="P007",
            channel="Fp1",
            data=data,
            sampling_rate=500.0
        )
        assert len(segment) == 1500


class TestComplexityMetric:
    def test_creation_lzc(self):
        """Test creation of a LZC metric."""
        metric = ComplexityMetric(
            participant_id="P001",
            channel="Fp1",
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.6543,
            parameters={"normalized": True}
        )
        
        assert metric.participant_id == "P001"
        assert metric.channel == "Fp1"
        assert metric.metric_type == MetricType.LEMPEL_ZIV_COMPLEXITY
        assert metric.value == 0.6543
        assert metric.parameters["normalized"] is True

    def test_creation_pe(self):
        """Test creation of a Permutation Entropy metric."""
        metric = ComplexityMetric(
            participant_id="P002",
            channel="Cz",
            metric_type=MetricType.PERMUTATION_ENTROPY,
            value=2.312,
            parameters={"order": 3, "lag": 1}
        )
        
        assert metric.metric_type == MetricType.PERMUTATION_ENTROPY
        assert metric.value == 2.312

    def test_invalid_value_type(self):
        """Test that non-numeric value raises TypeError."""
        with pytest.raises(TypeError):
            ComplexityMetric(
                participant_id="P003",
                channel="Fp1",
                metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
                value="string_value"
            )

    def test_nan_value_rejected(self):
        """Test that NaN value raises ValueError."""
        with pytest.raises(ValueError):
            ComplexityMetric(
                participant_id="P004",
                channel="Fp1",
                metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
                value=float('nan')
            )

    def test_inf_value_rejected(self):
        """Test that Inf value raises ValueError."""
        with pytest.raises(ValueError):
            ComplexityMetric(
                participant_id="P005",
                channel="Fp1",
                metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
                value=float('inf')
            )

    def test_serialization_roundtrip(self):
        """Test that to_dict and from_dict preserve data."""
        metric = ComplexityMetric(
            participant_id="P006",
            channel="O1",
            metric_type=MetricType.SAMPLE_ENTROPY,
            value=1.2345,
            parameters={"m": 2, "r": 0.2},
            metadata={"source": "raw"}
        )
        
        d = metric.to_dict()
        restored = ComplexityMetric.from_dict(d)
        
        assert restored.participant_id == metric.participant_id
        assert restored.channel == metric.channel
        assert restored.metric_type == metric.metric_type
        assert restored.value == metric.value
        assert restored.parameters == metric.parameters
        assert restored.metadata == metric.metadata

    def test_str_representation(self):
        """Test string representation."""
        metric = ComplexityMetric(
            participant_id="P007",
            channel="Fp1",
            metric_type=MetricType.PERMUTATION_ENTROPY,
            value=2.5
        )
        s = str(metric)
        assert "PERMUTATION_ENTROPY" in s
        assert "Fp1" in s
        assert "2.5000" in s