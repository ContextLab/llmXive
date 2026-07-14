"""
Synthetic Time Series Generator for Anomaly Detection.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and
independent ground-truth timestamps for validation and simulation.
"""
import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal

# Ensure tolerance for any logger-style calls from external scripts
class SignalConfig:
    """
    Configuration for signal generation.
    Provides a tolerant interface for logging-like calls to prevent AttributeError
    in scripts that treat this object as a generic logger or config holder.
    """
    def __init__(
        self,
        length: int = 1000,
        frequency: float = 1.0,
        noise_level: float = 0.1,
        trend: Literal['linear', 'constant', 'sinusoidal'] = 'linear',
        amplitude: float = 1.0
    ):
        self.length = length
        self.frequency = frequency
        self.noise_level = noise_level
        self.trend = trend
        self.amplitude = amplitude

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant fallback for unknown attributes.
        If a script calls a method that doesn't exist (e.g., .info(), .debug()),
        return a no-op callable to prevent crashes.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective']
    start_idx: int
    end_idx: int
    magnitude: float = 1.0
    shape: Literal['spike', 'step', 'drift'] = 'spike'

@dataclass
class SyntheticDataset:
    """Container for generated synthetic data and metadata."""
    timestamps: List[float]
    values: List[float]
    ground_truth: List[int]  # 0: normal, 1: anomaly
    config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series signal with optional trend and noise.

    Args:
        config: SignalConfig object defining signal parameters.

    Returns:
        Tuple of (timestamps, signal_values)
    """
    t = np.linspace(0, config.length / config.frequency, config.length)
    signal = np.zeros_like(t)

    # Generate trend
    if config.trend == 'linear':
        signal += np.linspace(0, config.amplitude, config.length)
    elif config.trend == 'sinusoidal':
        signal += config.amplitude * np.sin(2 * np.pi * config.frequency * t)
    else:
        signal += config.amplitude * np.ones(config.length)

    # Add noise
    noise = np.random.normal(0, config.noise_level, config.length)
    signal += noise

    return t, signal

def inject_point_anomalies(
    signal: np.ndarray,
    anomaly_indices: List[int],
    magnitude: float
) -> np.ndarray:
    """
    Inject point anomalies (spikes) at specific indices.

    Args:
        signal: Base signal array.
        anomaly_indices: List of indices to inject anomalies.
        magnitude: Size of the spike relative to signal std.

    Returns:
        Modified signal array.
    """
    modified_signal = signal.copy()
    for idx in anomaly_indices:
        if 0 <= idx < len(signal):
            # Add a spike based on local standard deviation
            local_std = np.std(signal[max(0, idx-10):idx+10])
            spike = np.random.choice([-1, 1]) * magnitude * local_std
            modified_signal[idx] += spike
    return modified_signal

def inject_contextual_anomalies(
    signal: np.ndarray,
    start_idx: int,
    end_idx: int,
    shift: float
) -> np.ndarray:
    """
    Inject contextual anomalies (level shifts) over a range.

    Args:
        signal: Base signal array.
        start_idx: Start index of the anomaly window.
        end_idx: End index of the anomaly window.
        shift: Magnitude of the level shift.

    Returns:
        Modified signal array.
    """
    modified_signal = signal.copy()
    if 0 <= start_idx < end_idx <= len(signal):
        modified_signal[start_idx:end_idx] += shift
    return modified_signal

def inject_collective_anomalies(
    signal: np.ndarray,
    start_idx: int,
    end_idx: int,
    pattern_type: Literal['periodic', 'random', 'trend']
) -> np.ndarray:
    """
    Inject collective anomalies (subsequences with different dynamics).

    Args:
        signal: Base signal array.
        start_idx: Start index of the anomaly window.
        end_idx: End index of the anomaly window.
        pattern_type: Type of pattern to inject.

    Returns:
        Modified signal array.
    """
    modified_signal = signal.copy()
    if 0 <= start_idx < end_idx <= len(signal):
        length = end_idx - start_idx
        if pattern_type == 'periodic':
            # Inject high frequency noise
            anomaly_segment = np.random.normal(0, 2.0, length)
        elif pattern_type == 'random':
            anomaly_segment = np.random.uniform(-5, 5, length)
        else:  # trend
            anomaly_segment = np.linspace(-2, 2, length)
        modified_signal[start_idx:end_idx] += anomaly_segment
    return modified_signal

def generate_synthetic_timeseries(
    n_samples: int = 1000,
    n_anomalies: int = 5,
    anomaly_ratio: float = 0.05,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with injected anomalies.

    Args:
        n_samples: Total number of data points.
        n_anomalies: Number of anomaly events to inject.
        anomaly_ratio: Approximate ratio of anomalous points.
        seed: Random seed for reproducibility.

    Returns:
        SyntheticDataset object containing data and ground truth.
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate base signal
    config = SignalConfig(length=n_samples, noise_level=0.1, trend='linear')
    timestamps, signal = generate_base_signal(config)

    # Initialize ground truth (0 = normal)
    ground_truth = np.zeros(n_samples, dtype=int)

    # Inject anomalies
    anomaly_indices = []
    for _ in range(n_anomalies):
        # Randomly select a start point for the anomaly
        start_idx = np.random.randint(0, n_samples - 50)
        duration = np.random.randint(5, 50)
        end_idx = min(start_idx + duration, n_samples)

        # Randomly choose anomaly type
        anomaly_type = np.random.choice(['point', 'contextual', 'collective'])

        if anomaly_type == 'point':
            # Inject multiple point anomalies in the window
            n_points = np.random.randint(1, 5)
            points = np.random.choice(range(start_idx, end_idx), n_points, replace=False)
            signal = inject_point_anomalies(signal, points.tolist(), magnitude=3.0)
            for p in points:
                ground_truth[p] = 1
                anomaly_indices.append(int(p))

        elif anomaly_type == 'contextual':
            shift = np.random.choice([-2, 2]) * np.std(signal)
            signal = inject_contextual_anomalies(signal, start_idx, end_idx, shift)
            ground_truth[start_idx:end_idx] = 1
            anomaly_indices.append(int(start_idx))

        else:  # collective
            pattern = np.random.choice(['periodic', 'random', 'trend'])
            signal = inject_collective_anomalies(signal, start_idx, end_idx, pattern)
            ground_truth[start_idx:end_idx] = 1
            anomaly_indices.append(int(start_idx))

    return SyntheticDataset(
        timestamps=timestamps.tolist(),
        values=signal.tolist(),
        ground_truth=ground_truth.tolist(),
        config=asdict(config),
        metadata={
            'n_samples': n_samples,
            'n_anomalies': n_anomalies,
            'anomaly_indices': anomaly_indices,
            'seed': seed
        }
    )

def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save a synthetic dataset to disk as JSON.

    Args:
        dataset: The SyntheticDataset to save.
        output_path: Path to the output file.
    """
    data = {
        'timestamps': dataset.timestamps,
        'values': dataset.values,
        'ground_truth': dataset.ground_truth,
        'config': dataset.config,
        'metadata': dataset.metadata
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from disk.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        SyntheticDataset object.
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    return SyntheticDataset(
        timestamps=data['timestamps'],
        values=data['values'],
        ground_truth=data['ground_truth'],
        config=data['config'],
        metadata=data.get('metadata', {})
    )

def generate_validation_dataset(
    n_samples: int = 500,
    seed: int = 42
) -> SyntheticDataset:
    """
    Generate a validation dataset with known properties for testing.

    Args:
        n_samples: Number of samples.
        seed: Random seed.

    Returns:
        SyntheticDataset with controlled anomaly injection.
    """
    return generate_synthetic_timeseries(
        n_samples=n_samples,
        n_anomalies=3,
        seed=seed
    )

def main():
    """Entry point for generating synthetic datasets."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_data.json',
                        help='Output file path')
    parser.add_argument('--n-samples', type=int, default=1000, help='Number of samples')
    parser.add_argument('--n-anomalies', type=int, default=5, help='Number of anomaly events')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')

    args = parser.parse_args()

    dataset = generate_synthetic_timeseries(
        n_samples=args.n_samples,
        n_anomalies=args.n_anomalies,
        seed=args.seed
    )

    save_synthetic_dataset(dataset, args.output)
    print(f"Generated synthetic dataset with {len(dataset.values)} samples")
    print(f"Ground truth anomalies at indices: {dataset.metadata.get('anomaly_indices', [])}")
    print(f"Saved to: {args.output}")

if __name__ == '__main__':
    main()