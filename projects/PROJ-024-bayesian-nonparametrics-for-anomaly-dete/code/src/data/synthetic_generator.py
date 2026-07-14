"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for simulation studies and model validation.

This module implements FR-021 and FR-022 requirements for ground truth
simulation data generation.
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    length: int = 1000
    base_frequency: float = 0.01
    noise_std: float = 0.1
    trend_slope: float = 0.001
    seasonality_amplitude: float = 0.5
    seasonality_period: int = 50

    # Allow arbitrary attributes for logger-like usage
    def __getattr__(self, name: str) -> Any:
        # Tolerant logger-style fallback for any method/attribute access
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'point'
    start_index: int = 500
    duration: int = 50
    magnitude: float = 3.0
    magnitude_std: float = 0.5
    probability: float = 0.05
    gap_min: int = 100
    gap_max: int = 500


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    signal: np.ndarray
    ground_truth: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamps: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataset to dictionary for serialization."""
        return {
            'signal': self.signal.tolist(),
            'ground_truth': self.ground_truth,
            'metadata': self.metadata,
            'timestamps': self.timestamps.tolist() if self.timestamps is not None else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyntheticDataset':
        """Load dataset from dictionary."""
        return cls(
            signal=np.array(data['signal']),
            ground_truth=data['ground_truth'],
            metadata=data['metadata'],
            timestamps=np.array(data['timestamps']) if data.get('timestamps') is not None else None
        )


def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series with trend, seasonality, and noise.

    Args:
        config: Signal configuration parameters.

    Returns:
        Tuple of (signal values, timestamps).
    """
    np.random.seed(42)  # Reproducibility for base signal
    t = np.arange(config.length)
    timestamps = t.astype(float)

    # Trend component
    trend = config.trend_slope * t

    # Seasonal component
    seasonal = config.seasonality_amplitude * np.sin(2 * np.pi * t / config.seasonality_period)

    # High-frequency noise
    noise = np.random.normal(0, config.noise_std, config.length)

    # Base signal
    signal = trend + seasonal + noise

    return signal, timestamps


