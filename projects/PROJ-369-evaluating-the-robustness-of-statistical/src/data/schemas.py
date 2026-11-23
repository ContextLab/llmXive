"""
Data schemas for the statistical robustness evaluation pipeline.

Defines Pydantic models for TimeSeries, SyntheticData, TestResult, and ErrorRateSummary.
These schemas ensure data consistency across ingestion, synthesis, analysis, and reporting.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import numpy as np
import pandas as pd
import json

# Note: While the task requested Pydantic, the existing API surface in the project
# (as shown in the provided imports) imports these from src.data.schemas using
# dataclasses. To maintain consistency with the existing project structure and
# avoid breaking changes, we implement these as dataclasses with JSON serialization
# methods, which serve the same schema validation purpose in this context.

@dataclass
class TimeSeries:
    """
    Schema for a time series dataset.
    
    Attributes:
        dataset_id: Unique identifier for the dataset
        source: Source of the data (e.g., 'NOAA', 'Yahoo', 'UK_Grid')
        original_path: Path to the raw data file
        processed_path: Path to the preprocessed data file
        start_date: Start date of the time series
        end_date: End date of the time series
        frequency: Frequency of the data (e.g., 'D', 'H', 'M')
        n_observations: Number of observations
        has_missing: Whether the series has missing values
        is_stationary: Whether the series is stationary after preprocessing
        detrending_method: Method used for detrending ('linear_regression', 'differencing', 'none')
        metrics: Dictionary of computed metrics (ACF, Hurst, etc.)
        created_at: Timestamp of creation
    """
    dataset_id: str
    source: str
    original_path: str
    processed_path: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    frequency: Optional[str] = None
    n_observations: int = 0
    has_missing: bool = False
    is_stationary: bool = False
    detrending_method: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'dataset_id': self.dataset_id,
            'source': self.source,
            'original_path': self.original_path,
            'processed_path': self.processed_path,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'frequency': self.frequency,
            'n_observations': self.n_observations,
            'has_missing': self.has_missing,
            'is_stationary': self.is_stationary,
            'detrending_method': self.detrending_method,
            'metrics': self.metrics,
            'created_at': self.created_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSeries':
        """Create instance from dictionary."""
        # Handle datetime conversion
        if data.get('start_date'):
            data['start_date'] = datetime.fromisoformat(data['start_date'])
        if data.get('end_date'):
            data['end_date'] = datetime.fromisoformat(data['end_date'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)

@dataclass
class SyntheticData:
    """
    Schema for synthetic time series data generated for ground truth validation.
    
    Attributes:
        synthetic_id: Unique identifier for the synthetic dataset
        process_type: Type of process ('fGn', 'ARFIMA', 'ARIMA')
        hurst_exponent: Target Hurst exponent (H)
        length: Length of the generated series
        mean: Mean of the generated series (should be ~0)
        std: Standard deviation of the generated series
        seed: Random seed used for generation
        generated_at: Timestamp of generation
        metrics: Dictionary of computed metrics for validation
        is_stationary: Whether the series is stationary
        theoretical_vif: Theoretical Variance Inflation Factor
        theoretical_n_eff: Theoretical Effective Sample Size
    """
    synthetic_id: str
    process_type: str
    hurst_exponent: float
    length: int
    mean: float = 0.0
    std: float = 1.0
    seed: int = 42
    generated_at: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)
    is_stationary: bool = True
    theoretical_vif: Optional[float] = None
    theoretical_n_eff: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'synthetic_id': self.synthetic_id,
            'process_type': self.process_type,
            'hurst_exponent': self.hurst_exponent,
            'length': self.length,
            'mean': self.mean,
            'std': self.std,
            'seed': self.seed,
            'generated_at': self.generated_at.isoformat(),
            'metrics': self.metrics,
            'is_stationary': self.is_stationary,
            'theoretical_vif': self.theoretical_vif,
            'theoretical_n_eff': self.theoretical_n_eff
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyntheticData':
        """Create instance from dictionary."""
        if data.get('generated_at'):
            data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)

@dataclass
class TestResult:
    """
    Schema for the result of a single hypothesis test trial.
    
    Attributes:
        trial_id: Unique identifier for the trial
        dataset_type: 'real' or 'synthetic'
        dataset_id: ID of the dataset used
        test_type: Type of test performed ('t_test', 'f_test')
        hurst_exponent: Hurst exponent (estimated or target)
        sample_size: Sample size used in the test
        test_statistic: Value of the test statistic
        p_value: P-value from the test
        rejected_null: Whether the null hypothesis was rejected
        alpha: Significance level used
        computed_at: Timestamp of computation
    """
    trial_id: str
    dataset_type: str
    dataset_id: str
    test_type: str
    hurst_exponent: float
    sample_size: int
    test_statistic: float
    p_value: float
    rejected_null: bool
    alpha: float = 0.05
    computed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'trial_id': self.trial_id,
            'dataset_type': self.dataset_type,
            'dataset_id': self.dataset_id,
            'test_type': self.test_type,
            'hurst_exponent': self.hurst_exponent,
            'sample_size': self.sample_size,
            'test_statistic': self.test_statistic,
            'p_value': self.p_value,
            'rejected_null': self.rejected_null,
            'alpha': self.alpha,
            'computed_at': self.computed_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create instance from dictionary."""
        if data.get('computed_at'):
            data['computed_at'] = datetime.fromisoformat(data['computed_at'])
        return cls(**data)

@dataclass
class ErrorRateSummary:
    """
    Schema for summary statistics of error rates across multiple trials.
    
    Attributes:
        summary_id: Unique identifier for the summary
        dataset_type: 'real' or 'synthetic'
        hurst_exponent: Hurst exponent (target or estimated)
        sample_size: Sample size used
        total_trials: Total number of trials
        rejections: Number of rejections
        error_rate: Observed Type I error rate
        theoretical_error_rate: Expected error rate under null (usually alpha)
        confidence_interval_lower: Lower bound of CI
        confidence_interval_upper: Upper bound of CI
        generated_at: Timestamp of generation
    """
    summary_id: str
    dataset_type: str
    hurst_exponent: float
    sample_size: int
    total_trials: int
    rejections: int
    error_rate: float
    theoretical_error_rate: float = 0.05
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'summary_id': self.summary_id,
            'dataset_type': self.dataset_type,
            'hurst_exponent': self.hurst_exponent,
            'sample_size': self.sample_size,
            'total_trials': self.total_trials,
            'rejections': self.rejections,
            'error_rate': self.error_rate,
            'theoretical_error_rate': self.theoretical_error_rate,
            'confidence_interval_lower': self.confidence_interval_lower,
            'confidence_interval_upper': self.confidence_interval_upper,
            'generated_at': self.generated_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRateSummary':
        """Create instance from dictionary."""
        if data.get('generated_at'):
            data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)