"""
Contract tests for the Semantic Divergence Diagnostic output schemas.

This module defines expected data structures for the correlation analysis
between semantic divergence scores and simulated RL failure rates.
"""
import pytest
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class ExpectedCorrelationResult:
    """
    Expected schema for a single correlation result between divergence and failure.
    
    Attributes:
        problem_id: Unique identifier for the problem instance
        divergence_score: Calculated semantic divergence score (float)
        failure_rate: Simulated RL failure rate from AXPO (float, 0.0-1.0)
        correlation_coefficient: Pearson correlation coefficient (float)
        p_value: Statistical significance p-value (float)
        is_significant: Boolean flag indicating if p < 0.05
        problem_type: Optional type/category of the problem
    """
    problem_id: str
    divergence_score: float
    failure_rate: float
    correlation_coefficient: float
    p_value: float
    is_significant: bool
    problem_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        """
        Validate that a dictionary matches the expected schema.
        
        Args:
            data: Dictionary to validate
            
        Raises:
            ValueError: If any required field is missing or has wrong type
        """
        required_fields = {
            'problem_id': str,
            'divergence_score': (int, float),
            'failure_rate': (int, float),
            'correlation_coefficient': (int, float),
            'p_value': (int, float),
            'is_significant': bool,
            'problem_type': (str, type(None))
        }
        
        for field_name, expected_type in required_fields.items():
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
            
            if not isinstance(data[field_name], expected_type):
                raise ValueError(
                    f"Field '{field_name}' has wrong type. "
                    f"Expected {expected_type}, got {type(data[field_name])}"
                )
        
        # Additional range validation
        if not (0.0 <= data['failure_rate'] <= 1.0):
            raise ValueError(f"failure_rate must be between 0 and 1, got {data['failure_rate']}")
        
        if not (-1.0 <= data['correlation_coefficient'] <= 1.0):
            raise ValueError(
                f"correlation_coefficient must be between -1 and 1, "
                f"got {data['correlation_coefficient']}"
            )
        
        if not (0.0 <= data['p_value'] <= 1.0):
            raise ValueError(f"p_value must be between 0 and 1, got {data['p_value']}")


@dataclass
class ExpectedBatchCorrelationReport:
    """
    Expected schema for the full batch correlation analysis report.
    
    Attributes:
        report_id: Unique identifier for this report
        timestamp: ISO format timestamp of report generation
        total_samples: Total number of samples analyzed
        significant_count: Number of samples with significant correlation
        mean_divergence: Mean divergence score across all samples
        mean_failure_rate: Mean failure rate across all samples
        overall_correlation: Overall Pearson correlation coefficient
        overall_p_value: Overall p-value for the correlation
        results: List of individual correlation results
        metadata: Additional metadata about the analysis
    """
    report_id: str
    timestamp: str
    total_samples: int
    significant_count: int
    mean_divergence: float
    mean_failure_rate: float
    overall_correlation: float
    overall_p_value: float
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        """
        Validate that a dictionary matches the expected batch report schema.
        
        Args:
            data: Dictionary to validate
            
        Raises:
            ValueError: If any required field is missing or has wrong type
        """
        required_fields = {
            'report_id': str,
            'timestamp': str,
            'total_samples': int,
            'significant_count': int,
            'mean_divergence': (int, float),
            'mean_failure_rate': (int, float),
            'overall_correlation': (int, float),
            'overall_p_value': (int, float),
            'results': list,
            'metadata': dict
        }
        
        for field_name, expected_type in required_fields.items():
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
            
            if not isinstance(data[field_name], expected_type):
                raise ValueError(
                    f"Field '{field_name}' has wrong type. "
                    f"Expected {expected_type}, got {type(data[field_name])}"
                )
        
        # Validate individual results
        for i, result in enumerate(data['results']):
            try:
                ExpectedCorrelationResult.validate(result)
            except ValueError as e:
                raise ValueError(f"Invalid result at index {i}: {e}")
        
        # Cross-field validation
        if data['total_samples'] != len(data['results']):
            raise ValueError(
                f"total_samples ({data['total_samples']}) does not match "
                f"number of results ({len(data['results'])})"
            )
        
        if data['significant_count'] > data['total_samples']:
            raise ValueError(
                f"significant_count ({data['significant_count']}) cannot exceed "
                f"total_samples ({data['total_samples']})"
            )


