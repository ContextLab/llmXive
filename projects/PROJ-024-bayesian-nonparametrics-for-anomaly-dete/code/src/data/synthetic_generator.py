"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with:
1. Pre-anomaly dynamics (stable regime)
2. Abrupt shifts (regime changes)
3. Independent ground-truth timestamps for validation

Implements FR-021 and FR-022 requirements.
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
    """Configuration for the base signal generation."""
    length: int = 1000
    base_frequency: float = 0.05
    noise_std: float = 0.1
    trend_slope: float = 0.0001
    seed: int = 42

    # Allow arbitrary attribute access for logger compatibility
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective', 'shift'] = 'shift'
    anomaly_start: int = 500
    anomaly_duration: int = 50
    magnitude: float = 3.0
    seed: int = 42
    anomaly_duration_min: int = 10  # Minimum duration for collective anomalies

    # Allow arbitrary attribute access for logger compatibility
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class SyntheticDataset:
    """Container for generated synthetic data and metadata."""
    timestamps: List[float]
    values: List[float]
    ground_truth: List[bool]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_base_signal(config: SignalConfig) -> np.ndarray:
    """
    Generate a base time series with trend and noise.

    Args:
        config: SignalConfig with generation parameters.

    Returns:
        numpy array of base signal values.
    """
    np.random.seed(config.seed)
    t = np.arange(config.length)
    # Linear trend + low frequency sine + noise
    trend = config.trend_slope * t
    signal = config.base_frequency * np.sin(2 * np.pi * config.base_frequency * t)
    noise = np.random.normal(0, config.noise_std, config.length)
    return trend + signal + noise


def inject_point_anomalies(data: np.ndarray, config: AnomalyConfig) -> Tuple[np.ndarray, List[int]]:
    """
    Inject point anomalies (spikes) at random locations.

    Args:
        data: Base signal array.
        config: AnomalyConfig with magnitude and seed.

    Returns:
        Modified data array and list of anomaly indices.
    """
    np.random.seed(config.seed)
    anomaly_indices = [config.anomaly_start]
    data[config.anomaly_start] += config.magnitude * np.random.choice([-1, 1])
    return data, anomaly_indices


def inject_contextual_anomalies(data: np.ndarray, config: AnomalyConfig) -> Tuple[np.ndarray, List[int]]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous in context).

    Args:
        data: Base signal array.
        config: AnomalyConfig.

    Returns:
        Modified data array and list of anomaly indices.
    """
    np.random.seed(config.seed)
    # Create a value that is statistically normal but contextually wrong
    # e.g., a high value during a low trend period
    anomaly_indices = [config.anomaly_start]
    # Inject a value that contradicts the local trend
    data[config.anomaly_start] += config.magnitude
    return data, anomaly_indices


def inject_collective_anomalies(data: np.ndarray, config: AnomalyConfig) -> Tuple[np.ndarray, List[int]]:
    """
    Inject collective anomalies (a sequence of points that are anomalous together).

    Args:
        data: Base signal array.
        config: AnomalyConfig.

    Returns:
        Modified data array and list of anomaly indices.
    """
    np.random.seed(config.seed)
    duration = max(config.anomaly_duration, config.anomaly_duration_min)
    anomaly_indices = list(range(config.anomaly_start, config.anomaly_start + duration))
    # Shift the entire segment
    data[config.anomaly_start:config.anomaly_start + duration] += config.magnitude
    return data, anomaly_indices


def inject_abrupt_shift(data: np.ndarray, config: AnomalyConfig) -> Tuple[np.ndarray, List[int]]:
    """
    Inject an abrupt regime shift (change in mean level).

    Args:
        data: Base signal array.
        config: AnomalyConfig.

    Returns:
        Modified data array and list of anomaly indices.
    """
    np.random.seed(config.seed)
    duration = max(config.anomaly_duration, config.anomaly_duration_min)
    anomaly_indices = list(range(config.anomaly_start, config.anomaly_start + duration))
    # Apply a step change
    data[config.anomaly_start:config.anomaly_start + duration] += config.magnitude
    return data, anomaly_indices



def generate_synthetic_timeseries(
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series with anomalies.

    Args:
        signal_config: Configuration for base signal.
        anomaly_config: Configuration for anomaly injection.

    Returns:
        SyntheticDataset with values, timestamps, and ground truth.
    """
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()

    # Generate base signal
    data = generate_base_signal(signal_config)

    # Inject anomalies based on type
    if anomaly_config.anomaly_type == 'point':
        data, gt_indices = inject_point_anomalies(data, anomaly_config)
    elif anomaly_config.anomaly_type == 'contextual':
        data, gt_indices = inject_contextual_anomalies(data, anomaly_config)
    elif anomaly_config.anomaly_type == 'collective':
        data, gt_indices = inject_collective_anomalies(data, anomaly_config)
    elif anomaly_config.anomaly_type == 'shift':
        data, gt_indices = inject_abrupt_shift(data, anomaly_config)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Create ground truth boolean mask
    ground_truth = np.zeros(signal_config.length, dtype=bool)
    for idx in gt_indices:
        if 0 <= idx < signal_config.length:
            ground_truth[idx] = True

    timestamps = np.arange(signal_config.length).astype(float)

    # Create metadata
    metadata = {
        "signal_config": asdict(signal_config),
        "anomaly_config": asdict(anomaly_config),
        "anomaly_indices": gt_indices,
        "total_points": signal_config.length,
        "anomaly_count": len(gt_indices)
    }

    return SyntheticDataset(
        timestamps=timestamps.tolist(),
        values=data.tolist(),
        ground_truth=ground_truth.tolist(),
        metadata=metadata
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save synthetic dataset to a JSON file.

    Args:
        dataset: The SyntheticDataset to save.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)



