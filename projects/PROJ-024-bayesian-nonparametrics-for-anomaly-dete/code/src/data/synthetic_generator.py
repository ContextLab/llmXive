"""
Synthetic Timeseries Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for simulation and validation purposes (FR-021, FR-022).
"""
import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    signal_type: Literal['sine', 'random_walk', 'ar1', 'mixed'] = 'mixed'
    length: int = 1000
    noise_level: float = 0.1
    frequency: float = 0.05  # For sine waves
    ar_coefficient: float = 0.9  # For AR(1) process
    seed: Optional[int] = None

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_rate: float = 0.05
    anomaly_types: List[Literal['point', 'contextual', 'collective']] = field(
        default_factory=lambda: ['point', 'contextual', 'collective']
    )
    shift_magnitude: float = 3.0  # Standard deviations for shift
    duration_min: int = 5
    duration_max: int = 20
    seed: Optional[int] = None

@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    timestamps: List[float]
    values: List[float]
    ground_truth: Dict[int, str]  # index -> anomaly_type
    metadata: Dict[str, Any]

def generate_base_signal(config: SignalConfig) -> np.ndarray:
    """Generate base signal according to configuration."""
    if config.seed is not None:
        np.random.seed(config.seed)

    length = config.length
    t = np.arange(length)

    if config.signal_type == 'sine':
        signal = np.sin(2 * np.pi * config.frequency * t)
    elif config.signal_type == 'random_walk':
        signal = np.cumsum(np.random.normal(0, 1, length))
    elif config.signal_type == 'ar1':
        signal = np.zeros(length)
        for i in range(1, length):
            signal[i] = config.ar_coefficient * signal[i-1] + np.random.normal(0, 1)
    elif config.signal_type == 'mixed':
        # Combine sine, trend, and noise
        trend = 0.1 * t
        sine = 0.5 * np.sin(2 * np.pi * config.frequency * t)
        noise = np.random.normal(0, config.noise_level, length)
        signal = trend + sine + noise
    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")

    # Add noise
    signal = signal + np.random.normal(0, config.noise_level, length)

    return signal

def inject_point_anomalies(
    signal: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[int, str]
) -> np.ndarray:
    """Inject point anomalies (single-point spikes)."""
    if config.seed is not None:
        np.random.seed(config.seed)

    n_anomalies = int(len(signal) * config.anomaly_rate * 0.33)  # 1/3 of anomalies
    indices = np.random.choice(len(signal), n_anomalies, replace=False)

    for idx in indices:
        direction = np.random.choice([-1, 1])
        magnitude = config.shift_magnitude * np.std(signal)
        signal[idx] += direction * magnitude
        ground_truth[int(idx)] = 'point'

    return signal

def inject_contextual_anomalies(
    signal: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[int, str]
) -> np.ndarray:
    """Inject contextual anomalies (values anomalous in context)."""
    if config.seed is not None:
        np.random.seed(config.seed)

    n_anomalies = int(len(signal) * config.anomaly_rate * 0.33)
    indices = np.random.choice(len(signal) - 10, n_anomalies, replace=False)

    for idx in indices:
        # Create a value that is normal globally but anomalous locally
        local_mean = np.mean(signal[max(0, idx-5):idx+5])
        local_std = np.std(signal[max(0, idx-5):idx+5])
        anomaly_value = local_mean + np.random.choice([-1, 1]) * 3 * local_std
        signal[idx] = anomaly_value
        ground_truth[int(idx)] = 'contextual'

    return signal

def inject_collective_anomalies(
    signal: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[int, str]
) -> np.ndarray:
    """Inject collective anomalies (sequences of anomalous values)."""
    if config.seed is not None:
        np.random.seed(config.seed)

    n_anomalies = int(len(signal) * config.anomaly_rate * 0.34)  # 1/3 of anomalies

    # Generate collective anomaly segments
    attempts = 0
    while n_anomalies > 0 and attempts < 100:
        start_idx = np.random.randint(0, len(signal) - config.duration_max)
        duration = np.random.randint(config.duration_min, config.duration_max)
        end_idx = min(start_idx + duration, len(signal))

        # Shift the segment
        shift = np.random.choice([-1, 1]) * config.shift_magnitude * np.std(signal)
        signal[start_idx:end_idx] += shift

        # Mark ground truth
        for i in range(start_idx, end_idx):
            ground_truth[int(i)] = 'collective'

        n_anomalies -= 1
        attempts += 1

    return signal

