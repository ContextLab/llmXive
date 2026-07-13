"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for validation of the DP-GMM anomaly detection pipeline.

This module supports:
- Base signal generation (Sine, Random Walk, AR(1), Mixed)
- Injection of Point, Contextual, and Collective anomalies
- Deterministic seeding for reproducibility
- Ground-truth timestamp tracking
"""
import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_rate: float = 0.05
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'point'
    magnitude: float = 3.0  # Standard deviations from mean
    duration: int = 10     # For collective anomalies
    seed: Optional[int] = None

@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    signal_type: Literal['sine', 'random_walk', 'ar1', 'mixed'] = 'mixed'
    length: int = 1000
    frequency: float = 0.1
    noise_std: float = 0.1
    drift: float = 0.0
    seed: Optional[int] = None

@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    timestamps: List[int]
    values: List[float]
    ground_truth_anomalies: List[Dict[str, Any]]
    config: Dict[str, Any]
    signal_config: Dict[str, Any]
    anomaly_config: Dict[str, Any]

def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, List[int]]:
    """
    Generate a base time series signal.

    Args:
        config: Signal configuration parameters.

    Returns:
        Tuple of (signal values, timestamps).
    """
    if config.seed is not None:
        np.random.seed(config.seed)

    t = np.arange(config.length)
    signal = np.zeros(config.length)

    if config.signal_type == 'sine':
        signal = np.sin(2 * np.pi * config.frequency * t)
    elif config.signal_type == 'random_walk':
        signal = np.cumsum(np.random.normal(0, config.noise_std, config.length))
    elif config.signal_type == 'ar1':
        # AR(1) process: x_t = phi * x_{t-1} + epsilon
        phi = 0.9
        signal[0] = np.random.normal(0, config.noise_std)
        for i in range(1, config.length):
            signal[i] = phi * signal[i-1] + np.random.normal(0, config.noise_std)
    elif config.signal_type == 'mixed':
        # Combination of sine and random walk
        sine_component = np.sin(2 * np.pi * config.frequency * t)
        rw_component = np.cumsum(np.random.normal(0, config.noise_std * 0.5, config.length))
        signal = 0.7 * sine_component + 0.3 * rw_component
    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")

    # Add drift
    if config.drift != 0:
        signal += config.drift * t

    # Add noise
    signal += np.random.normal(0, config.noise_std, config.length)

    return signal, t.tolist()

def inject_point_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    timestamps: List[int]
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject point anomalies (abrupt shifts at specific points).

    Args:
        values: Base signal values.
        anomaly_config: Anomaly configuration.
        timestamps: Timestamps corresponding to values.

    Returns:
        Tuple of (modified values, list of ground truth anomaly records).
    """
    if anomaly_config.seed is not None:
        np.random.seed(anomaly_config.seed)

    n_anomalies = int(len(values) * anomaly_config.anomaly_rate)
    if n_anomalies == 0:
        return values, []

    # Select random indices for anomalies (avoiding boundaries)
    anomaly_indices = np.random.choice(
        range(10, len(values) - 10),
        size=n_anomalies,
        replace=False
    )

    ground_truth = []
    for idx in anomaly_indices:
        # Determine direction of shift
        direction = np.random.choice([-1, 1])
        shift = direction * anomaly_config.magnitude * np.std(values)
        values[idx] += shift

        ground_truth.append({
            'start_index': int(idx),
            'end_index': int(idx),
            'type': 'point',
            'magnitude': float(shift),
            'timestamp': timestamps[idx]
        })

    return values, ground_truth

