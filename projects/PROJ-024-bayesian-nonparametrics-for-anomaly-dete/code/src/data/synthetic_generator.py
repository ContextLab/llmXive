"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for validation and simulation studies.

This module supports:
- Point anomalies (single spike/drop)
- Contextual anomalies (values anomalous in context)
- Collective anomalies (sequence of anomalous behavior)

Per FR-021 and FR-022, ground-truth timestamps are injected independently.
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal


@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    n_samples: int = 1000
    frequency: float = 1.0  # cycles per sample unit
    amplitude: float = 1.0
    noise_std: float = 0.1
    trend_slope: float = 0.0
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Logger-like methods to satisfy flexible call sites
    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'point'
    anomaly_start: Optional[int] = None
    anomaly_end: Optional[int] = None
    magnitude: float = 3.0  # Standard deviations for point anomalies
    duration: int = 10  # For collective anomalies
    count: int = 1  # Number of point anomalies
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Logger-like methods to satisfy flexible call sites
    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    signal: np.ndarray
    ground_truth: Dict[str, Any]
    config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            'signal': self.signal.tolist(),
            'ground_truth': self.ground_truth,
            'config': self.config,
            'metadata': self.metadata
        }


def generate_base_signal(config: SignalConfig) -> np.ndarray:
    """
    Generate a base time series signal with optional trend and noise.

    Args:
        config: SignalConfig with parameters for generation.

    Returns:
        1D numpy array of signal values.
    """
    if config.seed is not None:
        np.random.seed(config.seed)

    t = np.arange(config.n_samples)
    # Base sinusoidal signal
    signal = config.amplitude * np.sin(2 * np.pi * config.frequency * t / config.n_samples)
    # Add trend
    signal += config.trend_slope * t
    # Add noise
    noise = np.random.normal(0, config.noise_std, config.n_samples)
    signal += noise

    return signal


