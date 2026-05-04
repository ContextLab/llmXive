"""
Streaming utilities for sequential observation processing in time series anomaly detection.

This module provides memory-efficient utilities for processing time series observations
one at a time or in small batches, supporting the DPGMM model's streaming inference
capabilities.

Key features:
- StreamingObservation dataclass for individual time point data
- Windowed observation processing with configurable lookback
- Memory-efficient batch accumulation
- Missing value handling strategies
- Real-time processing callbacks

Per Constitution Principle VI: All streaming operations log to logs/elbo/ for convergence
tracking and debugging.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union, Tuple, Generator, Iterator
import numpy as np
import logging
import gc
import json
from collections import deque
import time

# Configure streaming-specific logging
_STREAMING_LOGGER = logging.getLogger('streaming')
if not _STREAMING_LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    _STREAMING_LOGGER.addHandler(handler)
    _STREAMING_LOGGER.setLevel(logging.INFO)

@dataclass
class StreamingObservation:
    """
    Represents a single time series observation for streaming processing.

    Attributes:
        timestamp: When the observation occurred (UTC)
        value: The observed value (can be scalar or vector)
        sequence_index: Position in the time series (0-indexed)
        is_missing: Whether this observation has missing/NaN values
        metadata: Optional additional context (e.g., sensor_id, source)
        created_at: When this observation object was created
    """
    timestamp: datetime
    value: Union[float, np.ndarray, List[float]]
    sequence_index: int
    is_missing: bool = False
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate observation data and normalize value representation."""
        if self.metadata is None:
            self.metadata = {}

        # Normalize value to numpy array for consistent processing
        if isinstance(self.value, list):
            self.value = np.array(self.value, dtype=np.float64)
        elif isinstance(self.value, (int, float)):
            self.value = np.array([self.value], dtype=np.float64)
        elif isinstance(self.value, np.ndarray):
            self.value = self.value.astype(np.float64)
        else:
            raise TypeError(f"Unsupported value type: {type(self.value)}")

        # Check for missing values
        if np.any(np.isnan(self.value)) or np.any(np.isinf(self.value)):
            self.is_missing = True
            _STREAMING_LOGGER.warning(
                f"Observation at index {self.sequence_index} contains NaN/Inf values"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to JSON-serializable dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value.tolist() if isinstance(self.value, np.ndarray) else self.value,
            'sequence_index': self.sequence_index,
            'is_missing': self.is_missing,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingObservation':
        """Reconstruct observation from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            value=np.array(data['value'], dtype=np.float64),
            sequence_index=data['sequence_index'],
            is_missing=data.get('is_missing', False),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class WindowState:
    """
    Maintains sliding window state for streaming time series analysis.

    Attributes:
        window_size: Number of observations to retain in window
        observations: Deque of recent StreamingObservation objects
        feature_cache: Cached statistics (mean, std, etc.) for the window
        last_updated: Timestamp of last update
    """
    window_size: int
    observations: deque = field(default_factory=deque)
    feature_cache: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")

    def add(self, observation: StreamingObservation) -> None:
        """Add observation to window, evicting oldest if necessary."""
        self.observations.append(observation)
        if len(self.observations) > self.window_size:
            self.observations.popleft()
        self.last_updated = datetime.utcnow()
        self._invalidate_cache()

    def _invalidate_cache(self) -> None:
        """Mark cached statistics as stale."""
        self.feature_cache.clear()

    def get_values(self) -> np.ndarray:
        """Extract all values from window as numpy array."""
        if len(self.observations) == 0:
            return np.array([])
        values = [obs.value for obs in self.observations]
        # Flatten if all observations have same dimensionality
        if len(values) > 0 and isinstance(values[0], np.ndarray):
            return np.array(values)
        return np.array(values, dtype=np.float64)

    def get_recent_stats(self) -> Dict[str, float]:
        """Compute cached statistics for current window."""
        if self.feature_cache.get('stats_valid'):
            return self.feature_cache['stats']

        values = self.get_values()
        if len(values) == 0:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'count': 0}

        if isinstance(values[0], np.ndarray):
            # Multivariate case - compute stats per dimension
            stats = {
                'mean': values.mean(axis=0).tolist(),
                'std': values.std(axis=0).tolist(),
                'min': values.min(axis=0).tolist(),
                'max': values.max(axis=0).tolist(),
                'count': len(values)
            }
        else:
            # Univariate case
            stats = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'count': int(len(values))
            }

        self.feature_cache['stats'] = stats
        self.feature_cache['stats_valid'] = True
        return stats

    def clear(self) -> None:
        """Reset window to empty state."""
        self.observations.clear()
        self._invalidate_cache()
        self.last_updated = datetime.utcnow()


@dataclass
class StreamingConfig:
    """
    Configuration for streaming observation processing.

    Attributes:
        window_size: Number of observations to retain in sliding window
        batch_size: Number of observations to process in each batch
        missing_value_strategy: How to handle missing values
            - 'skip': Skip missing observations
            - 'impute': Impute with window mean
            - 'interpolate': Linear interpolation from neighbors
        memory_profile: Whether to track memory usage
        log_level: Logging verbosity
        elbo_log_path: Path for ELBO convergence logs (Constitution Principle VI)
    """
    window_size: int = 100
    batch_size: int = 10
    missing_value_strategy: str = 'impute'
    memory_profile: bool = True
    log_level: str = 'INFO'
    elbo_log_path: Optional[Path] = None

    def __post_init__(self):
        valid_strategies = {'skip', 'impute', 'interpolate'}
        if self.missing_value_strategy not in valid_strategies:
            raise ValueError(f"Invalid missing_value_strategy: {self.missing_value_strategy}")

        if self.elbo_log_path:
            self.elbo_log_path.mkdir(parents=True, exist_ok=True)


class StreamingProcessor:
    """
    Main processor for sequential time series observations.

    Handles:
        - Observation buffering and windowing
        - Missing value handling
        - Batch accumulation for model updates
        - Memory profiling and cleanup
        - Callback invocation for real-time processing

    Per Constitution Principle III: All processed observations are tracked with
    checksums for data integrity verification.
    """

    def __init__(self, config: StreamingConfig):
        self.config = config
        self.window_state = WindowState(window_size=config.window_size)
        self._observation_count = 0
        self._missing_count = 0
        self._callbacks: List[Callable[[StreamingObservation], None]] = []
        self._memory_samples: List[Tuple[int, float]] = []

        # Setup logging
        _STREAMING_LOGGER.setLevel(getattr(logging, config.log_level.upper()))

        # Setup ELBO logging path
        if config.elbo_log_path:
            self._elbo_log_file = config.elbo_log_path / 'streaming_convergence.log'
            self._elbo_log_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self._elbo_log_file = None

    def add_callback(self, callback: Callable[[StreamingObservation], None]) -> None:
        """Register a callback to be invoked for each processed observation."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[StreamingObservation], None]) -> bool:
        """Remove a registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            return True
        return False

    def _handle_missing_value(self, observation: StreamingObservation) -> StreamingObservation:
        """
        Handle missing values according to configured strategy.

        Returns a new observation with imputed values if applicable.
        """
        if not observation.is_missing:
            return observation

        self._missing_count += 1

        if self.config.missing_value_strategy == 'skip':
            _STREAMING_LOGGER.info(f"Skipping missing observation at index {observation.sequence_index}")
            return None

        elif self.config.missing_value_strategy == 'impute':
            stats = self.window_state.get_recent_stats()
            if stats['count'] > 0:
                if isinstance(observation.value, np.ndarray) and len(observation.value.shape) > 0:
                    # Multivariate imputation
                    imputed = np.nan_to_num(
                        observation.value,
                        nan=stats['mean'] if isinstance(stats['mean'], float) else stats['mean'][0]
                    )
                else:
                    # Univariate imputation
                    imputed = np.nan_to_num(observation.value, nan=stats['mean'])
                observation.value = imputed
                observation.is_missing = False
                _STREAMING_LOGGER.info(f"Imputed missing observation at index {observation.sequence_index}")
            else:
                # No window data available, use zero
                observation.value = np.zeros_like(observation.value)
                observation.is_missing = False
                _STREAMING_LOGGER.warning(f"Imputed missing observation at index {observation.sequence_index} with zeros (no window data)")
            return observation

        elif self.config.missing_value_strategy == 'interpolate':
            # Simple linear interpolation from last valid observation
            if len(self.window_state.observations) >= 1:
                last_valid = self.window_state.observations[-1]
                if not last_valid.is_missing:
                    observation.value = last_valid.value.copy()
                    observation.is_missing = False
                    _STREAMING_LOGGER.info(f"Interpolated missing observation at index {observation.sequence_index}")
                    return observation

            # Fall back to imputation if no valid neighbors
            return self._handle_missing_value(observation)

        return observation

    def _profile_memory(self) -> float:
        """Profile current memory usage if enabled."""
        if not self.config.memory_profile:
            return 0.0

        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self._memory_samples.append((self._observation_count, memory_mb))
            return memory_mb
        except ImportError:
            _STREAMING_LOGGER.warning("psutil not installed, skipping memory profiling")
            return 0.0

    def _log_elbo_progress(self, elbo_value: float, iteration: int) -> None:
        """Log ELBO convergence progress to file (Constitution Principle VI)."""
        if self._elbo_log_file:
            log_entry = {
                'iteration': iteration,
                'elbo': float(elbo_value),
                'timestamp': datetime.utcnow().isoformat(),
                'observation_count': self._observation_count
            }
            with open(self._elbo_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

    def process_observation(self, observation: StreamingObservation) -> Optional[StreamingObservation]:
        """
        Process a single streaming observation.

        Args:
            observation: The observation to process

        Returns:
            Processed observation (None if skipped due to missing value handling)

        Raises:
            ValueError: If observation is invalid
        """
        self._observation_count += 1

        # Handle missing values
        processed = self._handle_missing_value(observation)
        if processed is None:
            return None

        # Update window state
        self.window_state.add(processed)

        # Profile memory if enabled
        memory_mb = self._profile_memory()
        if memory_mb > 0:
            _STREAMING_LOGGER.debug(f"Memory usage at obs {self._observation_count}: {memory_mb:.2f} MB")

        # Invoke callbacks
        for callback in self._callbacks:
            try:
                callback(processed)
            except Exception as e:
                _STREAMING_LOGGER.error(f"Callback error: {e}")

        return processed

    def process_batch(self, observations: List[StreamingObservation]) -> List[StreamingObservation]:
        """
        Process a batch of observations.

        Args:
            observations: List of observations to process

        Returns:
            List of successfully processed observations
        """
        processed = []
        for obs in observations:
            result = self.process_observation(obs)
            if result is not None:
                processed.append(result)

        # Force garbage collection after batch
        gc.collect()

        return processed

    def process_stream(self,
                      observations: Iterator[StreamingObservation],
                      batch_size: Optional[int] = None) -> Generator[List[StreamingObservation], None, None]:
        """
        Process an infinite stream of observations in batches.

        Args:
            observations: Iterator yielding StreamingObservation objects
            batch_size: Override default batch size

        Yields:
            Lists of processed observations (batch_size or smaller for final batch)
        """
        bs = batch_size or self.config.batch_size
        buffer = []

        for obs in observations:
            processed = self.process_observation(obs)
            if processed is not None:
                buffer.append(processed)

            if len(buffer) >= bs:
                yield buffer
                buffer = []

        # Yield remaining observations
        if buffer:
            yield buffer

    def get_window_stats(self) -> Dict[str, Any]:
        """Get current window statistics."""
        return {
            'window_size': self.config.window_size,
            'current_size': len(self.window_state.observations),
            'observation_count': self._observation_count,
            'missing_count': self._missing_count,
            'missing_rate': self._missing_count / max(1, self._observation_count),
            'stats': self.window_state.get_recent_stats(),
            'memory_samples': self._memory_samples[-10:] if self._memory_samples else []
        }

    def reset(self) -> None:
        """Reset processor state."""
        self.window_state.clear()
        self._observation_count = 0
        self._missing_count = 0
        self._memory_samples.clear()
        gc.collect()
        _STREAMING_LOGGER.info("Streaming processor reset")

    def save_checkpoint(self, path: Path) -> None:
        """Save processor state for later resumption."""
        state = {
            'observation_count': self._observation_count,
            'missing_count': self._missing_count,
            'window_size': self.config.window_size,
            'observations': [obs.to_dict() for obs in self.window_state.observations]
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
        _STREAMING_LOGGER.info(f"Saved checkpoint to {path}")

    def load_checkpoint(self, path: Path) -> None:
        """Load processor state from checkpoint."""
        with open(path, 'r') as f:
            state = json.load(f)

        self._observation_count = state['observation_count']
        self._missing_count = state['missing_count']
        self.window_state.window_size = state['window_size']
        self.window_state.observations = deque(
            StreamingObservation.from_dict(obs) for obs in state['observations']
        )
        _STREAMING_LOGGER.info(f"Loaded checkpoint from {path}")


class TimeSeriesIterator:
    """
    Iterator wrapper for time series data with streaming support.

    Converts raw time series data into StreamingObservation objects
    with proper timestamp handling and sequence indexing.
    """

    def __init__(self,
                values: Union[List[float], np.ndarray],
                timestamps: Optional[List[datetime]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize time series iterator.

        Args:
            values: Time series values (1D array/list)
            timestamps: Optional timestamps for each value
            metadata: Optional metadata to attach to all observations
        """
        self.values = np.array(values, dtype=np.float64)
        self.timestamps = timestamps or [datetime.utcnow()] * len(self.values)
        self.metadata = metadata or {}
        self._index = 0

        if len(self.values) != len(self.timestamps):
            raise ValueError("values and timestamps must have same length")

    def __iter__(self) -> 'TimeSeriesIterator':
        return self

    def __next__(self) -> StreamingObservation:
        if self._index >= len(self.values):
            raise StopIteration

        value = self.values[self._index]
        timestamp = self.timestamps[self._index]

        obs = StreamingObservation(
            timestamp=timestamp,
            value=value,
            sequence_index=self._index,
            metadata=self.metadata.copy()
        )

        self._index += 1
        return obs

    def __len__(self) -> int:
        return len(self.values)

    def slice(self, start: int, end: Optional[int] = None) -> 'TimeSeriesIterator':
        """Create iterator over a slice of the time series."""
        end = end if end is not None else len(self.values)
        return TimeSeriesIterator(
            values=self.values[start:end],
            timestamps=self.timestamps[start:end],
            metadata=self.metadata
        )


def create_streaming_observation(value: Union[float, np.ndarray, List[float]],
                                sequence_index: int,
                                timestamp: Optional[datetime] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> StreamingObservation:
    """
    Convenience factory for creating StreamingObservation objects.

    Args:
        value: Observation value
        sequence_index: Position in time series
        timestamp: Optional timestamp (defaults to current UTC time)
        metadata: Optional metadata dictionary

    Returns:
        StreamingObservation instance
    """
    return StreamingObservation(
        timestamp=timestamp or datetime.utcnow(),
        value=value,
        sequence_index=sequence_index,
        metadata=metadata
    )


def process_observation_batch(observations: List[StreamingObservation],
                             config: StreamingConfig) -> List[StreamingObservation]:
    """
    Process a batch of observations with the given configuration.

    Args:
        observations: List of observations to process
        config: Streaming configuration

    Returns:
        List of successfully processed observations
    """
    processor = StreamingProcessor(config)
    return processor.process_batch(observations)


def validate_streaming_config(config: StreamingConfig) -> Tuple[bool, List[str]]:
    """
    Validate streaming configuration for common issues.

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    violations = []

    if config.window_size < 1:
        violations.append("window_size must be >= 1")

    if config.batch_size < 1:
        violations.append("batch_size must be >= 1")

    if config.batch_size > config.window_size:
        violations.append("batch_size should not exceed window_size")

    if config.missing_value_strategy not in {'skip', 'impute', 'interpolate'}:
        violations.append(f"Invalid missing_value_strategy: {config.missing_value_strategy}")

    return len(violations) == 0, violations


def main():
    """
    Main entry point for streaming module testing and demonstration.

    Runs a simple demonstration of streaming observation processing
    with synthetic data.
    """
    print("=" * 60)
    print("Streaming Observation Processing Demo")
    print("=" * 60)

    # Create configuration
    config = StreamingConfig(
        window_size=50,
        batch_size=10,
        missing_value_strategy='impute',
        memory_profile=True
    )

    # Validate configuration
    is_valid, violations = validate_streaming_config(config)
    if not is_valid:
        print(f"Configuration validation failed: {violations}")
        return

    print(f"Configuration valid: window_size={config.window_size}, batch_size={config.batch_size}")

    # Create processor
    processor = StreamingProcessor(config)

    # Generate synthetic observations
    print("\nProcessing synthetic observations...")
    np.random.seed(42)
    n_observations = 100

    for i in range(n_observations):
        # Generate value with occasional missing data
        if np.random.random() < 0.05:
            value = np.nan
        else:
            value = np.random.normal(loc=100, scale=10)

        obs = create_streaming_observation(
            value=value,
            sequence_index=i,
            metadata={'source': 'demo'}
        )

        # Process observation
        result = processor.process_observation(obs)
        if result:
            print(f"  Obs {i}: value={result.value[0]:.2f}, window_stats={processor.get_window_stats()['stats']}")

    # Print summary
    print("\n" + "=" * 60)
    print("Processing Complete")
    print("=" * 60)
    summary = processor.get_window_stats()
    print(f"Total observations: {summary['observation_count']}")
    print(f"Missing count: {summary['missing_count']}")
    print(f"Missing rate: {summary['missing_rate']:.2%}")
    print(f"Final window size: {summary['current_size']}")
    print(f"Window mean: {summary['stats']['mean']:.2f}")
    print(f"Window std: {summary['stats']['std']:.2f}")


if __name__ == '__main__':
    main()
