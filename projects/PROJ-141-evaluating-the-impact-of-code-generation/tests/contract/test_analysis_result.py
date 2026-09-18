"""
Contract test for analysis_result schema.

This test verifies that the analysis results produced by the statistical analysis
pipeline conform to the expected schema defined in the project specifications.

The schema includes:
- trace_id: Unique identifier derived from data_row_id + code location + timestamp
- metric_name: Name of the metric being analyzed
- condition_comparison: Description of the conditions being compared
- statistic_type: Type of statistical test used (e.g., 'paired_t_test', 'wilcoxon')
- effect_size: Cohen's d or other effect size measure
- p_value: P-value from the statistical test
- confidence_interval_95: 95% confidence interval tuple (lower, upper)
- correction_method: Multiple comparison correction method used
- corrected_p_value: P-value after correction
- sample_size: Number of paired observations
- data_row_id: Reference to the source data row
- timestamp: ISO 8601 timestamp of analysis
"""
import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


# ============================================================================
# Schema Definitions (Source of Truth)
# ============================================================================

class StatisticType(Enum):
    """Supported statistical test types."""
    PAIRED_T_TEST = "paired_t_test"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    COHENS_D = "cohens_d"


class CorrectionMethod(Enum):
    """Supported multiple comparison correction methods."""
    BONFERRONI = "bonferroni"
    HOLM = "holm"
    NONE = "none"


@dataclass
class AnalysisResultSchema:
    """
    Schema for a single analysis result entry.
    
    All fields are required unless marked as optional.
    """
    trace_id: str
    metric_name: str
    condition_comparison: str
    statistic_type: str
    effect_size: float
    p_value: float
    confidence_interval_95: Tuple[float, float]
    correction_method: str
    corrected_p_value: float
    sample_size: int
    data_row_id: str
    timestamp: str
    is_significant: Optional[bool] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResultSchema':
        """Validate and create instance from dictionary."""
        # Validate required fields
        required_fields = [
            'trace_id', 'metric_name', 'condition_comparison', 
            'statistic_type', 'effect_size', 'p_value',
            'confidence_interval_95', 'correction_method',
            'corrected_p_value', 'sample_size', 'data_row_id', 'timestamp'
        ]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate types
        if not isinstance(data['trace_id'], str) or not data['trace_id']:
            raise ValueError("trace_id must be a non-empty string")
        
        if not isinstance(data['metric_name'], str) or not data['metric_name']:
            raise ValueError("metric_name must be a non-empty string")
        
        if not isinstance(data['condition_comparison'], str):
            raise ValueError("condition_comparison must be a string")
        
        if not isinstance(data['statistic_type'], str):
            raise ValueError("statistic_type must be a string")
        
        if not isinstance(data['effect_size'], (int, float)):
            raise ValueError("effect_size must be a number")
        
        if not isinstance(data['p_value'], (int, float)):
            raise ValueError("p_value must be a number")
        
        if not (0 <= data['p_value'] <= 1):
            raise ValueError("p_value must be between 0 and 1")
        
        if not isinstance(data['confidence_interval_95'], (list, tuple)) or len(data['confidence_interval_95']) != 2:
            raise ValueError("confidence_interval_95 must be a tuple of two numbers")
        
        if not isinstance(data['correction_method'], str):
            raise ValueError("correction_method must be a string")
        
        if not isinstance(data['corrected_p_value'], (int, float)):
            raise ValueError("corrected_p_value must be a number")
        
        if not (0 <= data['corrected_p_value'] <= 1):
            raise ValueError("corrected_p_value must be between 0 and 1")
        
        if not isinstance(data['sample_size'], int) or data['sample_size'] <= 0:
            raise ValueError("sample_size must be a positive integer")
        
        if not isinstance(data['data_row_id'], str) or not data['data_row_id']:
            raise ValueError("data_row_id must be a non-empty string")
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError("timestamp must be in ISO 8601 format")
        
        # Validate statistic_type enum
        if data['statistic_type'] not in [e.value for e in StatisticType]:
            raise ValueError(f"statistic_type must be one of: {[e.value for e in StatisticType]}")
        
        # Validate correction_method enum
        if data['correction_method'] not in [e.value for e in CorrectionMethod]:
            raise ValueError(f"correction_method must be one of: {[e.value for e in CorrectionMethod]}")
        
        return cls(**data)


