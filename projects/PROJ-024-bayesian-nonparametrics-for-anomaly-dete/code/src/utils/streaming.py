"""
Streaming utilities for sequential observation processing in time series anomaly detection.

This module provides classes and functions for:
- Sequential observation ingestion and processing
- Missing value handling and imputation
- Sliding window buffer management
- Real-time statistics computation

Designed to work with the DPGMM model (dp_gmm.py) for incremental inference.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Iterator
import numpy as np
from pathlib import Path


@dataclass
class StreamingObservation:
    """
    Represents a single time series observation in a streaming context.
    
    Attributes:
        timestamp: Unix timestamp or sequence index of the observation
        value: Observed value (float, can be NaN for missing)
        is_missing: Whether this observation is missing/NaN
        metadata: Optional metadata dictionary for the observation
    """
    timestamp: float
    value: float
    is_missing: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate observation after initialization."""
        if self.is_missing:
            self.value = float('nan')
        elif np.isnan(self.value):
            self.is_missing = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to dictionary representation."""
        return {
            'timestamp': self.timestamp,
            'value': self.value,
            'is_missing': self.is_missing,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingObservation':
        """Create observation from dictionary."""
        return cls(
            timestamp=data['timestamp'],
            value=data['value'],
            is_missing=data.get('is_missing', False),
            metadata=data.get('metadata', {})
        )


class StreamingObservationProcessor:
    """
    Processes time series observations sequentially for online anomaly detection.
    
    This class handles:
    - Sequential observation ingestion
    - Missing value tracking and imputation options
    - Sliding window buffer management
    - Real-time statistics computation
    
    Memory efficient: maintains bounded buffer size to prevent unbounded growth.
    """
    
    def __init__(
        self,
        window_size: int = 100,
        validate: bool = True,
        impute_missing: bool = False,
        imputation_strategy: str = 'forward_fill'
    ):
        """
        Initialize the streaming observation processor.
        
        Args:
            window_size: Maximum number of observations to keep in buffer
            validate: Whether to validate observations on ingestion
            impute_missing: Whether to impute missing values
            imputation_strategy: Strategy for missing value imputation
                                ('forward_fill', 'mean', 'interpolate', 'none')
        """
        self.window_size = window_size
        self.validate = validate
        self.impute_missing = impute_missing
        self.imputation_strategy = imputation_strategy
        
        self._buffer: List[StreamingObservation] = []
        self._observation_count: int = 0
        self._missing_count: int = 0
        self._last_valid_value: Optional[float] = None
        self._running_mean: Optional[float] = None
        self._running_var: Optional[float] = None
    
    def ingest(self, timestamp: float, value: float, metadata: Optional[Dict[str, Any]] = None) -> StreamingObservation:
        """
        Ingest a new observation into the streaming processor.
        
        Args:
            timestamp: Observation timestamp
            value: Observation value (can be NaN for missing)
            metadata: Optional metadata dictionary
            
        Returns:
            StreamingObservation object representing the ingested observation
        """
        is_missing = np.isnan(value) if isinstance(value, (int, float)) else False
        
        observation = StreamingObservation(
            timestamp=timestamp,
            value=float(value) if not is_missing else np.nan,
            is_missing=is_missing,
            metadata=metadata or {}
        )
        
        if self.validate and not self._validate_observation(observation):
            raise ValueError(f"Invalid observation: {observation}")
        
        # Handle missing value imputation if enabled
        if is_missing and self.impute_missing:
            observation = self._impute_missing_value(observation)
        
        self._buffer.append(observation)
        self._observation_count += 1
        
        if is_missing and not self.impute_missing:
            self._missing_count += 1
        
        # Maintain buffer size
        if len(self._buffer) > self.window_size:
            self._buffer.pop(0)
        
        # Update running statistics
        self._update_running_stats(observation.value)
        
        return observation
    
    def ingest_batch(self, timestamps: np.ndarray, values: np.ndarray) -> List[StreamingObservation]:
        """
        Ingest a batch of observations.
        
        Args:
            timestamps: Array of observation timestamps
            values: Array of observation values
            
        Returns:
            List of StreamingObservation objects
        """
        observations = []
        for ts, val in zip(timestamps, values):
            obs = self.ingest(float(ts), float(val))
            observations.append(obs)
        return observations
    
    def _validate_observation(self, observation: StreamingObservation) -> bool:
        """Validate an observation before ingestion."""
        if observation.timestamp is None:
            return False
        if not isinstance(observation.value, (int, float)):
            return False
        return True
    
    def _impute_missing_value(self, observation: StreamingObservation) -> StreamingObservation:
        """
        Impute a missing value based on configured strategy.
        
        Args:
            observation: Observation with missing value
            
        Returns:
            Observation with imputed value
        """
        if self.imputation_strategy == 'forward_fill':
            if self._last_valid_value is not None:
                observation.value = self._last_valid_value
            else:
                observation.value = 0.0
        elif self.imputation_strategy == 'mean':
            if self._running_mean is not None:
                observation.value = self._running_mean
            else:
                observation.value = 0.0
        elif self.imputation_strategy == 'interpolate':
            # Simple linear interpolation using neighbors
            if len(self._buffer) >= 2:
                prev_obs = self._buffer[-2]
                next_obs = observation
                if not np.isnan(prev_obs.value):
                    observation.value = prev_obs.value
                else:
                    observation.value = 0.0
            else:
                observation.value = 0.0
        
        observation.is_missing = False
        return observation
    
    def _update_running_stats(self, value: float):
        """Update running mean and variance (Welford's algorithm)."""
        if not np.isnan(value):
            self._last_valid_value = value
            if self._running_mean is None:
                self._running_mean = value
                self._running_var = 0.0
            else:
                delta = value - self._running_mean
                self._running_mean += delta / self._observation_count
                delta2 = value - self._running_mean
                self._running_var += delta * delta2
    
    def get_recent_observations(self, n: int) -> List[StreamingObservation]:
        """
        Get the n most recent observations.
        
        Args:
            n: Number of observations to retrieve
            
        Returns:
            List of StreamingObservation objects
        """
        n = min(n, len(self._buffer))
        return self._buffer[-n:] if n > 0 else []
    
    def get_values(self) -> np.ndarray:
        """
        Get all values from the buffer as a numpy array.
        
        Returns:
            Numpy array of observation values
        """
        return np.array([obs.value for obs in self._buffer])
    
    def get_timestamps(self) -> np.ndarray:
        """
        Get all timestamps from the buffer as a numpy array.
        
        Returns:
            Numpy array of observation timestamps
        """
        return np.array([obs.timestamp for obs in self._buffer])
    
    def get_valid_values(self) -> np.ndarray:
        """
        Get non-missing values from the buffer.
        
        Returns:
            Numpy array of valid observation values
        """
        return np.array([obs.value for obs in self._buffer if not obs.is_missing])
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get basic statistics about the current buffer.
        
        Returns:
            Dictionary with count, missing_count, missing_ratio, mean, std
        """
        values = self.get_valid_values()
        
        return {
            'count': self._observation_count,
            'missing_count': self._missing_count,
            'missing_ratio': self._missing_count / self._observation_count if self._observation_count > 0 else 0.0,
            'mean': float(np.mean(values)) if len(values) > 0 else np.nan,
            'std': float(np.std(values)) if len(values) > 0 else np.nan,
            'buffer_size': len(self._buffer),
            'running_mean': self._running_mean if self._running_mean is not None else np.nan,
            'running_var': self._running_var if self._running_var is not None else np.nan
        }
    
    def clear(self):
        """Clear the observation buffer and reset statistics."""
        self._buffer.clear()
        self._observation_count = 0
        self._missing_count = 0
        self._last_valid_value = None
        self._running_mean = None
        self._running_var = None
    
    def __len__(self) -> int:
        """Return the number of observations in the buffer."""
        return len(self._buffer)
    
    def __iter__(self) -> Iterator[StreamingObservation]:
        """Iterate over observations in the buffer."""
        return iter(self._buffer)
    
    def __repr__(self) -> str:
        """String representation of the processor."""
        return (f"StreamingObservationProcessor(window_size={self.window_size}, "
                f"observations={self._observation_count}, "
                f"missing={self._missing_count})")


class SlidingWindowBuffer:
    """
    Fixed-size sliding window buffer for streaming data.
    
    Efficient for computing rolling statistics without storing
    the entire time series.
    """
    
    def __init__(self, window_size: int, dtype: type = float):
        """
        Initialize the sliding window buffer.
        
        Args:
            window_size: Maximum size of the window
            dtype: Data type for stored values
        """
        self.window_size = window_size
        self.dtype = dtype
        self._data: np.ndarray = np.zeros(window_size, dtype=dtype)
        self._position: int = 0
        self._is_full: bool = False
    
    def append(self, value: float):
        """
        Append a value to the buffer.
        
        Args:
            value: Value to append
        """
        self._data[self._position] = value
        self._position = (self._position + 1) % self.window_size
        self._is_full = self._is_full or (self._position == 0)
    
    def get_window(self) -> np.ndarray:
        """
        Get the current window contents.
        
        Returns:
            Numpy array of window values
        """
        if self._is_full:
            return np.concatenate([self._data[self._position:], self._data[:self._position]])
        else:
            return self._data[:self._position]
    
    def mean(self) -> float:
        """Compute the mean of the current window."""
        return float(np.mean(self.get_window()))
    
    def std(self) -> float:
        """Compute the standard deviation of the current window."""
        return float(np.std(self.get_window()))
    
    def z_score(self, value: float) -> float:
        """
        Compute the z-score of a value relative to the window.
        
        Args:
            value: Value to score
            
        Returns:
            Z-score
        """
        window = self.get_window()
        mean = np.mean(window)
        std = np.std(window)
        if std < 1e-10:
            return 0.0
        return float((value - mean) / std)
    
    def clear(self):
        """Clear the buffer."""
        self._data.fill(0)
        self._position = 0
        self._is_full = False
    
    def __len__(self) -> int:
        """Return the current number of elements in the buffer."""
        return self.window_size if self._is_full else self._position


def create_streaming_processor(
    config: Optional[Dict[str, Any]] = None,
    window_size: Optional[int] = None
) -> StreamingObservationProcessor:
    """
    Factory function to create a streaming processor with sensible defaults.
    
    Args:
        config: Optional configuration dictionary
        window_size: Optional window size override
        
    Returns:
        Configured StreamingObservationProcessor instance
    """
    defaults = {
        'window_size': 100,
        'validate': True,
        'impute_missing': False,
        'imputation_strategy': 'forward_fill'
    }
    
    if config:
        defaults.update(config)
    
    if window_size is not None:
        defaults['window_size'] = window_size
    
    return StreamingObservationProcessor(**defaults)

__all__ = [
    'StreamingObservation',
    'StreamingObservationProcessor',
    'SlidingWindowBuffer',
    'create_streaming_processor'
]