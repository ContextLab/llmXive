"""
Data schemas for the robustness evaluation pipeline.

Defines Pydantic-like dataclasses for TimeSeries, SyntheticData, 
TestResult, and ErrorRateSummary to ensure type safety and 
consistent data exchange across the pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np
import pandas as pd


@dataclass
class TimeSeries:
    """
    Represents a single time series dataset with metadata.
    
    Attributes:
        source_name: Name of the data source (e.g., 'NOAA', 'Yahoo', 'UK_Grid')
        dataset_id: Unique identifier for this specific dataset
        timestamp: Time when the data was ingested
        frequency: Resampled frequency (e.g., 'H', 'D', 'M')
        length: Number of data points
        has_missing: Boolean indicating if missing values were detected
        is_stationary: Boolean indicating result of ADF test
        preprocessing_method: Method used to achieve stationarity ('none', 'diff', 'detrend')
        data: The actual numpy array or pandas Series of values
        metadata: Dictionary for additional source-specific info
    """
    source_name: str
    dataset_id: str
    timestamp: datetime
    frequency: str
    length: int
    has_missing: bool
    is_stationary: bool
    preprocessing_method: str
    data: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the TimeSeries object to a dictionary for JSON serialization."""
        return {
            "source_name": self.source_name,
            "dataset_id": self.dataset_id,
            "timestamp": self.timestamp.isoformat(),
            "frequency": self.frequency,
            "length": self.length,
            "has_missing": self.has_missing,
            "is_stationary": self.is_stationary,
            "preprocessing_method": self.preprocessing_method,
            "data": self.data.tolist() if self.data is not None else [],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeSeries":
        """Create a TimeSeries object from a dictionary."""
        # Handle datetime parsing
        ts_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now()
        
        # Handle data conversion
        raw_data = data.get("data", [])
        np_data = np.array(raw_data) if raw_data else np.array([])
        
        return cls(
            source_name=data["source_name"],
            dataset_id=data["dataset_id"],
            timestamp=timestamp,
            frequency=data["frequency"],
            length=data["length"],
            has_missing=data["has_missing"],
            is_stationary=data["is_stationary"],
            preprocessing_method=data["preprocessing_method"],
            data=np_data,
            metadata=data.get("metadata", {})
        )


@dataclass
class SyntheticData:
    """
    Represents a generated synthetic time series with ground truth parameters.
    
    Attributes:
        generation_id: Unique identifier for this generation run
        timestamp: Time when the data was generated
        process_type: Type of process ('fGn', 'ARFIMA')
        hurst_exponent: True Hurst exponent used for generation
        mean: True mean used for generation (should be 0)
        length: Number of data points generated
        seed: Random seed used for reproducibility
        data: The generated numpy array
        metrics: Dictionary of computed metrics (ACF, Hurst estimate, etc.)
        is_shuffled: Whether this series has been shuffled for null distribution
    """
    generation_id: str
    timestamp: datetime
    process_type: str
    hurst_exponent: float
    mean: float
    length: int
    seed: int
    data: np.ndarray
    metrics: Dict[str, float] = field(default_factory=dict)
    is_shuffled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the SyntheticData object to a dictionary."""
        return {
            "generation_id": self.generation_id,
            "timestamp": self.timestamp.isoformat(),
            "process_type": self.process_type,
            "hurst_exponent": self.hurst_exponent,
            "mean": self.mean,
            "length": self.length,
            "seed": self.seed,
            "data": self.data.tolist(),
            "metrics": self.metrics,
            "is_shuffled": self.is_shuffled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyntheticData":
        """Create a SyntheticData object from a dictionary."""
        ts_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now()
        
        raw_data = data.get("data", [])
        np_data = np.array(raw_data) if raw_data else np.array([])
        
        return cls(
            generation_id=data["generation_id"],
            timestamp=timestamp,
            process_type=data["process_type"],
            hurst_exponent=data["hurst_exponent"],
            mean=data["mean"],
            length=data["length"],
            seed=data["seed"],
            data=np_data,
            metrics=data.get("metrics", {}),
            is_shuffled=data.get("is_shuffled", False)
        )


@dataclass
class TestResult:
    """
    Represents the result of a single hypothesis test.
    
    Attributes:
        test_id: Unique identifier for this test run
        dataset_id: ID of the dataset being tested (real or synthetic)
        test_type: Type of test performed ('t_test', 'f_test')
        timestamp: Time when the test was run
        null_hypothesis: Description of the null hypothesis
        alpha: Significance level used
        statistic: Calculated test statistic value
        p_value: Calculated p-value
        rejected: Boolean indicating if null hypothesis was rejected
        true_hurst: True Hurst exponent (for synthetic) or estimated (for real)
        is_shuffled: Whether this test was run on a shuffled version
        ground_truth_label: Expected outcome (e.g., 'true_null' for H=0.5 synthetic)
    """
    test_id: str
    dataset_id: str
    test_type: str
    timestamp: datetime
    null_hypothesis: str
    alpha: float
    statistic: float
    p_value: float
    rejected: bool
    true_hurst: Optional[float] = None
    is_shuffled: bool = False
    ground_truth_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the TestResult object to a dictionary."""
        return {
            "test_id": self.test_id,
            "dataset_id": self.dataset_id,
            "test_type": self.test_type,
            "timestamp": self.timestamp.isoformat(),
            "null_hypothesis": self.null_hypothesis,
            "alpha": self.alpha,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "rejected": self.rejected,
            "true_hurst": self.true_hurst,
            "is_shuffled": self.is_shuffled,
            "ground_truth_label": self.ground_truth_label
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestResult":
        """Create a TestResult object from a dictionary."""
        ts_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now()
        
        return cls(
            test_id=data["test_id"],
            dataset_id=data["dataset_id"],
            test_type=data["test_type"],
            timestamp=timestamp,
            null_hypothesis=data["null_hypothesis"],
            alpha=data["alpha"],
            statistic=data["statistic"],
            p_value=data["p_value"],
            rejected=data["rejected"],
            true_hurst=data.get("true_hurst"),
            is_shuffled=data.get("is_shuffled", False),
            ground_truth_label=data.get("ground_truth_label")
        )


@dataclass
class ErrorRateSummary:
    """
    Summary of error rates for a specific configuration.
    
    Attributes:
        summary_id: Unique identifier for this summary
        timestamp: Time when the summary was computed
        configuration: Dictionary describing the configuration (H, N, test_type)
        total_trials: Total number of trials run
        total_rejections: Number of times null was rejected
        observed_error_rate: Calculated error rate (rejections / total)
        expected_error_rate: Expected error rate (usually 0.05)
        confidence_interval_lower: Lower bound of CI
        confidence_interval_upper: Upper bound of CI
        vif: Variance Inflation Factor if applicable
        n_eff: Effective sample size if applicable
        regression_slope: Slope from error rate vs Hurst regression if applicable
    """
    summary_id: str
    timestamp: datetime
    configuration: Dict[str, Any]
    total_trials: int
    total_rejections: int
    observed_error_rate: float
    expected_error_rate: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    vif: Optional[float] = None
    n_eff: Optional[float] = None
    regression_slope: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the ErrorRateSummary object to a dictionary."""
        return {
            "summary_id": self.summary_id,
            "timestamp": self.timestamp.isoformat(),
            "configuration": self.configuration,
            "total_trials": self.total_trials,
            "total_rejections": self.total_rejections,
            "observed_error_rate": self.observed_error_rate,
            "expected_error_rate": self.expected_error_rate,
            "confidence_interval_lower": self.confidence_interval_lower,
            "confidence_interval_upper": self.confidence_interval_upper,
            "vif": self.vif,
            "n_eff": self.n_eff,
            "regression_slope": self.regression_slope
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorRateSummary":
        """Create an ErrorRateSummary object from a dictionary."""
        ts_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now()
        
        return cls(
            summary_id=data["summary_id"],
            timestamp=timestamp,
            configuration=data["configuration"],
            total_trials=data["total_trials"],
            total_rejections=data["total_rejections"],
            observed_error_rate=data["observed_error_rate"],
            expected_error_rate=data["expected_error_rate"],
            confidence_interval_lower=data.get("confidence_interval_lower"),
            confidence_interval_upper=data.get("confidence_interval_upper"),
            vif=data.get("vif"),
            n_eff=data.get("n_eff"),
            regression_slope=data.get("regression_slope")
        )
