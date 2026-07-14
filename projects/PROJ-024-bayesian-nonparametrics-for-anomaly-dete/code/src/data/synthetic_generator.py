"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with:
1. Pre-anomaly dynamics (stable regime)
2. Abrupt regime shifts (anomalies)
3. Independent ground-truth timestamps

This module is used for simulation studies (T018) and as a fallback
if real-world data acquisition fails.
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field, dataclass
from typing import Tuple, Dict, List, Optional, Any, Literal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SignalConfig:
    """Configuration for signal generation."""
    # Signal parameters
    base_frequency: float = 1.0
    amplitude: float = 1.0
    noise_std: float = 0.1
    trend_slope: float = 0.0

    # Anomaly parameters
    anomaly_amplitude_factor: float = 3.0  # Multiplier for anomaly magnitude
    anomaly_duration_min: int = 5
    anomaly_duration_max: int = 20

    # Random seed for reproducibility
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Tolerant logger interface to handle various caller expectations
    def info(self, *args, **kwargs):
        logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        logger.debug(*args, **kwargs)

    def warning(self, *args, **kwargs):
        logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        logger.error(*args, **kwargs)


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_rate: float = 0.05  # Expected proportion of anomalous points
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'collective'
    min_gap: int = 10  # Minimum gap between anomaly events
    max_anomalies: Optional[int] = None  # Cap total number of anomalies

    # Ground truth tracking
    record_ground_truth: bool = True


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    timestamps: np.ndarray
    values: np.ndarray
    ground_truth: Dict[str, Any]
    config: Dict[str, Any]

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamps': self.timestamps.tolist(),
            'values': self.values.tolist(),
            'ground_truth': {
                'anomaly_start_indices': self.ground_truth['anomaly_start_indices'].tolist(),
                'anomaly_end_indices': self.ground_truth['anomaly_end_indices'].tolist(),
                'anomaly_labels': self.ground_truth['anomaly_labels'].tolist(),
                'anomaly_type': self.ground_truth['anomaly_type']
            },
            'config': self.config
        }