def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        Loaded SyntheticDataset.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    return SyntheticDataset(
        timestamps=data['timestamps'],
        values=data['values'],
        ground_truth=data['ground_truth'],
        metadata=data['metadata']
    )


def generate_validation_dataset(
    n_samples: int = 10,
    anomaly_rate: float = 0.2,
    output_dir: Optional[str] = None
) -> List[SyntheticDataset]:
    """
    Generate a set of validation datasets with varying parameters.

    Args:
        n_samples: Number of datasets to generate.
        anomaly_rate: Fraction of datasets to include anomalies.
        output_dir: Optional directory to save datasets.

    Returns:
        List of SyntheticDataset objects.
    """
    datasets = []
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

    for i in range(n_samples):
        # Vary parameters slightly for diversity
        seed = 42 + i
        signal_cfg = SignalConfig(seed=seed, length=500 + i * 10)
        
        # Randomly decide if this sample has an anomaly
        has_anomaly = (i / n_samples) < anomaly_rate
        
        if has_anomaly:
            anomaly_cfg = AnomalyConfig(
                seed=seed + 1000,
                anomaly_start=200 + i * 5,
                anomaly_duration=30 + i,
                magnitude=2.0 + i * 0.1
            )
        else:
            # Create a config that effectively injects no anomalies
            anomaly_cfg = AnomalyConfig(
                seed=seed + 2000,
                anomaly_start=signal_cfg.length + 100, # Start outside range
                anomaly_duration=10,
                magnitude=0.0
            )

        dataset = generate_synthetic_timeseries(signal_cfg, anomaly_cfg)
        datasets.append(dataset)

        if output_dir:
            save_synthetic_dataset(dataset, str(out_path / f"validation_sample_{i}.json"))

    return datasets


def main():
    """Main entry point for generating synthetic datasets."""
    logger.info("Starting synthetic dataset generation...")

    # Generate a single example dataset
    signal_cfg = SignalConfig(length=1000, base_frequency=0.05, noise_std=0.1)
    anomaly_cfg = AnomalyConfig(
        anomaly_type='shift',
        anomaly_start=500,
        anomaly_duration=50,
        magnitude=3.0
    )

    dataset = generate_synthetic_timeseries(signal_cfg, anomaly_cfg)

    # Save to data/processed/results as per project conventions
    output_dir = Path("data/processed/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "synthetic_timeseries_example.json"

    save_synthetic_dataset(dataset, str(output_file))

    # Generate validation set for T018 simulation
    val_datasets = generate_validation_dataset(n_samples=5, anomaly_rate=1.0, output_dir=str(output_dir))

    logger.info(f"Generated {len(val_datasets)} validation datasets.")
    logger.info(f"Example dataset saved to: {output_file}")

    return dataset


if __name__ == "__main__":
    main()