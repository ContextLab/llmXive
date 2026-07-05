"""
Unit tests for data models (EEGSegment and ComplexityMetric).
"""

import pytest
from datetime import datetime
from code.models import EEGSegment, ComplexityMetric
from code.models.complexity_metric import MetricType


class TestEEGSegment:
    """Tests for the EEGSegment data model."""
    
    def test_create_eeg_segment(self):
        """Test creating a basic EEGSegment."""
        segment = EEGSegment(
            segment_id='seg_001',
            participant_id='p_001',
            channel_count=19,
            sample_rate=256.0,
            duration_seconds=120.0
        )
        
        assert segment.segment_id == 'seg_001'
        assert segment.participant_id == 'p_001'
        assert segment.channel_count == 19
        assert segment.sample_rate == 256.0
        assert segment.duration_seconds == 120.0
        assert segment.preprocessed is False
        assert segment.artifact_rejected is False
        assert len(segment.rejection_reasons) == 0
    
    def test_eeg_segment_to_dict(self):
        """Test converting EEGSegment to dictionary."""
        segment = EEGSegment(
            segment_id='seg_001',
            participant_id='p_001',
            recording_date=datetime(2024, 1, 15, 10, 30),
            channel_count=19,
            sample_rate=256.0,
            duration_seconds=120.0,
            preprocessed=True,
            artifact_rejected=True,
            rejection_reasons=['high_amplitude', 'line_noise'],
            metadata={'source': 'Sleep-EDF', 'quality': 'good'}
        )
        
        data = segment.to_dict()
        
        assert data['segment_id'] == 'seg_001'
        assert data['participant_id'] == 'p_001'
        assert data['channel_count'] == 19
        assert data['preprocessed'] is True
        assert data['artifact_rejected'] is True
        assert 'high_amplitude' in data['rejection_reasons']
        assert data['metadata']['source'] == 'Sleep-EDF'
    
    def test_eeg_segment_from_dict(self):
        """Test creating EEGSegment from dictionary."""
        data = {
            'segment_id': 'seg_002',
            'participant_id': 'p_002',
            'recording_date': '2024-02-20T14:00:00',
            'channel_count': 21,
            'sample_rate': 512.0,
            'duration_seconds': 180.0,
            'preprocessed': False,
            'artifact_rejected': False,
            'rejection_reasons': [],
            'metadata': {'source': 'SHHS'}
        }
        
        segment = EEGSegment.from_dict(data)
        
        assert segment.segment_id == 'seg_002'
        assert segment.participant_id == 'p_002'
        assert segment.channel_count == 21
        assert segment.sample_rate == 512.0
        assert segment.duration_seconds == 180.0
        assert segment.recording_date == datetime(2024, 2, 20, 14, 0)
    
    def test_eeg_segment_validation(self):
        """Test EEGSegment validation."""
        # Valid segment
        valid_segment = EEGSegment(
            segment_id='seg_001',
            participant_id='p_001',
            channel_count=19,
            sample_rate=256.0,
            duration_seconds=120.0
        )
        assert valid_segment.validate() is True
        
        # Invalid segment - missing segment_id
        invalid_segment = EEGSegment(
            segment_id='',
            participant_id='p_001',
            channel_count=19,
            sample_rate=256.0,
            duration_seconds=120.0
        )
        assert invalid_segment.validate() is False
        
        # Invalid segment - zero channels
        invalid_segment = EEGSegment(
            segment_id='seg_001',
            participant_id='p_001',
            channel_count=0,
            sample_rate=256.0,
            duration_seconds=120.0
        )
        assert invalid_segment.validate() is False
        
        # Invalid segment - negative sample rate
        invalid_segment = EEGSegment(
            segment_id='seg_001',
            participant_id='p_001',
            channel_count=19,
            sample_rate=-1.0,
            duration_seconds=120.0
        )
        assert invalid_segment.validate() is False
    
    def test_eeg_segment_rejection(self):
        """Test artifact rejection tracking."""
        segment = EEGSegment(
            segment_id='seg_001',
            participant_id='p_001',
            channel_count=19,
            sample_rate=256.0,
            duration_seconds=120.0
        )
        
        # Initially not rejected
        assert segment.artifact_rejected is False
        assert len(segment.rejection_reasons) == 0
        
        # Add rejection reason
        segment.artifact_rejected = True
        segment.rejection_reasons.append('high_amplitude')
        segment.rejection_reasons.append('muscle_artifact')
        
        assert segment.artifact_rejected is True
        assert len(segment.rejection_reasons) == 2