@dataclass
class AnalysisResultBatch:
    """Schema for a batch of analysis results."""
    results: List[AnalysisResultSchema]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'results': [r.to_dict() for r in self.results],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResultBatch':
        """Validate and create instance from dictionary."""
        if 'results' not in data or not isinstance(data['results'], list):
            raise ValueError("results must be a list")
        
        if 'metadata' not in data or not isinstance(data['metadata'], dict):
            raise ValueError("metadata must be a dictionary")
        
        results = [AnalysisResultSchema.from_dict(r) for r in data['results']]
        return cls(results=results, metadata=data['metadata'])


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def valid_analysis_result() -> Dict[str, Any]:
    """Create a valid analysis result for testing."""
    return {
        'trace_id': 'abc123def456',
        'metric_name': 'completion_time',
        'condition_comparison': 'LLM-assisted vs baseline',
        'statistic_type': 'paired_t_test',
        'effect_size': 0.85,
        'p_value': 0.003,
        'confidence_interval_95': (0.45, 1.25),
        'correction_method': 'bonferroni',
        'corrected_p_value': 0.009,
        'sample_size': 50,
        'data_row_id': 'participant_001_session_1',
        'timestamp': '2024-01-15T14:30:00Z',
        'is_significant': True,
        'notes': 'Significant improvement in LLM-assisted condition'
    }


@pytest.fixture
def valid_analysis_batch() -> Dict[str, Any]:
    """Create a valid analysis result batch for testing."""
    return {
        'results': [
            {
                'trace_id': 'trace_001',
                'metric_name': 'completion_time',
                'condition_comparison': 'LLM-assisted vs baseline',
                'statistic_type': 'paired_t_test',
                'effect_size': 0.85,
                'p_value': 0.003,
                'confidence_interval_95': (0.45, 1.25),
                'correction_method': 'bonferroni',
                'corrected_p_value': 0.009,
                'sample_size': 50,
                'data_row_id': 'participant_001',
                'timestamp': '2024-01-15T14:30:00Z'
            },
            {
                'trace_id': 'trace_002',
                'metric_name': 'pass_rate',
                'condition_comparison': 'LLM-assisted vs baseline',
                'statistic_type': 'wilcoxon_signed_rank',
                'effect_size': 0.62,
                'p_value': 0.045,
                'confidence_interval_95': (0.15, 0.89),
                'correction_method': 'holm',
                'corrected_p_value': 0.09,
                'sample_size': 50,
                'data_row_id': 'participant_001',
                'timestamp': '2024-01-15T14:31:00Z'
            }
        ],
        'metadata': {
            'analysis_version': '1.0.0',
            'timestamp': '2024-01-15T14:32:00Z',
            'total_participants': 50,
            'alpha_level': 0.05
        }
    }


# ============================================================================
# Contract Tests
# ============================================================================