def inject_point_anomalies(
    signal: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject point anomalies (single spikes or drops) into the signal.

    Args:
        signal: Base signal array.
        config: AnomalyConfig with magnitude and count.
        ground_truth: Dict to update with anomaly timestamps.

    Returns:
        Tuple of (modified signal, updated ground_truth).
    """
    n_samples = len(signal)
    # Randomly select indices for anomalies
    available_indices = list(range(10, n_samples - 10))  # Avoid edges
    anomaly_indices = np.random.choice(available_indices, size=config.count, replace=False)
    anomaly_indices = sorted(anomaly_indices)

    for idx in anomaly_indices:
        direction = np.random.choice([-1, 1])
        signal[idx] += direction * config.magnitude * np.std(signal)

    # Record ground truth
    if 'anomalies' not in ground_truth:
        ground_truth['anomalies'] = []
    for idx in anomaly_indices:
        ground_truth['anomalies'].append({
            'type': 'point',
            'index': int(idx),
            'magnitude': float(config.magnitude * np.std(signal)),
            'direction': int(direction)
        })

    return signal, ground_truth


def inject_contextual_anomalies(
    signal: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject contextual anomalies (values anomalous in local context).

    Args:
        signal: Base signal array.
        config: AnomalyConfig with start/end or duration.
        ground_truth: Dict to update with anomaly timestamps.

    Returns:
        Tuple of (modified signal, updated ground_truth).
    """
    n_samples = len(signal)

    # Determine anomaly region
    if config.anomaly_start is not None and config.anomaly_end is not None:
        start, end = config.anomaly_start, config.anomaly_end
    elif config.duration is not None:
        start = np.random.randint(10, n_samples - config.duration - 10)
        end = start + config.duration
    else:
        start = int(n_samples * 0.4)
        end = int(n_samples * 0.6)

    # Inject values that are normal globally but anomalous locally
    # e.g., flat line in a varying signal, or high frequency in low frequency region
    local_mean = np.mean(signal[start:end])
    local_std = np.std(signal[start:end])

    # Create a flat segment (contextual anomaly if original was varying)
    signal[start:end] = local_mean + np.random.normal(0, local_std * 0.1, end - start)

    if 'anomalies' not in ground_truth:
        ground_truth['anomalies'] = []
    ground_truth['anomalies'].append({
        'type': 'contextual',
        'start_index': int(start),
        'end_index': int(end),
        'duration': int(end - start)
    })

    return signal, ground_truth


def inject_collective_anomalies(
    signal: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject collective anomalies (sequence of anomalous behavior).

    Args:
        signal: Base signal array.
        config: AnomalyConfig with duration.
        ground_truth: Dict to update with anomaly timestamps.

    Returns:
        Tuple of (modified signal, updated ground_truth).
    """
    n_samples = len(signal)

    # Determine anomaly region
    if config.anomaly_start is not None and config.anomaly_end is not None:
        start, end = config.anomaly_start, config.anomaly_end
    elif config.duration is not None:
        start = np.random.randint(10, n_samples - config.duration - 10)
        end = start + config.duration
    else:
        start = int(n_samples * 0.3)
        end = start + 50

    # Inject a different pattern (e.g., higher frequency or different amplitude)
    t_local = np.arange(end - start)
    new_pattern = config.magnitude * np.sin(2 * np.pi * 3 * t_local / (end - start))
    signal[start:end] += new_pattern

    if 'anomalies' not in ground_truth:
        ground_truth['anomalies'] = []
    ground_truth['anomalies'].append({
        'type': 'collective',
        'start_index': int(start),
        'end_index': int(end),
        'duration': int(end - start),
        'pattern': 'higher_frequency'
    })

    return signal, ground_truth


def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: Optional[AnomalyConfig] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic dataset with optional anomalies.

    Args:
        signal_config: Configuration for base signal.
        anomaly_config: Configuration for anomaly injection (optional).

    Returns:
        SyntheticDataset containing signal and ground truth.
    """
    # Generate base signal
    signal = generate_base_signal(signal_config)

    # Initialize ground truth
    ground_truth = {
        'anomalies': [],
        'n_samples': signal_config.n_samples,
        'injected': False
    }

    # Inject anomalies if configured
    if anomaly_config is not None:
        if anomaly_config.anomaly_type == 'point':
            signal, ground_truth = inject_point_anomalies(signal, anomaly_config, ground_truth)
        elif anomaly_config.anomaly_type == 'contextual':
            signal, ground_truth = inject_contextual_anomalies(signal, anomaly_config, ground_truth)
        elif anomaly_config.anomaly_type == 'collective':
            signal, ground_truth = inject_collective_anomalies(signal, anomaly_config, ground_truth)
        ground_truth['injected'] = True

    # Prepare config dict
    config_dict = {
        'signal': asdict(signal_config),
        'anomaly': asdict(anomaly_config) if anomaly_config else None
    }

    metadata = {
        'generated_at': str(np.datetime64('now')),
        'seed': signal_config.seed
    }

    return SyntheticDataset(
        signal=signal,
        ground_truth=ground_truth,
        config=config_dict,
        metadata=metadata
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save a synthetic dataset to a JSON file.

    Args:
        dataset: SyntheticDataset to save.
        output_path: Path to output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = dataset.to_dict()
    # Convert numpy arrays to lists for JSON serialization
    data['signal'] = data['signal'].tolist() if isinstance(data['signal'], np.ndarray) else data['signal']

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from a JSON file.

    Args:
        input_path: Path to input file.

    Returns:
        Loaded SyntheticDataset.
    """
    with open(input_path, 'r') as f:
        data = json.load(f)

    return SyntheticDataset(
        signal=np.array(data['signal']),
        ground_truth=data['ground_truth'],
        config=data['config'],
        metadata=data.get('metadata', {})
    )


def generate_validation_dataset(seed: int = 42) -> SyntheticDataset:
    """
    Generate a standard validation dataset for testing.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        SyntheticDataset with known anomaly locations.
    """
    signal_config = SignalConfig(
        n_samples=1000,
        frequency=1.0,
        amplitude=1.0,
        noise_std=0.1,
        seed=seed
    )

    anomaly_config = AnomalyConfig(
        anomaly_type='point',
        count=5,
        magnitude=4.0,
        seed=seed
    )

    return generate_synthetic_timeseries(signal_config, anomaly_config)


def main():
    """
    Main entry point for CLI execution.

    Generates a synthetic dataset and saves it to disk.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate synthetic time series data for anomaly detection research.'
    )
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_dataset.json',
                        help='Output path for the generated dataset.')
    parser.add_argument('--n-samples', type=int, default=1000,
                        help='Number of samples in the time series.')
    parser.add_argument('--anomaly-type', type=str, choices=['point', 'contextual', 'collective'],
                        default='point', help='Type of anomaly to inject.')
    parser.add_argument('--anomaly-start', type=int, default=None,
                        help='Start index for anomaly injection.')
    parser.add_argument('--anomaly-end', type=int, default=None,
                        help='End index for anomaly injection.')
    parser.add_argument('--magnitude', type=float, default=3.0,
                        help='Magnitude of anomaly (in std devs).')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility.')

    args = parser.parse_args()

    # Create config objects
    signal_config = SignalConfig(
        n_samples=args.n_samples,
        seed=args.seed
    )

    anomaly_config = AnomalyConfig(
        anomaly_type=args.anomaly_type,
        anomaly_start=args.anomaly_start,
        anomaly_end=args.anomaly_end,
        magnitude=args.magnitude,
        seed=args.seed
    )

    # Generate dataset
    print(f"Generating synthetic dataset with {args.n_samples} samples...")
    dataset = generate_synthetic_timeseries(signal_config, anomaly_config)

    # Save dataset
    save_synthetic_dataset(dataset, args.output)
    print(f"Dataset saved to: {args.output}")
    print(f"Ground truth: {dataset.ground_truth}")


if __name__ == '__main__':
    main()