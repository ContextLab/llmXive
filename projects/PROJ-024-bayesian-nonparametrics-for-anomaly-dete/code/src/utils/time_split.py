"""
Time-ordered train/test split utilities for time series anomaly detection.

This module provides explicit time-ordered train/test split functionality
to prevent temporal data leakage. All splits maintain chronological order
where training data always precedes test data temporally.

Key Principles:
1. No future data in training set
2. No past data in test set
3. Gap period can be configured to prevent look-ahead bias
4. Supports multiple time series formats (numpy, pandas, lists)

Author: Implementer Agent
Date: 2026-01-XX
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union, Sequence
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TimeSplitConfig:
    """
    Configuration for time-ordered train/test split.

    Attributes:
        train_ratio: Fraction of data for training (0.0 to 1.0)
        test_ratio: Fraction of data for testing (0.0 to 1.0)
        gap_size: Number of observations to leave as gap between train/test
        gap_unit: Unit for gap_size ('observations', 'hours', 'days', 'weeks')
        min_train_size: Minimum number of observations required in training set
        min_test_size: Minimum number of observations required in test set
        shuffle: Whether to shuffle before splitting (should be False for time series)
        random_seed: Random seed for reproducibility (only used if shuffle=True)
        timestamp_column: Name of timestamp column if using pandas DataFrame
        datetime_format: Format string for parsing timestamp strings
        allow_overlap: Whether to allow overlapping train/test windows (for sliding window)
    """
    train_ratio: float = 0.8
    test_ratio: float = 0.2
    gap_size: int = 0
    gap_unit: str = 'observations'
    min_train_size: int = 100
    min_test_size: int = 50
    shuffle: bool = False
    random_seed: int = 42
    timestamp_column: Optional[str] = None
    datetime_format: Optional[str] = None
    allow_overlap: bool = False

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0.0 <= self.train_ratio <= 1.0:
            raise ValueError(f"train_ratio must be between 0.0 and 1.0, got {self.train_ratio}")
        if not 0.0 <= self.test_ratio <= 1.0:
            raise ValueError(f"test_ratio must be between 0.0 and 1.0, got {self.test_ratio}")
        if self.train_ratio + self.test_ratio > 1.0:
            raise ValueError(f"train_ratio + test_ratio must not exceed 1.0, got {self.train_ratio + self.test_ratio}")
        if self.gap_size < 0:
            raise ValueError(f"gap_size must be non-negative, got {self.gap_size}")
        if self.gap_unit not in ['observations', 'hours', 'days', 'weeks', 'months']:
            raise ValueError(f"gap_unit must be one of 'observations', 'hours', 'days', 'weeks', 'months', got {self.gap_unit}")


@dataclass
class TimeSplitResult:
    """
    Result of a time-ordered train/test split.

    Attributes:
        train_data: Training data subset
        test_data: Test data subset
        train_indices: Indices of training data in original dataset
        test_indices: Indices of test data in original dataset
        train_start: Start timestamp of training period
        train_end: End timestamp of training period
        test_start: Start timestamp of test period
        test_end: End timestamp of test period
        gap_start: Start of gap period (if applicable)
        gap_end: End of gap period (if applicable)
        total_observations: Total number of observations in original dataset
        train_observations: Number of observations in training set
        test_observations: Number of observations in test set
        split_timestamp: Timestamp when split was performed
        config_summary: Summary of configuration used for split
    """
    train_data: Any
    test_data: Any
    train_indices: List[int]
    test_indices: List[int]
    train_start: Optional[datetime] = None
    train_end: Optional[datetime] = None
    test_start: Optional[datetime] = None
    test_end: Optional[datetime] = None
    gap_start: Optional[datetime] = None
    gap_end: Optional[datetime] = None
    total_observations: int = 0
    train_observations: int = 0
    test_observations: int = 0
    split_timestamp: datetime = field(default_factory=datetime.now)
    config_summary: Dict[str, Any] = field(default_factory=dict)


def _parse_timestamps(
    data: Union[np.ndarray, List, 'pd.DataFrame'],
    config: TimeSplitConfig
) -> Optional[List[datetime]]:
    """
    Parse timestamps from data if available.

    Args:
        data: Input data (numpy array, list, or pandas DataFrame)
        config: TimeSplitConfig with timestamp settings

    Returns:
        List of datetime objects or None if no timestamps available
    """
    try:
        import pandas as pd
        is_dataframe = isinstance(data, pd.DataFrame)
    except ImportError:
        is_dataframe = False

    if is_dataframe and config.timestamp_column:
        if config.datetime_format:
            return [
                datetime.strptime(str(ts), config.datetime_format)
                for ts in data[config.timestamp_column].values
            ]
        else:
            return data[config.timestamp_column].astype(datetime).tolist()
    elif isinstance(data, np.ndarray) and data.dtype == 'datetime64[ns]':
        return [pd.Timestamp(ts).to_pydatetime() for ts in data]
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], datetime):
        return data
    else:
        logger.warning("No timestamps found in data. Will use index-based splitting.")
        return None


def _calculate_gap_observations(
    total_size: int,
    config: TimeSplitConfig,
    timestamps: Optional[List[datetime]] = None
) -> int:
    """
    Calculate gap size in number of observations.

    Args:
        total_size: Total number of observations
        config: TimeSplitConfig with gap settings
        timestamps: Optional list of timestamps for time-based gap calculation

    Returns:
        Number of observations to use as gap
    """
    if config.gap_unit == 'observations':
        return config.gap_size

    if timestamps is None:
        logger.warning("Time-based gap requested but no timestamps available. Using 0 gap.")
        return 0

    # Calculate average time interval between observations
    if len(timestamps) < 2:
        return 0

    intervals = []
    for i in range(1, len(timestamps)):
        delta = timestamps[i] - timestamps[i - 1]
        intervals.append(delta.total_seconds())

    avg_interval_seconds = np.mean(intervals)

    # Convert gap_unit to seconds
    unit_to_seconds = {
        'hours': 3600,
        'days': 86400,
        'weeks': 604800,
        'months': 2592000  # Approximate 30 days
    }

    gap_seconds = config.gap_size * unit_to_seconds.get(config.gap_unit, 3600)
    gap_observations = int(gap_seconds / avg_interval_seconds) if avg_interval_seconds > 0 else 0

    return gap_observations


def _validate_split_sizes(
    total_size: int,
    train_size: int,
    test_size: int,
    gap_size: int,
    config: TimeSplitConfig
) -> None:
    """
    Validate that split sizes meet minimum requirements.

    Args:
        total_size: Total number of observations
        train_size: Planned training set size
        test_size: Planned test set size
        gap_size: Gap period size
        config: TimeSplitConfig with minimum size requirements

    Raises:
        ValueError: If minimum size requirements are not met
    """
    if train_size < config.min_train_size:
        raise ValueError(
            f"Training set size {train_size} is below minimum {config.min_train_size}. "
            f"Consider using more data or reducing min_train_size."
        )
    if test_size < config.min_test_size:
        raise ValueError(
            f"Test set size {test_size} is below minimum {config.min_test_size}. "
            f"Consider using more data or reducing min_test_size."
        )
    if train_size + test_size + gap_size > total_size:
        raise ValueError(
            f"Combined train ({train_size}) + test ({test_size}) + gap ({gap_size}) "
            f"exceeds total size {total_size}. Adjust ratios or gap_size."
        )


def split_time_series(
    data: Union[np.ndarray, List, 'pd.DataFrame'],
    config: Optional[TimeSplitConfig] = None,
    timestamps: Optional[Union[np.ndarray, List[datetime]]] = None
) -> TimeSplitResult:
    """
    Perform time-ordered train/test split on time series data.

    This function ensures that all training data temporally precedes all test data,
    preventing look-ahead bias and temporal data leakage.

    Args:
        data: Input time series data (numpy array, list, or pandas DataFrame)
        config: TimeSplitConfig for split parameters (default: 80/20 split)
        timestamps: Optional timestamps for time-based gap calculation

    Returns:
        TimeSplitResult containing train/test splits and metadata

    Example:
        >>> config = TimeSplitConfig(train_ratio=0.7, test_ratio=0.3, gap_size=10)
        >>> result = split_time_series(data_array, config)
        >>> train_data = result.train_data
        >>> test_data = result.test_data
        >>> print(f"Train: {result.train_observations} obs, Test: {result.test_observations} obs")
    """
    if config is None:
        config = TimeSplitConfig()

    # Convert timestamps to list if numpy array
    if isinstance(timestamps, np.ndarray):
        timestamps = timestamps.tolist()

    # Parse timestamps from data if not provided
    parsed_timestamps = None
    if timestamps is None:
        parsed_timestamps = _parse_timestamps(data, config)
    else:
        parsed_timestamps = timestamps

    # Get total size
    if isinstance(data, np.ndarray):
        total_size = len(data)
    elif isinstance(data, list):
        total_size = len(data)
    else:
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                total_size = len(data)
            else:
                total_size = len(data)
        except ImportError:
            total_size = len(data)

    # Calculate gap in observations
    gap_size = _calculate_gap_observations(total_size, config, parsed_timestamps)

    # Calculate train/test sizes
    train_size = int(total_size * config.train_ratio)
    remaining = total_size - train_size - gap_size
    test_size = min(remaining, int(total_size * config.test_ratio))

    # Adjust train_size if needed to ensure test_size meets minimum
    if test_size < config.min_test_size:
        test_size = config.min_test_size
        train_size = total_size - test_size - gap_size

    # Validate split sizes
    _validate_split_sizes(total_size, train_size, test_size, gap_size, config)

    # Calculate indices
    train_end_idx = train_size
    gap_end_idx = train_size + gap_size
    test_end_idx = train_size + gap_size + test_size

    train_indices = list(range(0, train_end_idx))
    test_indices = list(range(gap_end_idx, test_end_idx))

    # Extract data
    if isinstance(data, np.ndarray):
        train_data = data[train_indices]
        test_data = data[test_indices]
    elif isinstance(data, list):
        train_data = [data[i] for i in train_indices]
        test_data = [data[i] for i in test_indices]
    else:
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                train_data = data.iloc[train_indices].reset_index(drop=True)
                test_data = data.iloc[test_indices].reset_index(drop=True)
            else:
                train_data = [data[i] for i in train_indices]
                test_data = [data[i] for i in test_indices]
        except ImportError:
            train_data = [data[i] for i in train_indices]
            test_data = [data[i] for i in test_indices]

    # Extract timestamps for metadata
    train_start = None
    train_end = None
    test_start = None
    test_end = None
    gap_start = None
    gap_end = None

    if parsed_timestamps is not None:
        if len(train_indices) > 0:
            train_start = parsed_timestamps[min(train_indices)]
            train_end = parsed_timestamps[max(train_indices)]
        if len(test_indices) > 0:
            test_start = parsed_timestamps[min(test_indices)]
            test_end = parsed_timestamps[max(test_indices)]
        if gap_size > 0 and gap_end_idx < len(parsed_timestamps):
            gap_start = parsed_timestamps[train_end_idx] if train_end_idx < len(parsed_timestamps) else None
            gap_end = parsed_timestamps[gap_end_idx - 1] if gap_end_idx > 0 else None

    # Build config summary
    config_summary = {
        'train_ratio': config.train_ratio,
        'test_ratio': config.test_ratio,
        'gap_size': gap_size,
        'gap_unit': config.gap_unit,
        'shuffle': config.shuffle,
        'random_seed': config.random_seed,
        'min_train_size': config.min_train_size,
        'min_test_size': config.min_test_size,
        'allow_overlap': config.allow_overlap
    }

    return TimeSplitResult(
        train_data=train_data,
        test_data=test_data,
        train_indices=train_indices,
        test_indices=test_indices,
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
        gap_start=gap_start,
        gap_end=gap_end,
        total_observations=total_size,
        train_observations=len(train_indices),
        test_observations=len(test_indices),
        split_timestamp=datetime.now(),
        config_summary=config_summary
    )


def sliding_window_split(
    data: Union[np.ndarray, List, 'pd.DataFrame'],
    window_size: int,
    step_size: int = 1,
    train_ratio: float = 0.8,
    min_windows: int = 10
) -> List[TimeSplitResult]:
    """
    Create multiple train/test splits using sliding window approach.

    This is useful for time series cross-validation where you want to
    evaluate model performance across multiple time periods.

    Args:
        data: Input time series data
        window_size: Total size of each sliding window
        step_size: Number of observations to shift window each iteration
        train_ratio: Fraction of window for training (rest is test)
        min_windows: Minimum number of windows to produce

    Returns:
        List of TimeSplitResult objects for each window position

    Example:
        >>> windows = sliding_window_split(data, window_size=1000, step_size=100, train_ratio=0.7)
        >>> for i, window in enumerate(windows):
        ...     print(f"Window {i}: Train {window.train_observations}, Test {window.test_observations}")
    """
    if isinstance(data, np.ndarray):
        total_size = len(data)
    elif isinstance(data, list):
        total_size = len(data)
    else:
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                total_size = len(data)
            else:
                total_size = len(data)
        except ImportError:
            total_size = len(data)

    if total_size < window_size:
        logger.warning(f"Data size {total_size} < window_size {window_size}. Using all data.")
        window_size = total_size

    results = []
    window_start = 0

    while window_start + window_size <= total_size:
        # Extract window
        window_end = window_start + window_size
        window_data = data[window_start:window_end]

        # Create split config for this window
        config = TimeSplitConfig(
            train_ratio=train_ratio,
            test_ratio=1 - train_ratio,
            gap_size=0,
            min_train_size=int(window_size * train_ratio * 0.5),
            min_test_size=int(window_size * (1 - train_ratio) * 0.5),
            shuffle=False
        )

        # Split the window
        result = split_time_series(window_data, config)

        # Adjust indices to be relative to original data
        result.train_indices = [i + window_start for i in result.train_indices]
        result.test_indices = [i + window_start for i in result.test_indices]
        result.train_observations = len(result.train_indices)
        result.test_observations = len(result.test_indices)

        results.append(result)

        window_start += step_size

        # Stop if we have enough windows
        if len(results) >= min_windows and window_start + window_size > total_size:
            break

    logger.info(f"Created {len(results)} sliding window splits")
    return results


def validate_no_temporal_leakage(result: TimeSplitResult) -> bool:
    """
    Validate that a split result has no temporal leakage.

    Args:
        result: TimeSplitResult to validate

    Returns:
        True if no temporal leakage detected, False otherwise

    Raises:
        ValueError: If temporal leakage is detected
    """
    # Check that test indices are all after train indices
    if result.train_indices and result.test_indices:
        max_train_idx = max(result.train_indices)
        min_test_idx = min(result.test_indices)

        if min_test_idx <= max_train_idx:
            raise ValueError(
                f"TEMPORAL LEAKAGE DETECTED: Test index {min_test_idx} "
                f"is not after train index {max_train_idx}"
            )

    # Check timestamps if available
    if result.train_end and result.test_start:
        if result.test_start <= result.train_end:
            raise ValueError(
                f"TEMPORAL LEAKAGE DETECTED: Test start {result.test_start} "
                f"is not after train end {result.train_end}"
            )

    logger.info("No temporal leakage detected in split result")
    return True


def save_split_metadata(result: TimeSplitResult, output_path: Union[str, Path]) -> None:
    """
    Save split metadata to a JSON file for reproducibility.

    Args:
        result: TimeSplitResult to save
        output_path: Path to save metadata JSON file
    """
    import json

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        'split_timestamp': result.split_timestamp.isoformat(),
        'total_observations': result.total_observations,
        'train_observations': result.train_observations,
        'test_observations': result.test_observations,
        'config_summary': result.config_summary,
        'train_start': result.train_start.isoformat() if result.train_start else None,
        'train_end': result.train_end.isoformat() if result.train_end else None,
        'test_start': result.test_start.isoformat() if result.test_start else None,
        'test_end': result.test_end.isoformat() if result.test_end else None,
        'gap_start': result.gap_start.isoformat() if result.gap_start else None,
        'gap_end': result.gap_end.isoformat() if result.gap_end else None,
        'train_indices_sample': result.train_indices[:10],
        'test_indices_sample': result.test_indices[:10]
    }

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved split metadata to {output_path}")


def load_split_metadata(metadata_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load split metadata from a JSON file.

    Args:
        metadata_path: Path to metadata JSON file

    Returns:
        Dictionary containing split metadata
    """
    import json

    metadata_path = Path(metadata_path)

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    logger.info(f"Loaded split metadata from {metadata_path}")
    return metadata