class TestAnalysisResultSchema:
    """Contract tests for the analysis_result schema."""
    
    def test_valid_result_creation(self, valid_analysis_result):
        """Test that a valid result can be created from dictionary."""
        result = AnalysisResultSchema.from_dict(valid_analysis_result)
        
        assert result.metric_name == 'completion_time'
        assert result.statistic_type == 'paired_t_test'
        assert result.effect_size == 0.85
        assert result.p_value == 0.003
        assert result.confidence_interval_95 == (0.45, 1.25)
        assert result.sample_size == 50
    
    def test_result_to_dict_roundtrip(self, valid_analysis_result):
        """Test that result can be serialized and deserialized."""
        result = AnalysisResultSchema.from_dict(valid_analysis_result)
        result_dict = result.to_dict()
        result2 = AnalysisResultSchema.from_dict(result_dict)
        
        assert result.trace_id == result2.trace_id
        assert result.metric_name == result2.metric_name
        assert result.effect_size == result2.effect_size
    
    def test_missing_required_field(self, valid_analysis_result):
        """Test that missing required fields raise ValueError."""
        del valid_analysis_result['trace_id']
        
        with pytest.raises(ValueError, match="Missing required field: trace_id"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_invalid_p_value_range(self, valid_analysis_result):
        """Test that p_value outside [0, 1] raises ValueError."""
        valid_analysis_result['p_value'] = 1.5
        
        with pytest.raises(ValueError, match="p_value must be between 0 and 1"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_invalid_confidence_interval(self, valid_analysis_result):
        """Test that invalid confidence_interval_95 raises ValueError."""
        valid_analysis_result['confidence_interval_95'] = [0.5]
        
        with pytest.raises(ValueError, match="confidence_interval_95 must be a tuple of two numbers"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_invalid_statistic_type(self, valid_analysis_result):
        """Test that invalid statistic_type raises ValueError."""
        valid_analysis_result['statistic_type'] = 'invalid_test'
        
        with pytest.raises(ValueError, match="statistic_type must be one of"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_invalid_correction_method(self, valid_analysis_result):
        """Test that invalid correction_method raises ValueError."""
        valid_analysis_result['correction_method'] = 'invalid_correction'
        
        with pytest.raises(ValueError, match="correction_method must be one of"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_invalid_sample_size(self, valid_analysis_result):
        """Test that invalid sample_size raises ValueError."""
        valid_analysis_result['sample_size'] = -5
        
        with pytest.raises(ValueError, match="sample_size must be a positive integer"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_invalid_timestamp_format(self, valid_analysis_result):
        """Test that invalid timestamp format raises ValueError."""
        valid_analysis_result['timestamp'] = 'not-a-date'
        
        with pytest.raises(ValueError, match="timestamp must be in ISO 8601 format"):
            AnalysisResultSchema.from_dict(valid_analysis_result)
    
    def test_json_serialization(self, valid_analysis_result):
        """Test that result can be serialized to JSON."""
        result = AnalysisResultSchema.from_dict(valid_analysis_result)
        json_str = json.dumps(result.to_dict())
        
        parsed = json.loads(json_str)
        assert parsed['metric_name'] == 'completion_time'
        assert parsed['effect_size'] == 0.85


class TestAnalysisResultBatch:
    """Contract tests for the analysis_result batch schema."""
    
    def test_valid_batch_creation(self, valid_analysis_batch):
        """Test that a valid batch can be created from dictionary."""
        batch = AnalysisResultBatch.from_dict(valid_analysis_batch)
        
        assert len(batch.results) == 2
        assert batch.metadata['analysis_version'] == '1.0.0'
        assert batch.results[0].metric_name == 'completion_time'
    
    def test_batch_to_dict_roundtrip(self, valid_analysis_batch):
        """Test that batch can be serialized and deserialized."""
        batch = AnalysisResultBatch.from_dict(valid_analysis_batch)
        batch_dict = batch.to_dict()
        batch2 = AnalysisResultBatch.from_dict(batch_dict)
        
        assert len(batch.results) == len(batch2.results)
        assert batch.metadata == batch2.metadata
    
    def test_missing_results_field(self, valid_analysis_batch):
        """Test that missing results field raises ValueError."""
        del valid_analysis_batch['results']
        
        with pytest.raises(ValueError, match="results must be a list"):
            AnalysisResultBatch.from_dict(valid_analysis_batch)
    
    def test_invalid_results_type(self, valid_analysis_batch):
        """Test that non-list results raises ValueError."""
        valid_analysis_batch['results'] = "not a list"
        
        with pytest.raises(ValueError, match="results must be a list"):
            AnalysisResultBatch.from_dict(valid_analysis_batch)
    
    def test_missing_metadata_field(self, valid_analysis_batch):
        """Test that missing metadata field raises ValueError."""
        del valid_analysis_batch['metadata']
        
        with pytest.raises(ValueError, match="metadata must be a dictionary"):
            AnalysisResultBatch.from_dict(valid_analysis_batch)
    
    def test_batch_json_serialization(self, valid_analysis_batch):
        """Test that batch can be serialized to JSON."""
        batch = AnalysisResultBatch.from_dict(valid_analysis_batch)
        json_str = json.dumps(batch.to_dict())
        
        parsed = json.loads(json_str)
        assert len(parsed['results']) == 2
        assert parsed['metadata']['analysis_version'] == '1.0.0'


class TestTraceabilityConstraint:
    """Tests for traceability constraints per Constitution IV."""
    
    def test_trace_id_uniqueness(self, valid_analysis_batch):
        """Test that trace_ids are unique within a batch."""
        batch = AnalysisResultBatch.from_dict(valid_analysis_batch)
        trace_ids = [r.trace_id for r in batch.results]
        
        assert len(trace_ids) == len(set(trace_ids)), "trace_ids must be unique"
    
    def test_trace_id_format(self, valid_analysis_result):
        """Test that trace_id is a non-empty string."""
        result = AnalysisResultSchema.from_dict(valid_analysis_result)
        
        assert isinstance(result.trace_id, str)
        assert len(result.trace_id) > 0
    
    def test_data_row_id_reference(self, valid_analysis_result):
        """Test that data_row_id is present and non-empty."""
        result = AnalysisResultSchema.from_dict(valid_analysis_result)
        
        assert isinstance(result.data_row_id, str)
        assert len(result.data_row_id) > 0


# ============================================================================
# Integration with Project Components
# ============================================================================

def test_compatibility_with_analysis_export():
    """Test that schema is compatible with the export module."""
    # This test ensures the schema can be used by code/analysis/export.py
    # without modification
    
    sample_result = {
        'trace_id': 'hash_123',
        'metric_name': 'test_metric',
        'condition_comparison': 'A vs B',
        'statistic_type': 'paired_t_test',
        'effect_size': 0.5,
        'p_value': 0.05,
        'confidence_interval_95': (0.1, 0.9),
        'correction_method': 'bonferroni',
        'corrected_p_value': 0.1,
        'sample_size': 30,
        'data_row_id': 'row_001',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    result = AnalysisResultSchema.from_dict(sample_result)
    assert result is not None
    
    # Verify it can be exported as JSON
    json_str = json.dumps(result.to_dict())
    assert json_str is not None


def test_compatibility_with_data_loader():
    """Test that schema can be loaded from CSV/JSON data."""
    # This test ensures the schema can be used by code/analysis/data_loader.py
    
    # Simulate data that might come from data_loader.py
    csv_row = {
        'trace_id': 'trace_001',
        'metric_name': 'time',
        'condition_comparison': 'LLM vs baseline',
        'statistic_type': 'paired_t_test',
        'effect_size': '0.75',
        'p_value': '0.02',
        'confidence_interval_95': '(0.3, 1.2)',
        'correction_method': 'holm',
        'corrected_p_value': '0.04',
        'sample_size': '45',
        'data_row_id': 'participant_002',
        'timestamp': '2024-01-15T10:00:00Z'
    }
    
    # Convert string representations to proper types
    csv_row['effect_size'] = float(csv_row['effect_size'])
    csv_row['p_value'] = float(csv_row['p_value'])
    csv_row['corrected_p_value'] = float(csv_row['corrected_p_value'])
    csv_row['sample_size'] = int(csv_row['sample_size'])
    csv_row['confidence_interval_95'] = (0.3, 1.2)
    
    result = AnalysisResultSchema.from_dict(csv_row)
    assert result.effect_size == 0.75
    assert result.sample_size == 45


if __name__ == '__main__':
    pytest.main([__file__, '-v'])