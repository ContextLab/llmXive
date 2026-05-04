"""
Time Series data model for Bayesian Nonparametrics Anomaly Detection.

Provides the core TimeSeries dataclass and iterator for streaming
observation processing in the DPGMM model.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Iterator
import numpy as np
import logging
from ..utils.streaming import StreamingObservation

logger = logging.getLogger(__name__)

@dataclass
class TimeSeries:
    """
    Core time series entity for anomaly detection.
    
    Stores timestamped observations with metadata for streaming
    processing and model training.
    
    Attributes:
        timestamps: List of datetime objects for each observation
        values: numpy array of float64 observation values
        metadata: Dictionary of additional context (dataset_id, source, etc.)
        is_sorted: Flag indicating if timestamps are in chronological order
        missing_mask: Boolean array indicating missing values (True = missing)
    """
    timestamps: List[datetime] = field(default_factory=list)
    values: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_sorted: bool = False
    missing_mask: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    
    def __post_init__(self):
        """Validate and initialize derived state."""
        # Ensure values is a numpy array
        if not isinstance(self.values, np.ndarray):
            self.values = np.array(self.values, dtype=np.float64)
        
        # Ensure missing_mask matches values length
        if len(self.missing_mask) != len(self.values):
            self.missing_mask = np.zeros(len(self.values), dtype=bool)
        
        # Check if timestamps are sorted
        if len(self.timestamps) > 1:
            self.is_sorted = all(
                self.timestamps[i] <= self.timestamps[i+1] 
                for i in range(len(self.timestamps) - 1)
            )
        else:
            self.is_sorted = True
        
        # Default metadata if empty
        if not self.metadata:
            self.metadata = {
                'dataset_id': 'unknown',
                'source': 'generated',
                'created_at': datetime.now().isoformat()
            }
    
    @classmethod
    def from_array(
        cls,
        values: np.ndarray,
        timestamps: Optional[List[datetime]] = None,
        frequency: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'TimeSeries':
        """
        Create TimeSeries from numpy array.
        
        Args:
            values: Observation values as numpy array
            timestamps: Optional list of timestamps (will generate if not provided)
            frequency: Optional frequency in seconds for timestamp generation
            metadata: Optional metadata dictionary
        
        Returns:
            TimeSeries instance
        """
        values = np.asarray(values, dtype=np.float64)
        
        if timestamps is None:
            # Generate synthetic timestamps
            if frequency is None:
                frequency = 1.0  # Default 1 second
            base_time = datetime.now()
            timestamps = [
                base_time.timestamp() + i * frequency 
                for i in range(len(values))
            ]
            timestamps = [datetime.fromtimestamp(ts) for ts in timestamps]
        
        return cls(
            timestamps=timestamps,
            values=values,
            metadata=metadata or {},
            is_sorted=True
        )
    
    @classmethod
    def from_streaming_observations(
        cls,
        observations: List[StreamingObservation],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'TimeSeries':
        """
        Create TimeSeries from list of streaming observations.
        
        Args:
            observations: List of StreamingObservation objects
            metadata: Optional metadata dictionary
        
        Returns:
            TimeSeries instance
        """
        timestamps = [obs.timestamp for obs in observations]
        values = np.array([obs.value for obs in observations], dtype=np.float64)
        missing_mask = np.array([obs.is_missing for obs in observations], dtype=bool)
        
        return cls(
            timestamps=timestamps,
            values=values,
            metadata=metadata or {},
            is_sorted=True,
            missing_mask=missing_mask
        )
    
    def append(self, timestamp: datetime, value: float, is_missing: bool = False) -> None:
        """
        Append a single observation to the time series.
        
        Args:
            timestamp: Observation timestamp
            value: Observation value
            is_missing: Whether this is a missing value
        """
        self.timestamps.append(timestamp)
        self.values = np.append(self.values, value)
        self.missing_mask = np.append(self.missing_mask, is_missing)
        self.is_sorted = True  # Assuming appends maintain order
    
    def get_valid_observations(self) -> Union[np.ndarray, List[datetime]]:
        """
        Get observations excluding missing values.
        
        Returns:
            Tuple of (values, timestamps) for non-missing observations
        """
        valid_mask = ~self.missing_mask
        return self.values[valid_mask], [
            ts for ts, is_missing in zip(self.timestamps, self.missing_mask) 
            if not is_missing
        ]
    
    def get_missing_count(self) -> int:
        """Return count of missing values in the series."""
        return int(np.sum(self.missing_mask))
    
    def get_length(self) -> int:
        """Return total number of observations."""
        return len(self.values)
    
    def get_valid_length(self) -> int:
        """Return number of non-missing observations."""
        return int(np.sum(~self.missing_mask))
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Compute basic statistics for the time series.
        
        Returns:
            Dictionary with mean, std, min, max, count
        """
        valid_values = self.values[~self.missing_mask]
        
        if len(valid_values) == 0:
            return {
                'mean': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'count': 0,
                'valid_count': 0,
                'missing_count': self.get_missing_count()
            }
        
        return {
            'mean': float(np.mean(valid_values)),
            'std': float(np.std(valid_values)),
            'min': float(np.min(valid_values)),
            'max': float(np.max(valid_values)),
            'count': len(self.values),
            'valid_count': len(valid_values),
            'missing_count': self.get_missing_count()
        }
    
    def slice(
        self,
        start_idx: Optional[int] = None,
        end_idx: Optional[int] = None
    ) -> 'TimeSeries':
        """
        Create a sliced copy of the time series.
        
        Args:
            start_idx: Start index (inclusive), defaults to 0
            end_idx: End index (exclusive), defaults to length
        
        Returns:
            New TimeSeries with sliced data
        """
        start_idx = start_idx or 0
        end_idx = end_idx or len(self.values)
        
        return TimeSeries(
            timestamps=self.timestamps[start_idx:end_idx],
            values=self.values[start_idx:end_idx],
            metadata=self.metadata.copy(),
            is_sorted=self.is_sorted,
            missing_mask=self.missing_mask[start_idx:end_idx]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert time series to dictionary representation.
        
        Returns:
            Dictionary with all time series data
        """
        return {
            'timestamps': [ts.isoformat() for ts in self.timestamps],
            'values': self.values.tolist(),
            'metadata': self.metadata,
            'is_sorted': self.is_sorted,
            'missing_mask': self.missing_mask.tolist(),
            'length': self.get_length(),
            'valid_length': self.get_valid_length(),
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSeries':
        """
        Create TimeSeries from dictionary.
        
        Args:
            data: Dictionary with time series data
        
        Returns:
            TimeSeries instance
        """
        timestamps = [datetime.fromisoformat(ts) for ts in data['timestamps']]
        values = np.array(data['values'], dtype=np.float64)
        missing_mask = np.array(data.get('missing_mask', [False] * len(values)), dtype=bool)
        
        return cls(
            timestamps=timestamps,
            values=values,
            metadata=data.get('metadata', {}),
            is_sorted=data.get('is_sorted', True),
            missing_mask=missing_mask
        )
    
    def __len__(self) -> int:
        """Return number of observations."""
        return len(self.values)
    
    def __getitem__(self, idx: Union[int, slice]) -> Union[Dict[str, Any], 'TimeSeries']:
        """
        Index into the time series.
        
        Args:
            idx: Integer index or slice
        
        Returns:
            Single observation dict or sliced TimeSeries
        """
        if isinstance(idx, int):
            return {
                'timestamp': self.timestamps[idx],
                'value': float(self.values[idx]),
                'is_missing': bool(self.missing_mask[idx])
            }
        elif isinstance(idx, slice):
            return self.slice(idx.start, idx.stop)
        else:
            raise TypeError(f"Invalid index type: {type(idx)}")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TimeSeries(n={self.get_length()}, "
            f"valid={self.get_valid_length()}, "
            f"missing={self.get_missing_count()}, "
            f"metadata={self.metadata})"
        )

@dataclass
class TimeSeriesIterator:
    """
    Iterator for sequential time series observation processing.
    
    Enables streaming processing of time series data one observation
    at a time, compatible with DPGMM streaming updates.
    
    Attributes:
        time_series: Reference to the TimeSeries being iterated
        current_idx: Current position in the iteration
        skip_missing: Whether to skip missing values during iteration
    """
    time_series: TimeSeries
    current_idx: int = 0
    skip_missing: bool = False
    
    def __iter__(self) -> 'TimeSeriesIterator':
        """Return self as iterator."""
        self.current_idx = 0
        return self
    
    def __next__(self) -> StreamingObservation:
        """
        Get next observation as StreamingObservation.
        
        Returns:
            StreamingObservation with timestamp, value, and missing flag
        
        Raises:
            StopIteration: When all observations have been processed
        """
        while self.current_idx < len(self.time_series):
            ts = self.time_series.timestamps[self.current_idx]
            value = float(self.time_series.values[self.current_idx])
            is_missing = bool(self.time_series.missing_mask[self.current_idx])
            
            self.current_idx += 1
            
            if self.skip_missing and is_missing:
                continue
            
            return StreamingObservation(
                timestamp=ts,
                value=value,
                is_missing=is_missing
            )
        
        raise StopIteration
    
    def reset(self) -> None:
        """Reset iterator to beginning."""
        self.current_idx = 0
    
    def get_remaining_count(self) -> int:
        """Return number of remaining observations."""
        if self.skip_missing:
            return int(np.sum(~self.time_series.missing_mask[self.current_idx:]))
        return len(self.time_series) - self.current_idx
    
    def to_list(self, skip_missing: Optional[bool] = None) -> List[StreamingObservation]:
        """
        Convert all remaining observations to list.
        
        Args:
            skip_missing: Override skip_missing setting
        
        Returns:
            List of StreamingObservation objects
        """
        original_skip = self.skip_missing
        if skip_missing is not None:
            self.skip_missing = skip_missing
        
        observations = list(self)
        self.skip_missing = original_skip
        self.reset()
        
        return observations
    
    def __len__(self) -> int:
        """Return total observations in underlying time series."""
        return len(self.time_series)
    
    def __repr__(self) -> str:
        """String representation."""
        remaining = self.get_remaining_count()
        return (
            f"TimeSeriesIterator(total={len(self.time_series)}, "
            f"remaining={remaining}, "
            f"skip_missing={self.skip_missing})"
        )

def create_time_series_from_csv(
    csv_path: Union[str, Path],
    timestamp_column: str = 'timestamp',
    value_column: str = 'value',
    missing_value_indicator: Optional[str] = None
) -> TimeSeries:
    """
    Load time series from CSV file.
    
    Args:
        csv_path: Path to CSV file
        timestamp_column: Name of timestamp column
        value_column: Name of value column
        missing_value_indicator: String value indicating missing data
    
    Returns:
        TimeSeries instance
    """
    import pandas as pd
    
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    
    # Parse timestamps
    timestamps = pd.to_datetime(df[timestamp_column]).tolist()
    
    # Parse values
    if missing_value_indicator is not None:
        values = df[value_column].replace(missing_value_indicator, np.nan)
        missing_mask = values.isna().values
        values = values.fillna(0).values  # Fill with 0, mask indicates missing
    else:
        values = df[value_column].values
        missing_mask = np.isnan(values)
        values = np.where(missing_mask, 0.0, values)
    
    return TimeSeries(
        timestamps=timestamps,
        values=values.astype(np.float64),
        metadata={'source': str(csv_path), 'format': 'csv'},
        missing_mask=missing_mask
    )

def save_time_series_to_csv(
    time_series: TimeSeries,
    output_path: Union[str, Path],
    include_missing: bool = True
) -> None:
    """
    Save time series to CSV file.
    
    Args:
        time_series: TimeSeries to save
        output_path: Output file path
        include_missing: Whether to include missing value markers
    """
    import pandas as pd
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data
    data = {
        'timestamp': [ts.isoformat() for ts in time_series.timestamps],
        'value': time_series.values.tolist()
    }
    
    if include_missing:
        data['is_missing'] = time_series.missing_mask.tolist()
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved time series with {len(time_series)} observations to {output_path}")