def inject_contextual_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    timestamps: List[int]
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous in context).
    For simplicity, we use high-frequency oscillations in a smooth segment.

    Args:
        values: Base signal values.
        anomaly_config: Anomaly configuration.
        timestamps: Timestamps corresponding to values.

    Returns:
        Tuple of (modified values, list of ground truth anomaly records).
    """
    if anomaly_config.seed is not None:
        np.random.seed(anomaly_config.seed)

    n_anomalies = int(len(values) * anomaly_config.anomaly_rate)
    if n_anomalies == 0:
        return values, []

    # Select random start indices for contextual anomalies
    anomaly_starts = np.random.choice(
        range(10, len(values) - 20),
        size=n_anomalies,
        replace=False
    )

    ground_truth = []
    for start_idx in anomaly_starts:
        # Inject high-frequency noise in a local window
        window_size = 5
        noise = np.random.normal(0, anomaly_config.magnitude * np.std(values), window_size)
        values[start_idx:start_idx + window_size] += noise

        ground_truth.append({
            'start_index': int(start_idx),
            'end_index': int(start_idx + window_size - 1),
            'type': 'contextual',
            'magnitude': float(anomaly_config.magnitude * np.std(values)),
            'timestamp': timestamps[start_idx]
        })

    return values, ground_truth

def inject_collective_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    timestamps: List[int]
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject collective anomalies (a sequence of points that are anomalous together).

    Args:
        values: Base signal values.
        anomaly_config: Anomaly configuration.
        timestamps: Timestamps corresponding to values.

    Returns:
        Tuple of (modified values, list of ground truth anomaly records).
    """
    if anomaly_config.seed is not None:
        np.random.seed(anomaly_config.seed)

    n_anomalies = int(len(values) * anomaly_config.anomaly_rate / anomaly_config.duration)
    if n_anomalies == 0:
        return values, []

    # Select random start indices for collective anomalies
    available_starts = len(values) - anomaly_config.duration - 10
    if available_starts <= 0:
        return values, []

    anomaly_starts = np.random.choice(
        range(10, available_starts),
        size=min(n_anomalies, available_starts // 2),
        replace=False
    )

    ground_truth = []
    for start_idx in anomaly_starts:
        end_idx = start_idx + anomaly_config.duration
        # Shift the entire segment
        shift = anomaly_config.magnitude * np.std(values) * np.random.choice([-1, 1])
        values[start_idx:end_idx] += shift

        ground_truth.append({
            'start_index': int(start_idx),
            'end_index': int(end_idx - 1),
            'type': 'collective',
            'magnitude': float(shift),
            'timestamp': timestamps[start_idx]
        })

    return values, ground_truth

def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: AnomalyConfig
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series with anomalies.

    Args:
        signal_config: Configuration for base signal.
        anomaly_config: Configuration for anomaly injection.

    Returns:
        SyntheticDataset containing values, timestamps, and ground truth.
    """
    logger.info(f"Generating base signal: {signal_config.signal_type}, length={signal_config.length}")
    values, timestamps = generate_base_signal(signal_config)

    logger.info(f"Injecting {anomaly_config.anomaly_type} anomalies at rate {anomaly_config.anomaly_rate}")

    if anomaly_config.anomaly_type == 'point':
        values, ground_truth = inject_point_anomalies(values, anomaly_config, timestamps)
    elif anomaly_config.anomaly_type == 'contextual':
        values, ground_truth = inject_contextual_anomalies(values, anomaly_config, timestamps)
    elif anomaly_config.anomaly_type == 'collective':
        values, ground_truth = inject_collective_anomalies(values, anomaly_config, timestamps)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Prepare config dicts for storage
    dataset_config = {
        'signal_config': asdict(signal_config),
        'anomaly_config': asdict(anomaly_config),
        'generated_at': str(np.datetime64('now'))
    }

    return SyntheticDataset(
        timestamps=timestamps,
        values=values.tolist(),
        ground_truth_anomalies=ground_truth,
        config=dataset_config,
        signal_config=asdict(signal_config),
        anomaly_config=asdict(anomaly_config)
    )

def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save synthetic dataset to JSON file.

    Args:
        dataset: The synthetic dataset to save.
        output_path: Path to the output file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'timestamps': dataset.timestamps,
        'values': dataset.values,
        'ground_truth': dataset.ground_truth_anomalies,
        'config': dataset.config
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved synthetic dataset to {output_path}")

def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load synthetic dataset from JSON file.

    Args:
        input_path: Path to the input file.

    Returns:
        Loaded SyntheticDataset.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_path}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    return SyntheticDataset(
        timestamps=data['timestamps'],
        values=data['values'],
        ground_truth_anomalies=data['ground_truth'],
        config=data['config'],
        signal_config=data['config']['signal_config'],
        anomaly_config=data['config']['anomaly_config']
    )

def generate_validation_dataset(
    n_samples: int = 1000,
    anomaly_rate: float = 0.05,
    signal_type: str = 'mixed',
    seed: int = 42
) -> SyntheticDataset:
    """
    Generate a validation dataset with specific parameters.

    Args:
        n_samples: Number of samples.
        anomaly_rate: Rate of anomalies.
        signal_type: Type of base signal.
        seed: Random seed.

    Returns:
        SyntheticDataset for validation.
    """
    signal_config = SignalConfig(
        length=n_samples,
        signal_type=signal_type,
        seed=seed
    )
    anomaly_config = AnomalyConfig(
        anomaly_rate=anomaly_rate,
        anomaly_type='point',
        seed=seed + 1  # Different seed for anomaly injection
    )

    return generate_synthetic_timeseries(signal_config, anomaly_config)

def main():
    """
    Command-line entry point for generating synthetic datasets.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate synthetic time series data for anomaly detection research.'
    )
    parser.add_argument(
        '--n_samples',
        type=int,
        default=1000,
        help='Number of samples to generate'
    )
    parser.add_argument(
        '--anomaly_rate',
        type=float,
        default=0.05,
        help='Rate of anomalies to inject (0.0 to 1.0)'
    )
    parser.add_argument(
        '--signal_type',
        type=str,
        choices=['sine', 'random_walk', 'ar1', 'mixed'],
        default='mixed',
        help='Type of base signal to generate'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/results/synthetic_dataset.json',
        help='Output file path'
    )

    args = parser.parse_args()

    # Validate anomaly rate
    if not 0.0 <= args.anomaly_rate <= 1.0:
        parser.error("anomaly_rate must be between 0.0 and 1.0")

    logger.info(f"Generating synthetic dataset with {args.n_samples} samples")
    logger.info(f"Signal type: {args.signal_type}")
    logger.info(f"Anomaly rate: {args.anomaly_rate}")
    logger.info(f"Seed: {args.seed}")

    # Generate dataset
    dataset = generate_validation_dataset(
        n_samples=args.n_samples,
        anomaly_rate=args.anomaly_rate,
        signal_type=args.signal_type,
        seed=args.seed
    )

    # Save dataset
    save_synthetic_dataset(dataset, args.output)

    # Log summary
    logger.info(f"Generated {len(dataset.ground_truth_anomalies)} anomalies")
    logger.info(f"Anomaly types: {set(a['type'] for a in dataset.ground_truth_anomalies)}")

    # Verify output exists
    output_path = Path(args.output)
    if output_path.exists():
        logger.info(f"Verification: Output file created at {args.output} ({output_path.stat().st_size} bytes)")
    else:
        logger.error(f"Verification failed: Output file not found at {args.output}")
        sys.exit(1)

    return dataset

if __name__ == '__main__':
    main()