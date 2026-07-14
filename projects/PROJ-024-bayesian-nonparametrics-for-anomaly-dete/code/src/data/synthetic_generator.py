"""
Synthetic Time-Series Generator for Anomaly Detection

Generates datasets with:
- Pre-anomaly dynamics (stable regimes)
- Abrupt shifts (regime changes)
- Independent ground-truth timestamps for validation

This module is used for simulation studies (Phase 0) and as a fallback
data source if real-world data acquisition fails.
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SignalConfig:
    """Configuration for signal generation parameters."""
    # Signal characteristics
    base_frequency: float = 1.0  # Hz
    amplitude: float = 1.0
    noise_std: float = 0.1
    sampling_rate: int = 100  # Hz
    duration_seconds: float = 60.0  # Total duration

    # Trend options: 'none', 'linear', 'sinusoidal'
    trend_type: Literal['none', 'linear', 'sinusoidal'] = 'none'
    trend_magnitude: float = 0.1

    # Logger compatibility (tolerant interface)
    def __getattr__(self, name: str) -> Any:
        # Tolerate unknown logger-style calls
        def _noop(*args, **kwargs) -> None:
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection parameters."""
    # Anomaly types: 'point', 'contextual', 'collective'
    anomaly_types: List[Literal['point', 'contextual', 'collective']] = field(
        default_factory=lambda: ['point', 'collective']
    )

    # Injection probabilities
    point_anomaly_prob: float = 0.02
    contextual_anomaly_prob: float = 0.05
    collective_anomaly_prob: float = 0.01

    # Collective anomaly parameters
    collective_duration_min: int = 10
    collective_duration_max: int = 50
    collective_magnitude_multiplier: float = 3.0

    # Point anomaly magnitude (standard deviations)
    point_magnitude: float = 5.0

    # Contextual anomaly parameters
    contextual_threshold: float = 2.0  # Standard deviations

    # Logger compatibility (tolerant interface)
    def __getattr__(self, name: str) -> Any:
        # Tolerate unknown logger-style calls
        def _noop(*args, **kwargs) -> None:
            return None
        return _noop


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    timestamps: np.ndarray
    signal: np.ndarray
    ground_truth: np.ndarray  # Binary mask: 1=anomaly, 0=normal
    metadata: Dict[str, Any]
    anomaly_indices: List[int]  # Indices where anomalies occur

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamps': self.timestamps.tolist(),
            'signal': self.signal.tolist(),
            'ground_truth': self.ground_truth.tolist(),
            'metadata': self.metadata,
            'anomaly_indices': self.anomaly_indices
        }


def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time-series signal with configurable characteristics.

    Args:
        config: SignalConfig with signal parameters

    Returns:
        Tuple of (timestamps, signal_values)
    """
    n_samples = int(config.duration_seconds * config.sampling_rate)
    timestamps = np.linspace(
        0, config.duration_seconds, n_samples, endpoint=False
    )

    # Base sinusoidal component
    signal = config.amplitude * np.sin(2 * np.pi * config.base_frequency * timestamps)

    # Add trend if specified
    if config.trend_type == 'linear':
        trend = config.trend_magnitude * timestamps
        signal += trend
    elif config.trend_type == 'sinusoidal':
        trend = config.trend_magnitude * np.sin(2 * np.pi * 0.1 * timestamps)
        signal += trend

    # Add Gaussian noise
    noise = np.random.normal(0, config.noise_std, n_samples)
    signal += noise

    return timestamps, signal


def inject_point_anomalies(
    timestamps: np.ndarray,
    signal: np.ndarray,
    anomaly_config: AnomalyConfig,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Inject point anomalies (single-point spikes).

    Args:
        timestamps: Array of timestamps
        signal: Original signal values
        anomaly_config: Configuration for anomaly injection
        rng: NumPy random generator for reproducibility

    Returns:
        Tuple of (modified_signal, ground_truth_mask)
    """
    n_samples = len(signal)
    ground_truth = np.zeros(n_samples, dtype=int)

    # Determine number of point anomalies
    n_anomalies = int(n_samples * anomaly_config.point_anomaly_prob)

    # Randomly select indices for anomalies
    anomaly_indices = rng.choice(
        n_samples, size=n_anomalies, replace=False
    )

    # Inject anomalies with specified magnitude
    for idx in anomaly_indices:
        # Random direction (positive or negative)
        direction = rng.choice([-1, 1])
        magnitude = anomaly_config.point_magnitude * anomaly_config.noise_std
        signal[idx] += direction * magnitude
        ground_truth[idx] = 1

    return signal, ground_truth


