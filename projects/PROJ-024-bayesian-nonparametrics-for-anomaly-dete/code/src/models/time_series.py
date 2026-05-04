"""
TimeSeries dataclass and entity definitions for Bayesian nonparametric anomaly detection.

This module defines the core TimeSeries entity that represents time-ordered
observations with metadata, validation, and streaming compatibility.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import numpy as np

from ..streaming import StreamingObservation


@dataclass
class TimeSeries:
    """
    Core time series entity for anomaly detection.

    Represents a named time series with observations, metadata, and
    support for streaming processing. Compatible with the streaming
    utilities in utils/streaming.py.

    Attributes:
        name: Unique identifier for this time series
        values: 1D numpy array of numeric observations
        timestamps: Optional 1D array of timestamps (datetime or numeric)
        metadata: Additional key-value metadata about the series
        source: Original data source (file path, URL, or 'synthetic')
        is_processed: Whether this series has been preprocessed (normalized, etc.)
        start_index: Starting index for valid observations (for truncated series)
        end_index: Ending index for valid observations (for truncated series)

    Example:
        >>> ts = TimeSeries(
        ...     name='nyc_taxi',
        ...     values=np.array([100.5, 102.3, 98.7, 150.2]),
        ...     timestamps=np.array([0, 1, 2, 3]),
        ...     source='data/raw/nyc_taxi.csv'
        ... )
        >>> print(f"Series has {len(ts)} observations")
        Series has 4 observations
    """

    name: str
    values: np.ndarray
    timestamps: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    is_processed: bool = False
    start_index: int = 0
    end_index: Optional[int] = None

    def __post_init__(self):
        """Validate and normalize the time series after initialization."""
        # Ensure values is a numpy array
        if not isinstance(self.values, np.ndarray):
            self.values = np.asarray(self.values, dtype=np.float64)
        else:
            self.values = self.values.astype(np.float64)

        # Ensure 1D array
        if self.values.ndim == 0:
            self.values = self.values.reshape(1)
        elif self.values.ndim > 1:
            self.values = self.values.flatten()

        # Handle timestamps
        if self.timestamps is not None:
            if not isinstance(self.timestamps, np.ndarray):
                self.timestamps = np.asarray(self.timestamps)
            else:
                self.timestamps = self.timestamps.flatten()

            if len(self.timestamps) != len(self.values):
                raise ValueError(
                    f"Timestamps length ({len(self.timestamps)}) must match "
                    f"values length ({len(self.values)})"
                )

        # Validate indices
        if self.end_index is None:
            self.end_index = len(self.values)

        if self.start_index < 0 or self.end_index > len(self.values):
            raise ValueError(
                f"Invalid indices: start={self.start_index}, "
                f"end={self.end_index}, length={len(self.values)}"
            )

        if self.start_index >= self.end_index:
            raise ValueError(
                f"start_index ({self.start_index}) must be < end_index ({self.end_index})"
            )

    @property
    def length(self) -> int:
        """Return the length of valid observations in this series."""
        return self.end_index - self.start_index

    @property
    def observations(self) -> np.ndarray:
        """Return the valid slice of observations."""
        return self.values[self.start_index:self.end_index]

    @property
    def obs_timestamps(self) -> Optional[np.ndarray]:
        """Return the valid slice of timestamps, or None if not present."""
        if self.timestamps is None:
            return None
        return self.timestamps[self.start_index:self.end_index]

    def get_observation_at(self, index: int) -> Optional[StreamingObservation]:
        """
        Get a single observation at the given index as a StreamingObservation.

        Args:
            index: Index within the valid observation range (0 to length-1)

        Returns:
            StreamingObservation with value and timestamp, or None if out of range
        """
        if index < 0 or index >= self.length:
            return None

        abs_index = self.start_index + index
        value = float(self.values[abs_index])

        timestamp = None
        if self.timestamps is not None:
            ts_val = self.timestamps[abs_index]
            if isinstance(ts_val, datetime):
                timestamp = ts_val
            elif isinstance(ts_val, (int, float)):
                timestamp = ts_val

        return StreamingObservation(
            value=value,
            timestamp=timestamp,
            metadata={
                'series_name': self.name,
                'global_index': abs_index,
                **self.metadata
            }
        )

    def iterate_observations(self) -> 'TimeSeriesIterator':
        """
        Create an iterator over observations for streaming processing.

        Yields:
            StreamingObservation for each valid observation in order

        Example:
            >>> for obs in ts.iterate_observations():
            ...     print(f"Obs: {obs.value} at {obs.timestamp}")
        """
        return TimeSeriesIterator(self)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize this time series to a dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            'name': self.name,
            'values': self.observations.tolist(),
            'timestamps': self.obs_timestamps.tolist() if self.obs_timestamps is not None else None,
            'metadata': self.metadata,
            'source': self.source,
            'is_processed': self.is_processed,
            'length': self.length
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSeries':
        """
        Deserialize a time series from a dictionary.

        Args:
            data: Dictionary from to_dict() or JSON

        Returns:
            TimeSeries instance
        """
        return cls(
            name=data['name'],
            values=np.array(data['values'], dtype=np.float64),
            timestamps=(
                np.array(data['timestamps'], dtype=np.float64)
                if data.get('timestamps') is not None
                else None
            ),
            metadata=data.get('metadata', {}),
            source=data.get('source'),
            is_processed=data.get('is_processed', False)
        )

    def slice(self, start: int, end: Optional[int] = None) -> 'TimeSeries':
        """
        Create a new TimeSeries with a subset of observations.

        Args:
            start: Start index (relative to current valid range)
            end: End index (relative to current valid range, None means to end)

        Returns:
            New TimeSeries with sliced observations
        """
        if end is None:
            end = self.length

        if start < 0 or end > self.length or start >= end:
            raise ValueError(
                f"Invalid slice: start={start}, end={end}, length={self.length}"
            )

        new_start = self.start_index + start
        new_end = self.start_index + end

        return TimeSeries(
            name=self.name,
            values=self.values.copy(),
            timestamps=self.timestamps.copy() if self.timestamps is not None else None,
            metadata=self.metadata.copy(),
            source=self.source,
            is_processed=self.is_processed,
            start_index=new_start,
            end_index=new_end
        )

    def __len__(self) -> int:
        """Return the number of valid observations."""
        return self.length

    def __repr__(self) -> str:
        return (
            f"TimeSeries(name='{self.name}', length={self.length}, "
            f"source={self.source}, processed={self.is_processed})"
        )

@dataclass
class TimeSeriesIterator:
    """
    Iterator over TimeSeries observations for streaming processing.

    Wraps a TimeSeries and yields StreamingObservation objects one at a time,
    compatible with the StreamingObservationProcessor interface.
    """

    time_series: TimeSeries
    _current_index: int = field(default=0, init=False)

    def __iter__(self) -> 'TimeSeriesIterator':
        return self

    def __next__(self) -> StreamingObservation:
        if self._current_index >= self.time_series.length:
            raise StopIteration

        obs = self.time_series.get_observation_at(self._current_index)
        self._current_index += 1

        if obs is None:
            raise StopIteration

        return obs

    def reset(self) -> None:
        """Reset the iterator to the beginning."""
        self._current_index = 0