class TestCorrelationSchema:
    """Contract test class for correlation output schema validation."""
    
    @pytest.fixture
    def valid_single_result(self) -> Dict[str, Any]:
        """Fixture providing a valid single correlation result."""
        return {
            'problem_id': 'mathvista_001',
            'divergence_score': 0.75,
            'failure_rate': 0.42,
            'correlation_coefficient': -0.68,
            'p_value': 0.03,
            'is_significant': True,
            'problem_type': 'math'
        }
    
    @pytest.fixture
    def valid_batch_report(self, valid_single_result) -> Dict[str, Any]:
        """Fixture providing a valid batch correlation report."""
        return {
            'report_id': 'corr_report_20240101',
            'timestamp': datetime.now().isoformat(),
            'total_samples': 2,
            'significant_count': 1,
            'mean_divergence': 0.72,
            'mean_failure_rate': 0.38,
            'overall_correlation': -0.65,
            'overall_p_value': 0.04,
            'results': [valid_single_result, {
                'problem_id': 'scienceqa_002',
                'divergence_score': 0.69,
                'failure_rate': 0.35,
                'correlation_coefficient': -0.62,
                'p_value': 0.06,
                'is_significant': False,
                'problem_type': 'science'
            }],
            'metadata': {
                'method': 'pearson',
                'alpha': 0.05,
                'simulator_version': '1.0'
            }
        }
    
    def test_valid_single_result_schema(self, valid_single_result):
        """Test that a valid single result passes schema validation."""
        ExpectedCorrelationResult.validate(valid_single_result)
    
    def test_invalid_single_result_missing_field(self):
        """Test that missing required fields raise ValueError."""
        invalid_result = {
            'problem_id': 'test_001',
            'divergence_score': 0.75
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            ExpectedCorrelationResult.validate(invalid_result)
    
    def test_invalid_single_result_wrong_type(self):
        """Test that wrong field types raise ValueError."""
        invalid_result = {
            'problem_id': 123,  # Should be str
            'divergence_score': 0.75,
            'failure_rate': 0.42,
            'correlation_coefficient': -0.68,
            'p_value': 0.03,
            'is_significant': True,
            'problem_type': 'math'
        }
        
        with pytest.raises(ValueError, match="wrong type"):
            ExpectedCorrelationResult.validate(invalid_result)
    
    def test_invalid_single_result_range_failure_rate(self):
        """Test that out-of-range failure_rate raises ValueError."""
        invalid_result = {
            'problem_id': 'test_001',
            'divergence_score': 0.75,
            'failure_rate': 1.5,  # Out of range
            'correlation_coefficient': -0.68,
            'p_value': 0.03,
            'is_significant': True,
            'problem_type': 'math'
        }
        
        with pytest.raises(ValueError, match="failure_rate must be between"):
            ExpectedCorrelationResult.validate(invalid_result)
    
    def test_valid_batch_report_schema(self, valid_batch_report):
        """Test that a valid batch report passes schema validation."""
        ExpectedBatchCorrelationReport.validate(valid_batch_report)
    
    def test_invalid_batch_report_missing_field(self):
        """Test that missing required fields in batch report raise ValueError."""
        invalid_report = {
            'report_id': 'test_report',
            'timestamp': '2024-01-01T00:00:00'
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            ExpectedBatchCorrelationReport.validate(invalid_report)
    
    def test_invalid_batch_report_mismatched_counts(self, valid_single_result):
        """Test that mismatched total_samples and results length raises ValueError."""
        invalid_report = {
            'report_id': 'test_report',
            'timestamp': '2024-01-01T00:00:00',
            'total_samples': 10,  # Doesn't match 1 result
            'significant_count': 1,
            'mean_divergence': 0.75,
            'mean_failure_rate': 0.42,
            'overall_correlation': -0.68,
            'overall_p_value': 0.03,
            'results': [valid_single_result],
            'metadata': {}
        }
        
        with pytest.raises(ValueError, match="total_samples.*does not match"):
            ExpectedBatchCorrelationReport.validate(invalid_report)
    
    def test_invalid_batch_report_significant_count_exceeds_total(self, valid_single_result):
        """Test that significant_count > total_samples raises ValueError."""
        invalid_report = {
            'report_id': 'test_report',
            'timestamp': '2024-01-01T00:00:00',
            'total_samples': 1,
            'significant_count': 5,  # Exceeds total
            'mean_divergence': 0.75,
            'mean_failure_rate': 0.42,
            'overall_correlation': -0.68,
            'overall_p_value': 0.03,
            'results': [valid_single_result],
            'metadata': {}
        }
        
        with pytest.raises(ValueError, match="significant_count.*cannot exceed"):
            ExpectedBatchCorrelationReport.validate(invalid_report)
    
    def test_dataclass_to_dict_conversion(self, valid_single_result, valid_batch_report):
        """Test that dataclasses can be converted to dictionaries correctly."""
        single_obj = ExpectedCorrelationResult(**valid_single_result)
        assert single_obj.to_dict() == valid_single_result
        
        batch_obj = ExpectedBatchCorrelationReport(**valid_batch_report)
        assert batch_obj.to_dict() == valid_batch_report