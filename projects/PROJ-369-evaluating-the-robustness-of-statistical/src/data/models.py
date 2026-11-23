"""
Base data models for time series and synthetic data generation.

This module defines the core data structures used throughout the project
for representing time series data, both real and synthetic.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
import numpy as np
import pandas as pd
from enum import Enum

class TimeSeriesType(Enum):
    """Enumeration of time series types."""
    REAL = "real"
    SYNTHETIC = "synthetic"

class SyntheticProcessType(Enum):
    """Enumeration of synthetic process types."""
    FGn = "fGn"  # fractional Gaussian noise
    ARFIMA = "arfima"  # Autoregressive Fractionally Integrated Moving Average
    RANDOM_WALK = "random_walk"
    WHITE_NOISE = "white_noise"

@dataclass
class TimeSeries:
    """
    Represents a time series dataset with metadata.
    
    Attributes:
        name: Unique identifier for the time series
        values: Numpy array of time series values
        timestamps: Optional array of timestamps (can be None for regular intervals)
        series_type: Type of series (real or synthetic)
        source: Original source of the data (URL, dataset name, etc.)
        metadata: Additional metadata dictionary
        is_stationary: Whether the series has been tested and confirmed stationary
        stationarity_method: Method used to test stationarity (e.g., 'adf', 'dfa')
        stationarity_p_value: P-value from stationarity test (if applicable)
        missing_count: Number of missing values originally present
        interpolation_method: Method used for missing value interpolation (if any)
    """
    name: str
    values: np.ndarray
    timestamps: Optional[np.ndarray] = None
    series_type: TimeSeriesType = TimeSeriesType.REAL
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_stationary: Optional[bool] = None
    stationarity_method: Optional[str] = None
    stationarity_p_value: Optional[float] = None
    missing_count: int = 0
    interpolation_method: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize the time series data."""
        if not isinstance(self.values, np.ndarray):
            self.values = np.array(self.values)
        
        if self.values.ndim != 1:
            raise ValueError(f"Time series values must be 1D array, got {self.values.ndim}D")
        
        if np.any(np.isnan(self.values)):
            self.missing_count = int(np.sum(np.isnan(self.values)))
        
        if self.timestamps is not None and not isinstance(self.timestamps, np.ndarray):
            self.timestamps = np.array(self.timestamps)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert the time series to a pandas DataFrame."""
        data = {'value': self.values}
        if self.timestamps is not None:
            data['timestamp'] = self.timestamps
        df = pd.DataFrame(data)
        df['name'] = self.name
        return df
    
    def get_statistics(self) -> Dict[str, float]:
        """Compute basic statistics for the time series."""
        return {
            'mean': float(np.mean(self.values)),
            'std': float(np.std(self.values)),
            'min': float(np.min(self.values)),
            'max': float(np.max(self.values)),
            'length': len(self.values),
            'missing_count': self.missing_count
        }

@dataclass
class SyntheticData:
    """
    Represents synthetic time series data with known ground truth parameters.
    
    Attributes:
        name: Unique identifier for the synthetic dataset
        time_series: The TimeSeries object containing the data
        process_type: Type of synthetic process (fGn, ARFIMA, etc.)
        hurst_exponent: True Hurst exponent (H) used for generation
        sample_size: Number of data points (N)
        mean: True mean of the process
        seed: Random seed used for reproducibility
        parameters: Additional process-specific parameters
        theoretical_vif: Theoretical Variance Inflation Factor
        theoretical_n_eff: Theoretical effective sample size
    """
    name: str
    time_series: TimeSeries
    process_type: SyntheticProcessType
    hurst_exponent: float
    sample_size: int
    mean: float = 0.0
    seed: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    theoretical_vif: Optional[float] = None
    theoretical_n_eff: Optional[float] = None
    
    def __post_init__(self):
        """Validate synthetic data parameters."""
        if not 0.0 < self.hurst_exponent < 1.0:
            raise ValueError(f"Hurst exponent must be in (0, 1), got {self.hurst_exponent}")
        
        if self.sample_size != len(self.time_series.values):
            raise ValueError(
                f"Sample size mismatch: {self.sample_size} vs actual {len(self.time_series.values)}"
            )
        
        # Set the time series metadata to reflect synthetic origin
        self.time_series.series_type = TimeSeriesType.SYNTHETIC
        self.time_series.source = f"synthetic:{self.process_type.value}"
        self.time_series.metadata['hurst_exponent'] = self.hurst_exponent
        self.time_series.metadata['process_type'] = self.process_type.value
        self.time_series.metadata['seed'] = self.seed
    
    def get_ground_truth(self) -> Dict[str, float]:
        """Return the known ground truth parameters."""
        return {
            'hurst_exponent': self.hurst_exponent,
            'mean': self.mean,
            'sample_size': self.sample_size,
            'theoretical_vif': self.theoretical_vif,
            'theoretical_n_eff': self.theoretical_n_eff
        }
    
    def compute_theoretical_vif(self) -> float:
        """
        Compute theoretical Variance Inflation Factor based on Hurst exponent.
        
        VIF ≈ 2^(2H) for large N, or more precisely:
        VIF = (2N)^2H / N for fGn processes
        """
        N = self.sample_size
        H = self.hurst_exponent
        if N <= 1:
            return 1.0
        # Approximation for large N
        vif = (2 * N) ** (2 * H) / N
        self.theoretical_vif = float(vif)
        return self.theoretical_vif
    
    def compute_theoretical_n_eff(self) -> float:
        """
        Compute theoretical effective sample size.
        
        N_eff ≈ N / VIF
        """
        if self.theoretical_vif is None:
            self.compute_theoretical_vif()
        
        if self.theoretical_vif is None or self.theoretical_vif <= 0:
            return float(self.sample_size)
        
        n_eff = self.sample_size / self.theoretical_vif
        self.theoretical_n_eff = float(n_eff)
        return self.theoretical_n_eff