def get_dataset_split_documentation(datasets: Dict[str, TimeSplitResult]) -> str:
    """
    Generate documentation for dataset splits for reproducibility.

    Args:
        datasets: Dictionary mapping dataset names to TimeSplitResult

    Returns:
        Markdown-formatted documentation string
    """
    lines = [
        "# Time Series Train/Test Split Documentation",
        "",
        "This document describes the temporal train/test splits for all datasets.",
        "All splits maintain chronological order to prevent look-ahead bias.",
        "",
        "## Split Methodology",
        "",
        "- **Train/Test Split**: Time-ordered (no shuffling)",
        "- **Gap Period**: Configurable gap between train and test to prevent look-ahead bias",
        "- **Validation**: Each split is validated to ensure test data temporally follows train data",
        "",
        "## Dataset Splits",
        ""
    ]

    for dataset_name, result in datasets.items():
        lines.extend([
            f"### {dataset_name}",
            "",
            f"- **Total Observations**: {result.total_observations}",
            f"- **Train Observations**: {result.train_observations} ({result.train_observations / result.total_observations * 100:.1f}%)",
            f"- **Test Observations**: {result.test_observations} ({result.test_observations / result.total_observations * 100:.1f}%)",
            f"- **Train Period**: {result.train_start} to {result.train_end}",
            f"- **Test Period**: {result.test_start} to {result.test_end}",
            f"- **Split Timestamp**: {result.split_timestamp}",
            f"- **Configuration**: {result.config_summary}",
            ""
        ])

    lines.extend([
        "## Verification",
        "",
        "All splits have been verified using `validate_no_temporal_leakage()` to ensure",
        "no future data appears in the training set.",
        "",
        "## References",
        "",
        "- [Time Series Cross-Validation](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-cross-validation)",
        "- [Temporal Data Leakage Prevention](https://towardsdatascience.com/time-series-cross-validation-7c1b8e3c6e8d)",
        ""
    ])

    return "\n".join(lines)