class TestComplexityMetric:
    """Tests for the ComplexityMetric data model."""
    
    def test_create_complexity_metric(self):
        """Test creating a basic ComplexityMetric."""
        metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65,
            parameters={'threshold': 0.5, 'window_size': 10}
        )
        
        assert metric.metric_id == 'm_001'
        assert metric.segment_id == 'seg_001'
        assert metric.channel == 'Fz'
        assert metric.metric_type == MetricType.LEMPEL_ZIV_COMPLEXITY
        assert metric.value == 0.65
        assert metric.parameters['threshold'] == 0.5
    
    def test_complexity_metric_to_dict(self):
        """Test converting ComplexityMetric to dictionary."""
        metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Cz',
            metric_type=MetricType.PERMUTATION_ENTROPY,
            value=3.25,
            parameters={'order': 3, 'delay': 1},
            quality_score=0.92,
            metadata={'algorithm': 'standard'}
        )
        
        data = metric.to_dict()
        
        assert data['metric_id'] == 'm_001'
        assert data['segment_id'] == 'seg_001'
        assert data['channel'] == 'Cz'
        assert data['metric_type'] == 'pe'
        assert data['value'] == 3.25
        assert data['quality_score'] == 0.92
        assert data['metadata']['algorithm'] == 'standard'
    
    def test_complexity_metric_from_dict(self):
        """Test creating ComplexityMetric from dictionary."""
        data = {
            'metric_id': 'm_002',
            'segment_id': 'seg_002',
            'channel': 'Pz',
            'metric_type': 'lzc',
            'value': 0.72,
            'parameters': {'threshold': 0.5},
            'timestamp': '2024-03-15T09:30:00',
            'quality_score': 0.88,
            'metadata': {'source': 'preprocessing_v2'}
        }
        
        metric = ComplexityMetric.from_dict(data)
        
        assert metric.metric_id == 'm_002'
        assert metric.segment_id == 'seg_002'
        assert metric.channel == 'Pz'
        assert metric.metric_type == MetricType.LEMPEL_ZIV_COMPLEXITY
        assert metric.value == 0.72
        assert metric.quality_score == 0.88
        assert metric.metadata['source'] == 'preprocessing_v2'
    
    def test_complexity_metric_validation(self):
        """Test ComplexityMetric validation."""
        # Valid metric
        valid_metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65,
            parameters={}
        )
        assert valid_metric.validate() is True
        
        # Invalid metric - missing metric_id
        invalid_metric = ComplexityMetric(
            metric_id='',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65,
            parameters={}
        )
        assert invalid_metric.validate() is False
        
        # Invalid metric - quality_score out of range
        invalid_metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65,
            parameters={},
            quality_score=1.5
        )
        assert invalid_metric.validate() is False
    
    def test_complexity_metric_string_representation(self):
        """Test string representation of ComplexityMetric."""
        metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65432,
            parameters={}
        )
        
        str_repr = str(metric)
        assert 'LZC' in str_repr
        assert 'Fz' in str_repr
        assert '0.6543' in str_repr
    
    def test_metric_type_enum(self):
        """Test MetricType enum values."""
        assert MetricType.LEMPEL_ZIV_COMPLEXITY.value == 'lzc'
        assert MetricType.PERMUTATION_ENTROPY.value == 'pe'
        assert MetricType.SAMPLE_ENTROPY.value == 'sampen'
        assert MetricType.MULTISCALE_ENTROPY.value == 'mse'
    
    def test_complexity_metric_default_timestamp(self):
        """Test that timestamp defaults to current time."""
        metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65,
            parameters={}
        )
        
        assert metric.timestamp is not None
        assert isinstance(metric.timestamp, datetime)
    
    def test_complexity_metric_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        metric = ComplexityMetric(
            metric_id='m_001',
            segment_id='seg_001',
            channel='Fz',
            metric_type=MetricType.LEMPEL_ZIV_COMPLEXITY,
            value=0.65,
            parameters={}
        )
        
        assert metric.metadata == {}
        assert isinstance(metric.metadata, dict)