def inject_collective_anomalies(
    timestamps: np.ndarray,
    signal: np.ndarray,
    anomaly_config: AnomalyConfig,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Inject collective anomalies (sustained regime shifts).

    Args:
        timestamps: Array of timestamps
        signal: Original signal values
        anomaly_config: Configuration for anomaly injection
        rng: NumPy random generator for reproducibility

    Returns:
        Tuple of (modified_signal, ground_truth_mask)
    """
    n_samples = len(signal)
    ground_truth = np.zeros(n_samples, dtype=int)
    used_indices = set()

    # Determine number of collective anomalies
    n_anomalies = int(n_samples * anomaly_config.collective_anomaly_prob)

    attempts = 0
    while len(used_indices) < n_anomalies and attempts < n_anomalies * 10:
        attempts += 1

        # Random start position
        max_start = n_samples - anomaly_config.collective_duration_max
        if max_start <= 0:
            break

        start_idx = rng.integers(0, max_start)

        # Random duration
        duration = rng.integers(
            anomaly_config.collective_duration_min,
            anomaly_config.collective_duration_max + 1
        )

        end_idx = min(start_idx + duration, n_samples)

        # Check for overlap
        indices = set(range(start_idx, end_idx))
        if indices & used_indices:
            continue

        # Inject regime shift
        shift_magnitude = anomaly_config.collective_magnitude_multiplier * np.std(signal)
        direction = rng.choice([-1, 1])
        signal[start_idx:end_idx] += direction * shift_magnitude

        ground_truth[start_idx:end_idx] = 1
        used_indices.update(indices)

    return signal, ground_truth


def inject_contextual_anomalies(
    timestamps: np.ndarray,
    signal: np.ndarray,
    anomaly_config: AnomalyConfig,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous in context).

    For this implementation, we use high-frequency oscillations that deviate
    from the expected smooth trend.

    Args:
        timestamps: Array of timestamps
        signal: Original signal values
        anomaly_config: Configuration for anomaly injection
        rng: NumPy random generator for reproducibility

    Returns:
        Tuple of (modified_signal, ground_truth_mask)
    """
    n_samples = len(signal)
    ground_truth = np.zeros(n_samples, dtype=int)

    # Determine number of contextual anomaly segments
    n_segments = int(n_samples * anomaly_config.contextual_anomaly_prob / 10)

    for _ in range(n_segments):
        # Random start position
        max_start = n_samples - 20
        if max_start <= 0:
            break

        start_idx = rng.integers(0, max_start)
        duration = rng.integers(5, 20)
        end_idx = min(start_idx + duration, n_samples)

        # Inject high-frequency noise
        local_freq = rng.uniform(5, 10)  # Higher frequency
        local_amp = rng.uniform(1.5, 3.0) * anomaly_config.noise_std
        local_signal = local_amp * np.sin(2 * np.pi * local_freq * timestamps[start_idx:end_idx])

        signal[start_idx:end_idx] += local_signal
        ground_truth[start_idx:end_idx] = 1

    return signal, ground_truth


def generate_synthetic_timeseries(
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time-series dataset with anomalies.

    Args:
        signal_config: Configuration for signal generation
        anomaly_config: Configuration for anomaly injection
        seed: Random seed for reproducibility

    Returns:
        SyntheticDataset containing signal, timestamps, ground truth, and metadata
    """
    # Set defaults if not provided
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()

    # Initialize random generator
    rng = np.random.default_rng(seed)

    # Generate base signal
    timestamps, signal = generate_base_signal(signal_config)

    # Initialize ground truth
    ground_truth = np.zeros(len(signal), dtype=int)

    # Inject anomalies based on configuration
    if 'point' in anomaly_config.anomaly_types:
        signal, point_gt = inject_point_anomalies(
            timestamps, signal, anomaly_config, rng
        )
        ground_truth |= point_gt

    if 'collective' in anomaly_config.anomaly_types:
        signal, collective_gt = inject_collective_anomalies(
            timestamps, signal, anomaly_config, rng
        )
        ground_truth |= collective_gt

    if 'contextual' in anomaly_config.anomaly_types:
        signal, contextual_gt = inject_contextual_anomalies(
            timestamps, signal, anomaly_config, rng
        )
        ground_truth |= contextual_gt

    # Extract anomaly indices
    anomaly_indices = np.where(ground_truth == 1)[0].tolist()

    # Build metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'seed': seed,
        'signal_config': asdict(signal_config),
        'anomaly_config': asdict(anomaly_config),
        'n_samples': len(signal),
        'n_anomalies': int(np.sum(ground_truth)),
        'anomaly_rate': float(np.mean(ground_truth)),
        'sampling_rate': signal_config.sampling_rate,
        'duration_seconds': signal_config.duration_seconds
    }

    return SyntheticDataset(
        timestamps=timestamps,
        signal=signal,
        ground_truth=ground_truth,
        metadata=metadata,
        anomaly_indices=anomaly_indices
    )


def save_synthetic_dataset(
    dataset: SyntheticDataset,
    output_path: str,
    format: Literal['json', 'csv'] = 'json'
) -> Path:
    """
    Save synthetic dataset to disk.

    Args:
        dataset: SyntheticDataset to save
        output_path: Path to save file
        format: Output format ('json' or 'csv')

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == 'json':
        data = dataset.to_dict()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    elif format == 'csv':
        import pandas as pd
        df = pd.DataFrame({
            'timestamp': dataset.timestamps,
            'signal': dataset.signal,
            'ground_truth': dataset.ground_truth
        })
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info(f"Saved synthetic dataset to {output_path}")
    return output_path


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load synthetic dataset from disk.

    Args:
        input_path: Path to load file

    Returns:
        Loaded SyntheticDataset
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_path}")

    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            data = json.load(f)

        return SyntheticDataset(
            timestamps=np.array(data['timestamps']),
            signal=np.array(data['signal']),
            ground_truth=np.array(data['ground_truth']),
            metadata=data['metadata'],
            anomaly_indices=data['anomaly_indices']
        )
    elif input_path.suffix == '.csv':
        import pandas as pd
        df = pd.read_csv(input_path)

        # Infer metadata if not present
        metadata = {
            'n_samples': len(df),
            'anomaly_rate': float(df['ground_truth'].mean())
        }

        return SyntheticDataset(
            timestamps=df['timestamp'].values,
            signal=df['signal'].values,
            ground_truth=df['ground_truth'].values.astype(int),
            metadata=metadata,
            anomaly_indices=df[df['ground_truth'] == 1].index.tolist()
        )
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")


def generate_validation_dataset(
    n_samples: int = 1000,
    anomaly_rate: float = 0.05,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a validation dataset with controlled anomaly rate.

    Args:
        n_samples: Number of samples to generate
        anomaly_rate: Target anomaly rate (0-1)
        seed: Random seed for reproducibility

    Returns:
        SyntheticDataset with controlled anomaly characteristics
    """
    rng = np.random.default_rng(seed)

    # Generate timestamps
    timestamps = np.linspace(0, n_samples / 100.0, n_samples)

    # Generate base signal (simple sinusoidal + noise)
    signal = np.sin(2 * np.pi * timestamps) + rng.normal(0, 0.1, n_samples)

    # Create ground truth with controlled rate
    ground_truth = np.zeros(n_samples, dtype=int)
    n_anomalies = int(n_samples * anomaly_rate)
    anomaly_indices = rng.choice(n_samples, size=n_anomalies, replace=False)
    ground_truth[anomaly_indices] = 1

    # Inject anomalies
    for idx in anomaly_indices:
        direction = rng.choice([-1, 1])
        signal[idx] += direction * 5.0  # Large spike

    metadata = {
        'generated_at': datetime.now().isoformat(),
        'seed': seed,
        'n_samples': n_samples,
        'n_anomalies': n_anomalies,
        'anomaly_rate': anomaly_rate,
        'purpose': 'validation'
    }

    return SyntheticDataset(
        timestamps=timestamps,
        signal=signal,
        ground_truth=ground_truth,
        metadata=metadata,
        anomaly_indices=anomaly_indices.tolist()
    )


def main():
    """
    Main entry point for generating synthetic datasets.
    Creates sample datasets for testing and validation.
    """
    logger.info("Starting synthetic dataset generation...")

    # Create output directory
    output_dir = Path("data/processed/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate default dataset
    logger.info("Generating default synthetic dataset...")
    dataset = generate_synthetic_timeseries(
        seed=42,
        signal_config=SignalConfig(
            duration_seconds=10.0,
            sampling_rate=100,
            base_frequency=1.0,
            amplitude=1.0,
            noise_std=0.1
        ),
        anomaly_config=AnomalyConfig(
            point_anomaly_prob=0.02,
            collective_anomaly_prob=0.01,
            point_magnitude=5.0,
            collective_magnitude_multiplier=3.0
        )
    )

    # Save dataset
    output_file = output_dir / "synthetic_timeseries_default.json"
    save_synthetic_dataset(dataset, str(output_file), format='json')

    # Generate validation dataset
    logger.info("Generating validation dataset...")
    val_dataset = generate_validation_dataset(
        n_samples=5000,
        anomaly_rate=0.03,
        seed=123
    )

    val_file = output_dir / "synthetic_timeseries_validation.json"
    save_synthetic_dataset(val_dataset, str(val_file), format='json')

    # Log summary
    logger.info(f"Generated dataset with {dataset.metadata['n_samples']} samples")
    logger.info(f"Anomaly rate: {dataset.metadata['anomaly_rate']:.2%}")
    logger.info(f"Anomalies at indices: {dataset.anomaly_indices[:10]}...")

    # Return dataset for programmatic use
    return dataset


if __name__ == "__main__":
    main()