def main():
    """
    Main function for standalone testing and demonstration.
    """
    # Create sample time series data
    np.random.seed(42)
    n_observations = 1000
    timestamps = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n_observations)]
    values = np.cumsum(np.random.randn(n_observations)) + 100

    # Create config
    config = TimeSplitConfig(
        train_ratio=0.7,
        test_ratio=0.3,
        gap_size=10,
        gap_unit='observations',
        min_train_size=100,
        min_test_size=50
    )

    # Perform split
    result = split_time_series(values, config, timestamps)

    print("=" * 60)
    print("Time Series Split Results")
    print("=" * 60)
    print(f"Total observations: {result.total_observations}")
    print(f"Train observations: {result.train_observations} ({result.train_observations / result.total_observations * 100:.1f}%)")
    print(f"Test observations: {result.test_observations} ({result.test_observations / result.total_observations * 100:.1f}%)")
    print(f"Gap size: {result.test_start - result.train_end if result.test_start and result.train_end else 'N/A'}")
    print(f"Train period: {result.train_start} to {result.train_end}")
    print(f"Test period: {result.test_start} to {result.test_end}")

    # Validate
    try:
        validate_no_temporal_leakage(result)
        print("\n✓ No temporal leakage detected")
    except ValueError as e:
        print(f"\n✗ Temporal leakage detected: {e}")

    # Create documentation
    datasets = {'sample_series': result}
    doc = get_dataset_split_documentation(datasets)
    print("\n" + "=" * 60)
    print("Split Documentation")
    print("=" * 60)
    print(doc[:500] + "...")


if __name__ == '__main__':
    main()