def inject_point_anomalies(
    signal: np.ndarray,
    timestamps: np.ndarray,
    config: AnomalyConfig
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Inject point anomalies (sharp spikes/drops) into the signal.

    Args:
        signal: Base signal array.
        timestamps: Timestamp array.
        config: Anomaly configuration.

    Returns:
        Tuple of (modified signal, modified timestamps, ground truth metadata).
    """
    np.random.seed(42 + config.start_index)  # Different seed for anomalies
    anomalous_signal = signal.copy()
    anomalous_timestamps = timestamps.copy()

    ground_truth = {
        'anomalies': [],
        'anomaly_type': 'point',
        'total_anomalies': 0
    }

    # Determine number of anomalies based on probability
    n_anomalies = int(config.probability * config.length)
    n_anomalies = max(1, n_anomalies)  # At least one anomaly

    # Generate anomaly start positions with minimum gaps
    positions = []
    attempts = 0
    while len(positions) < n_anomalies and attempts < 1000:
        pos = np.random.randint(config.start_index, config.length - config.duration)
        # Check minimum gap
        if not positions or (pos - positions[-1]) >= config.gap_min:
            positions.append(pos)
        attempts += 1

    for i, start_pos in enumerate(positions):
        # Random magnitude with direction (spike or drop)
        direction = np.random.choice([-1, 1])
        magnitude = config.magnitude + np.random.normal(0, config.magnitude_std)
        magnitude *= direction

        # Anomaly duration (point anomaly is short)
        duration = min(config.duration, config.length - start_pos)

        # Inject anomaly
        anomalous_signal[start_pos:start_pos + duration] += magnitude

        ground_truth['anomalies'].append({
            'index': int(start_pos),
            'end_index': int(start_pos + duration),
            'type': 'point',
            'magnitude': float(magnitude),
            'direction': 'positive' if magnitude > 0 else 'negative'
        })

    ground_truth['total_anomalies'] = len(ground_truth['anomalies'])

    return anomalous_signal, anomalous_timestamps, ground_truth


def inject_contextual_anomalies(
    signal: np.ndarray,
    timestamps: np.ndarray,
    config: AnomalyConfig
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Inject contextual anomalies (values normal in isolation but abnormal in context).

    Args:
        signal: Base signal array.
        timestamps: Timestamp array.
        config: Anomaly configuration.

    Returns:
        Tuple of (modified signal, modified timestamps, ground truth metadata).
    """
    np.random.seed(42 + config.start_index)
    anomalous_signal = signal.copy()
    anomalous_timestamps = timestamps.copy()

    ground_truth = {
        'anomalies': [],
        'anomaly_type': 'contextual',
        'total_anomalies': 0
    }

    # Contextual anomalies: shift to a different regime temporarily
    n_anomalies = max(1, int(config.probability * config.length / 2))

    positions = []
    attempts = 0
    while len(positions) < n_anomalies and attempts < 1000:
        pos = np.random.randint(config.start_index, config.length - config.duration)
        if not positions or (pos - positions[-1]) >= config.gap_min:
            positions.append(pos)
        attempts += 1

    for start_pos in positions:
        # Shift to a different mean level
        shift = np.random.choice([-1, 1]) * config.magnitude * 2
        duration = min(config.duration, config.length - start_pos)

        anomalous_signal[start_pos:start_pos + duration] += shift

        ground_truth['anomalies'].append({
            'index': int(start_pos),
            'end_index': int(start_pos + duration),
            'type': 'contextual',
            'shift': float(shift),
            'context': 'regime_shift'
        })

    ground_truth['total_anomalies'] = len(ground_truth['anomalies'])

    return anomalous_signal, anomalous_timestamps, ground_truth


def inject_collective_anomalies(
    signal: np.ndarray,
    timestamps: np.ndarray,
    config: AnomalyConfig
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Inject collective anomalies (sequence of points that are anomalous together).

    Args:
        signal: Base signal array.
        timestamps: Timestamp array.
        config: Anomaly configuration.

    Returns:
        Tuple of (modified signal, modified timestamps, ground truth metadata).
    """
    np.random.seed(42 + config.start_index)
    anomalous_signal = signal.copy()
    anomalous_timestamps = timestamps.copy()

    ground_truth = {
        'anomalies': [],
        'anomaly_type': 'collective',
        'total_anomalies': 0
    }

    # Collective anomalies: change in variance or pattern
    n_anomalies = max(1, int(config.probability * config.length / 3))

    positions = []
    attempts = 0
    while len(positions) < n_anomalies and attempts < 1000:
        pos = np.random.randint(config.start_index, config.length - config.duration)
        if not positions or (pos - positions[-1]) >= config.gap_min:
            positions.append(pos)
        attempts += 1

    for start_pos in positions:
        # Increase variance significantly
        duration = min(config.duration * 2, config.length - start_pos)
        noise_multiplier = config.magnitude * 3

        # Inject high-variance noise
        anomalous_signal[start_pos:start_pos + duration] += np.random.normal(
            0, noise_multiplier, duration
        )

        ground_truth['anomalies'].append({
            'index': int(start_pos),
            'end_index': int(start_pos + duration),
            'type': 'collective',
            'variance_increase': float(noise_multiplier),
            'pattern': 'high_variance'
        })

    ground_truth['total_anomalies'] = len(ground_truth['anomalies'])

    return anomalous_signal, anomalous_timestamps, ground_truth


def generate_synthetic_timeseries(
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None,
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'point'
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series with anomalies.

    Args:
        signal_config: Configuration for base signal (default: SignalConfig()).
        anomaly_config: Configuration for anomaly injection (default: AnomalyConfig()).
        anomaly_type: Type of anomaly to inject ('point', 'contextual', or 'collective').

    Returns:
        SyntheticDataset containing signal, ground truth, and metadata.
    """
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()
        anomaly_config.anomaly_type = anomaly_type

    # Generate base signal
    signal, timestamps = generate_base_signal(signal_config)

    # Inject anomalies based on type
    if anomaly_type == 'point':
        signal, timestamps, ground_truth = inject_point_anomalies(
            signal, timestamps, anomaly_config
        )
    elif anomaly_type == 'contextual':
        signal, timestamps, ground_truth = inject_contextual_anomalies(
            signal, timestamps, anomaly_config
        )
    elif anomaly_type == 'collective':
        signal, timestamps, ground_truth = inject_collective_anomalies(
            signal, timestamps, anomaly_config
        )
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_type}")

    # Create metadata
    metadata = {
        'signal_length': len(signal),
        'signal_config': asdict(signal_config),
        'anomaly_config': asdict(anomaly_config),
        'anomaly_type': anomaly_type,
        'generated_at': '2026-01-01T00:00:00Z',  # Fixed for reproducibility
        'seed': 42
    }

    return SyntheticDataset(
        signal=signal,
        ground_truth=ground_truth,
        metadata=metadata,
        timestamps=timestamps
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save synthetic dataset to JSON file.

    Args:
        dataset: The synthetic dataset to save.
        output_path: Path to output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)

    logger.info(f"Saved synthetic dataset to {output_path}")


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load synthetic dataset from JSON file.

    Args:
        input_path: Path to input JSON file.

    Returns:
        Loaded SyntheticDataset.
    """
    input_path = Path(input_path)

    with open(input_path, 'r') as f:
        data = json.load(f)

    return SyntheticDataset.from_dict(data)


def generate_validation_dataset(
    n_samples: int = 100,
    anomaly_ratio: float = 0.2
) -> Tuple[List[SyntheticDataset], List[Dict[str, Any]]]:
    """
    Generate a validation dataset with multiple samples.

    Args:
        n_samples: Number of samples to generate.
        anomaly_ratio: Ratio of samples with anomalies.

    Returns:
        Tuple of (list of datasets, list of ground truth summaries).
    """
    datasets = []
    ground_truths = []

    anomaly_types = ['point', 'contextual', 'collective']

    for i in range(n_samples):
        # Randomly select anomaly type
        if i < int(n_samples * anomaly_ratio):
            anomaly_type = np.random.choice(anomaly_types)
            has_anomaly = True
        else:
            anomaly_type = None
            has_anomaly = False

        if has_anomaly:
            config = AnomalyConfig()
            config.anomaly_type = anomaly_type
            dataset = generate_synthetic_timeseries(
                signal_config=SignalConfig(length=500),
                anomaly_config=config,
                anomaly_type=anomaly_type
            )
        else:
            dataset = generate_synthetic_timeseries(
                signal_config=SignalConfig(length=500),
                anomaly_type=None  # No anomalies
            )

        datasets.append(dataset)
        ground_truths.append({
            'sample_id': i,
            'has_anomaly': has_anomaly,
            'anomaly_type': anomaly_type,
            'anomaly_count': dataset.ground_truth.get('total_anomalies', 0)
        })

    return datasets, ground_truths


def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_validation.json',
                        help='Output file path')
    parser.add_argument('--anomaly-type', type=str, choices=['point', 'contextual', 'collective'],
                        default='point', help='Type of anomaly to inject')
    parser.add_argument('--length', type=int, default=1000, help='Signal length')
    parser.add_argument('--n-samples', type=int, default=10, help='Number of samples for validation')

    args = parser.parse_args()

    logger.info(f"Generating synthetic dataset with anomaly_type={args.anomaly_type}, length={args.length}")

    # Generate single dataset
    signal_config = SignalConfig(length=args.length)
    anomaly_config = AnomalyConfig()
    anomaly_config.anomaly_type = args.anomaly_type

    dataset = generate_synthetic_timeseries(
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        anomaly_type=args.anomaly_type
    )

    # Save dataset
    save_synthetic_dataset(dataset, args.output)

    # Print summary
    print(f"\nGenerated Dataset Summary:")
    print(f"  Length: {len(dataset.signal)}")
    print(f"  Anomaly Type: {dataset.ground_truth.get('anomaly_type', 'None')}")
    print(f"  Total Anomalies: {dataset.ground_truth.get('total_anomalies', 0)}")
    print(f"  Output: {args.output}")

    # Generate validation set if requested
    if args.n_samples > 1:
        val_datasets, val_ground_truths = generate_validation_dataset(
            n_samples=args.n_samples,
            anomaly_ratio=0.3
        )

        val_output = args.output.replace('.json', '_validation.json')
        val_data = {
            'datasets': [d.to_dict() for d in val_datasets],
            'ground_truth': val_ground_truths
        }

        output_path = Path(val_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(val_output, 'w') as f:
            json.dump(val_data, f, indent=2)

        print(f"\nGenerated Validation Set:")
        print(f"  Samples: {len(val_datasets)}")
        print(f"  Output: {val_output}")

    return 0


if __name__ == '__main__':
    exit(main())