def generate_base_signal(config: SignalConfig, length: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series with pre-anomaly dynamics.

    Creates a signal with:
    - Sinusoidal component
    - Optional linear trend
    - Gaussian noise

    Args:
        config: Signal configuration
        length: Number of time steps

    Returns:
        Tuple of (timestamps, values)
    """
    if config.seed is not None:
        np.random.seed(config.seed)

    t = np.arange(length)
    timestamps = t.astype(float)

    # Base sinusoidal signal
    signal = config.amplitude * np.sin(2 * np.pi * config.base_frequency * t / length * 10)

    # Add trend
    signal += config.trend_slope * t

    # Add noise
    noise = np.random.normal(0, config.noise_std, length)
    signal += noise

    return timestamps, signal


def inject_point_anomalies(values: np.ndarray, config: AnomalyConfig,
                           ground_truth: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject point anomalies (sudden spikes/drops).

    Args:
        values: Original signal values
        config: Anomaly configuration
        ground_truth: Dictionary to record ground truth

    Returns:
        Modified values and updated ground truth
    """
    length = len(values)
    num_anomalies = max(1, int(length * config.anomaly_rate))

    if config.max_anomalies:
        num_anomalies = min(num_anomalies, config.max_anomalies)

    # Select random indices for point anomalies
    available_indices = list(range(5, length - 5))  # Avoid edges
    anomaly_indices = np.random.choice(available_indices, size=num_anomalies, replace=False)

    for idx in anomaly_indices:
        # Randomly choose spike or drop
        direction = np.random.choice([-1, 1])
        magnitude = config.anomaly_amplitude_factor * np.std(values)
        values[idx] += direction * magnitude

    # Update ground truth
    if config.record_ground_truth:
        ground_truth['anomaly_start_indices'].extend([int(idx) for idx in anomaly_indices])
        ground_truth['anomaly_end_indices'].extend([int(idx) for idx in anomaly_indices])
        ground_truth['anomaly_labels'].extend([1] * len(anomaly_indices))

    return values, ground_truth


def inject_contextual_anomalies(values: np.ndarray, config: AnomalyConfig,
                                ground_truth: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous in context).

    For this implementation, we shift a segment to a different regime temporarily.
    """
    length = len(values)
    num_events = max(1, int(length * config.anomaly_rate / 5))  # Fewer but longer events

    if config.max_anomalies:
        num_events = min(num_events, config.max_anomalies)

    anomaly_starts = []
    anomaly_ends = []

    for _ in range(num_events):
        # Ensure minimum gap
        if len(anomaly_starts) > 0:
            min_start = anomaly_ends[-1] + config.min_gap
        else:
            min_start = 5

        if min_start >= length - 10:
            break

        start = np.random.randint(min_start, length - 10)
        duration = np.random.randint(config.anomaly_duration_min, config.anomaly_duration_max + 1)
        end = min(start + duration, length - 1)

        # Shift the segment to a different level
        shift_amount = config.anomaly_amplitude_factor * np.std(values)
        values[start:end] += shift_amount

        anomaly_starts.append(start)
        anomaly_ends.append(end)

    # Update ground truth
    if config.record_ground_truth:
        ground_truth['anomaly_start_indices'].extend([int(s) for s in anomaly_starts])
        ground_truth['anomaly_end_indices'].extend([int(e) for e in anomaly_ends])
        ground_truth['anomaly_labels'].extend([1] * len(anomaly_starts))

    return values, ground_truth


def inject_collective_anomalies(values: np.ndarray, config: AnomalyConfig,
                                ground_truth: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject collective anomalies (sequence of points that are anomalous as a group).

    This simulates abrupt regime shifts where the statistical properties change.
    """
    length = len(values)
    num_events = max(1, int(length * config.anomaly_rate / 10))

    if config.max_anomalies:
        num_events = min(num_events, config.max_anomalies)

    anomaly_starts = []
    anomaly_ends = []

    for _ in range(num_events):
        # Ensure minimum gap
        if len(anomaly_starts) > 0:
            min_start = anomaly_ends[-1] + config.min_gap
        else:
            min_start = 10

        if min_start >= length - 15:
            break

        start = np.random.randint(min_start, length - 15)
        duration = np.random.randint(config.anomaly_duration_min * 2, config.anomaly_duration_max * 2 + 1)
        end = min(start + duration, length - 1)

        # Create a regime shift: change mean and variance
        segment = values[start:end]
        new_mean = np.mean(segment) + config.anomaly_amplitude_factor * np.std(values)
        new_std = np.std(segment) * 1.5

        # Generate new regime values
        new_segment = np.random.normal(new_mean, new_std, end - start)
        values[start:end] = new_segment

        anomaly_starts.append(start)
        anomaly_ends.append(end)

    # Update ground truth
    if config.record_ground_truth:
        ground_truth['anomaly_start_indices'].extend([int(s) for s in anomaly_starts])
        ground_truth['anomaly_end_indices'].extend([int(e) for e in anomaly_ends])
        ground_truth['anomaly_labels'].extend([1] * len(anomaly_starts))

    return values, ground_truth


def generate_synthetic_timeseries(config: SignalConfig, anomaly_config: AnomalyConfig,
                                  length: int = 1000) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with anomalies.

    Args:
        config: Signal configuration
        anomaly_config: Anomaly configuration
        length: Total length of the time series

    Returns:
        SyntheticDataset with values and ground truth
    """
    # Generate base signal
    timestamps, values = generate_base_signal(config, length)

    # Initialize ground truth
    ground_truth = {
        'anomaly_start_indices': [],
        'anomaly_end_indices': [],
        'anomaly_labels': np.zeros(length, dtype=int),
        'anomaly_type': anomaly_config.anomaly_type
    }

    # Inject anomalies based on type
    if anomaly_config.anomaly_type == 'point':
        values, ground_truth = inject_point_anomalies(values, anomaly_config, ground_truth)
    elif anomaly_config.anomaly_type == 'contextual':
        values, ground_truth = inject_contextual_anomalies(values, anomaly_config, ground_truth)
    elif anomaly_config.anomaly_type == 'collective':
        values, ground_truth = inject_collective_anomalies(values, anomaly_config, ground_truth)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Create labels array
    for start, end in zip(ground_truth['anomaly_start_indices'], ground_truth['anomaly_end_indices']):
        ground_truth['anomaly_labels'][start:end+1] = 1

    # Convert ground truth arrays to lists for JSON serialization
    gt_labels = ground_truth.pop('anomaly_labels')
    ground_truth['anomaly_labels'] = gt_labels.tolist()

    return SyntheticDataset(
        timestamps=timestamps,
        values=values,
        ground_truth=ground_truth,
        config={
            'signal': asdict(config),
            'anomaly': asdict(anomaly_config),
            'length': length
        }
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save synthetic dataset to CSV and JSON metadata files.

    Args:
        dataset: The synthetic dataset to save
        output_path: Path to save the files (without extension)
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV data
    csv_path = f"{output_path}.csv"
    with open(csv_path, 'w') as f:
        f.write("timestamp,value,anomaly_label\n")
        for ts, val, label in zip(dataset.timestamps, dataset.values, dataset.ground_truth['anomaly_labels']):
            f.write(f"{ts},{val},{label}\n")

    # Save metadata as JSON
    # Convert numpy types to Python native types for JSON serialization
    metadata = {
        'timestamps': dataset.timestamps.tolist(),
        'values': dataset.values.tolist(),
        'ground_truth': {
            'anomaly_start_indices': [int(x) for x in dataset.ground_truth['anomaly_start_indices']],
            'anomaly_end_indices': [int(x) for x in dataset.ground_truth['anomaly_end_indices']],
            'anomaly_labels': [int(x) for x in dataset.ground_truth['anomaly_labels']],
            'anomaly_type': dataset.ground_truth['anomaly_type']
        },
        'config': {
            'signal': {
                'base_frequency': float(dataset.config['signal']['base_frequency']),
                'amplitude': float(dataset.config['signal']['amplitude']),
                'noise_std': float(dataset.config['signal']['noise_std']),
                'trend_slope': float(dataset.config['signal']['trend_slope']),
                'anomaly_amplitude_factor': float(dataset.config['signal']['anomaly_amplitude_factor']),
                'anomaly_duration_min': int(dataset.config['signal']['anomaly_duration_min']),
                'anomaly_duration_max': int(dataset.config['signal']['anomaly_duration_max']),
                'seed': dataset.config['signal']['seed']
            },
            'anomaly': {
                'anomaly_rate': float(dataset.config['anomaly']['anomaly_rate']),
                'anomaly_type': dataset.config['anomaly']['anomaly_type'],
                'min_gap': int(dataset.config['anomaly']['min_gap']),
                'max_anomalies': dataset.config['anomaly']['max_anomalies'],
                'record_ground_truth': dataset.config['anomaly']['record_ground_truth']
            },
            'length': int(dataset.config['length'])
        }
    }

    json_path = f"{output_path}.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved synthetic dataset to {csv_path} and {json_path}")


def load_synthetic_dataset(csv_path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from CSV file.

    Args:
        csv_path: Path to the CSV file

    Returns:
        SyntheticDataset
    """
    import pandas as pd
    df = pd.read_csv(csv_path)

    timestamps = df['timestamp'].values
    values = df['value'].values
    labels = df['anomaly_label'].values

    # Find anomaly ranges
    anomaly_indices = np.where(labels == 1)[0]
    if len(anomaly_indices) == 0:
        start_indices = []
        end_indices = []
    else:
        # Group consecutive indices
        diff = np.diff(anomaly_indices)
        split_idx = np.where(diff > 1)[0] + 1
        groups = np.split(anomaly_indices, split_idx)
        start_indices = [g[0] for g in groups]
        end_indices = [g[-1] for g in groups]

    ground_truth = {
        'anomaly_start_indices': start_indices,
        'anomaly_end_indices': end_indices,
        'anomaly_labels': labels.tolist(),
        'anomaly_type': 'unknown'
    }

    return SyntheticDataset(
        timestamps=timestamps,
        values=values,
        ground_truth=ground_truth,
        config={}
    )


def generate_validation_dataset(seed: int = 42, length: int = 1000,
                                anomaly_rate: float = 0.05) -> SyntheticDataset:
    """
    Generate a validation dataset with known properties for testing.

    Args:
        seed: Random seed
        length: Dataset length
        anomaly_rate: Expected anomaly rate

    Returns:
        SyntheticDataset
    """
    signal_config = SignalConfig(
        base_frequency=1.0,
        amplitude=1.0,
        noise_std=0.1,
        seed=seed
    )

    anomaly_config = AnomalyConfig(
        anomaly_rate=anomaly_rate,
        anomaly_type='collective',
        min_gap=10,
        record_ground_truth=True
    )

    return generate_synthetic_timeseries(signal_config, anomaly_config, length)


def main():
    """Main entry point for CLI execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--length', type=int, default=1000, help='Length of time series')
    parser.add_argument('--anomaly-rate', type=float, default=0.05, help='Anomaly rate')
    parser.add_argument('--anomaly-type', type=str, default='collective',
                        choices=['point', 'contextual', 'collective'],
                        help='Type of anomaly to inject')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_data',
                        help='Output path (without extension)')

    args = parser.parse_args()

    logger.info(f"Generating synthetic dataset with seed={args.seed}, "
                f"length={args.length}, anomaly_rate={args.anomaly_rate}")

    signal_config = SignalConfig(seed=args.seed)
    anomaly_config = AnomalyConfig(
        anomaly_rate=args.anomaly_rate,
        anomaly_type=args.anomaly_type,
        min_gap=10,
        record_ground_truth=True
    )

    dataset = generate_synthetic_timeseries(signal_config, anomaly_config, args.length)
    save_synthetic_dataset(dataset, args.output)

    # Print summary
    num_anomalies = sum(dataset.ground_truth['anomaly_labels'])
    logger.info(f"Generated {len(dataset.values)} points with {num_anomalies} anomalous points "
                f"({100*num_anomalies/len(dataset.values):.2f}%)")


if __name__ == '__main__':
    main()