def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: AnomalyConfig
) -> SyntheticDataset:
    """Generate a complete synthetic timeseries with anomalies."""
    logger.info(f"Generating synthetic timeseries: {signal_config.signal_type}, "
               f"length={signal_config.length}, anomaly_rate={anomaly_config.anomaly_rate}")

    # Generate base signal
    signal = generate_base_signal(signal_config)

    # Initialize ground truth
    ground_truth: Dict[int, str] = {}

    # Inject anomalies
    if 'point' in anomaly_config.anomaly_types:
        signal = inject_point_anomalies(signal, anomaly_config, ground_truth)

    if 'contextual' in anomaly_config.anomaly_types:
        signal = inject_contextual_anomalies(signal, anomaly_config, ground_truth)

    if 'collective' in anomaly_config.anomaly_types:
        signal = inject_collective_anomalies(signal, anomaly_config, ground_truth)

    # Create timestamps
    timestamps = list(range(len(signal)))

    metadata = {
        'signal_type': signal_config.signal_type,
        'length': signal_config.length,
        'noise_level': signal_config.noise_level,
        'anomaly_rate': anomaly_config.anomaly_rate,
        'anomaly_count': len(ground_truth),
        'anomaly_types': list(set(ground_truth.values())),
        'seed': signal_config.seed if signal_config.seed else anomaly_config.seed
    }

    return SyntheticDataset(
        timestamps=timestamps,
        values=signal.tolist(),
        ground_truth=ground_truth,
        metadata=metadata
    )

def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """Save synthetic dataset to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'timestamps': dataset.timestamps,
        'values': dataset.values,
        'ground_truth': dataset.ground_truth,
        'metadata': dataset.metadata
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved synthetic dataset to {output_path}")

def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """Load synthetic dataset from JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)

    return SyntheticDataset(
        timestamps=data['timestamps'],
        values=data['values'],
        ground_truth={int(k): v for k, v in data['ground_truth'].items()},
        metadata=data['metadata']
    )

def generate_validation_dataset(
    n_samples: int = 1000,
    anomaly_rate: float = 0.05,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """Generate a validation dataset with known properties."""
    signal_config = SignalConfig(
        signal_type='mixed',
        length=n_samples,
        noise_level=0.1,
        seed=seed
    )

    anomaly_config = AnomalyConfig(
        anomaly_rate=anomaly_rate,
        seed=seed
    )

    return generate_synthetic_timeseries(signal_config, anomaly_config)

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic timeseries for anomaly detection research'
    )
    parser.add_argument('--n-samples', type=int, default=1000,
                      help='Number of samples to generate')
    parser.add_argument('--anomaly-rate', type=float, default=0.05,
                      help='Anomaly rate (0.0 to 1.0)')
    parser.add_argument('--signal-type', type=str,
                      choices=['sine', 'random_walk', 'ar1', 'mixed'],
                      default='mixed',
                      help='Type of base signal')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_dataset.json',
                      help='Output file path')

    args = parser.parse_args()

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate dataset
    signal_config = SignalConfig(
        signal_type=args.signal_type,
        length=args.n_samples,
        seed=args.seed
    )

    anomaly_config = AnomalyConfig(
        anomaly_rate=args.anomaly_rate,
        seed=args.seed
    )

    dataset = generate_synthetic_timeseries(signal_config, anomaly_config)

    # Save dataset
    save_synthetic_dataset(dataset, args.output)

    # Log summary
    logger.info(f"Generated dataset with {len(dataset.values)} samples")
    logger.info(f"Anomaly count: {len(dataset.ground_truth)}")
    logger.info(f"Anomaly types: {list(set(dataset.ground_truth.values()))}")
    logger.info(f"Output saved to: {args.output}")

if __name__ == '__main__':
    main()