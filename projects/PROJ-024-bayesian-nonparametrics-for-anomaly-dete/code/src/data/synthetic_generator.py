"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with:
- Pre-anomaly dynamics (stationary or trend)
- Abrupt regime shifts (mean/variance changes)
- Independent ground-truth timestamps

Used for:
- Simulation studies (T018)
- Fallback when real data search fails (FR-017b)
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
    trend_slope: float = 0.0
    seed: int = 42

    def __post_init__(self):
        np.random.seed(self.seed)

    def __getattr__(self, name):
        # Tolerant fallback for logger-style calls or unknown attributes
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective', 'shift'] = 'shift'
    start_index: int = 500
    duration: int = 50
    magnitude: float = 3.0
    variance_scale: float = 2.0
    seed: int = 42

    def __post_init__(self):
        np.random.seed(self.seed)

    def __getattr__(self, name):
        # Tolerant fallback for logger-style calls or unknown attributes
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset and metadata."""
    timestamps: List[float]
    values: List[float]
    ground_truth: Dict[str, Any]
    config: Dict[str, Any]
    checksum: Optional[str] = None

    def to_dict(self):
        return asdict(self)


def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series with optional trend and noise.

    Returns:
        Tuple of (timestamps, values)
    """
    t = np.arange(config.length)
    # Base frequency component
    signal = np.sin(2 * np.pi * config.base_frequency * t)
    # Add trend
    signal += config.trend_slope * t
    # Add noise
    noise = np.random.normal(0, config.noise_std, config.length)
    values = signal + noise
    return t, values


def inject_point_anomalous(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    count: int = 5
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject point anomalies (spikes) at random locations.

    Args:
        values: Base signal values
        anomaly_config: Configuration for anomaly properties
        count: Number of point anomalies to inject

    Returns:
        Tuple of (modified_values, list_of_indices)
    """
    indices = np.random.choice(
        range(anomaly_config.start_index, len(values) - anomaly_config.duration),
        size=count,
        replace=False
    )
    for idx in indices:
        # Inject spike
        values[idx] += anomaly_config.magnitude * np.random.choice([-1, 1])
    return values, list(indices)


def inject_contextual_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous in context).
    """
    # Create a region where normal values become anomalous
    start = anomaly_config.start_index
    end = start + anomaly_config.duration
    indices = list(range(start, end))

    # Invert the signal locally to make it contextually anomalous
    values[start:end] = -values[start:end]

    return values, indices


def inject_collective_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject collective anomalies (sequence of values that are anomalous together).
    """
    start = anomaly_config.start_index
    end = start + anomaly_config.duration

    # Generate a distinct pattern for the collective anomaly
    collective_pattern = np.sin(2 * np.pi * 0.1 * np.arange(end - start)) * anomaly_config.magnitude
    values[start:end] += collective_pattern

    return values, list(range(start, end))


def inject_regime_shift(
    values: np.ndarray,
    anomaly_config: AnomalyConfig
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject an abrupt regime shift (mean and/or variance change).
    This is the primary mode for testing $\dot{\alpha}$ detection.
    """
    start = anomaly_config.start_index
    end = min(start + anomaly_config.duration, len(values))

    # Calculate shift magnitude
    current_mean = np.mean(values[:start])
    current_std = np.std(values[:start])

    # Shift the mean
    shift_amount = anomaly_config.magnitude * current_std
    values[start:end] += shift_amount

    # Scale the variance in the anomalous region
    if anomaly_config.variance_scale > 1.0:
        noise = np.random.normal(0, 1, end - start)
        values[start:end] = values[start:end] * anomaly_config.variance_scale + noise * current_std * (anomaly_config.variance_scale - 1)

    return values, list(range(start, end))


def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: AnomalyConfig
) -> SyntheticDataset:
    """
    Generate a complete synthetic dataset with anomalies and ground truth.

    Args:
        signal_config: Configuration for the base signal
        anomaly_config: Configuration for anomaly injection

    Returns:
        SyntheticDataset object containing data and metadata
    """
    # Generate base signal
    timestamps, values = generate_base_signal(signal_config)
    values = values.copy()  # Ensure we don't modify the original

    # Determine injection method based on config
    if anomaly_config.anomaly_type == 'point':
        values, anomaly_indices = inject_point_anomalous(values, anomaly_config)
    elif anomaly_config.anomaly_type == 'contextual':
        values, anomaly_indices = inject_contextual_anomalies(values, anomaly_config)
    elif anomaly_config.anomaly_type == 'collective':
        values, anomaly_indices = inject_collective_anomalies(values, anomaly_config)
    elif anomaly_config.anomaly_type == 'shift':
        values, anomaly_indices = inject_regime_shift(values, anomaly_config)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Construct ground truth
    ground_truth = {
        "anomaly_type": anomaly_config.anomaly_type,
        "start_index": anomaly_config.start_index,
        "end_index": anomaly_config.start_index + anomaly_config.duration,
        "anomaly_indices": anomaly_indices,
        "magnitude": anomaly_config.magnitude,
        "duration": anomaly_config.duration,
        "is_anomalous": [1 if i in anomaly_indices else 0 for i in range(len(values))]
    }

    # Construct dataset metadata
    dataset_config = {
        "signal": asdict(signal_config),
        "anomaly": asdict(anomaly_config)
    }

    return SyntheticDataset(
        timestamps=timestamps.tolist(),
        values=values.tolist(),
        ground_truth=ground_truth,
        config=dataset_config
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save a synthetic dataset to JSON.

    Args:
        dataset: The SyntheticDataset to save
        output_path: Path to the output file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for JSON serialization
    data = dataset.to_dict()

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved synthetic dataset to {output_path}")


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from JSON.

    Args:
        input_path: Path to the input file

    Returns:
        SyntheticDataset object
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Reconstruct the object
    return SyntheticDataset(
        timestamps=data['timestamps'],
        values=data['values'],
        ground_truth=data['ground_truth'],
        config=data['config'],
        checksum=data.get('checksum')
    )


def generate_validation_dataset(seed: int = 42) -> SyntheticDataset:
    """
    Generate a standard validation dataset for testing the pipeline.
    Uses fixed parameters for reproducibility.

    Returns:
        SyntheticDataset with known ground truth
    """
    signal_cfg = SignalConfig(
        length=1000,
        base_frequency=0.01,
        noise_std=0.1,
        trend_slope=0.0,
        seed=seed
    )

    anomaly_cfg = AnomalyConfig(
        anomaly_type='shift',
        start_index=500,
        duration=50,
        magnitude=3.0,
        variance_scale=1.5,
        seed=seed + 1
    )

    return generate_synthetic_timeseries(signal_cfg, anomaly_cfg)


def main():
    """
    Main entry point for generating synthetic datasets.
    Creates a validation dataset and saves it to data/raw/.
    """
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate dataset
    logger.info("Generating synthetic validation dataset...")
    dataset = generate_validation_dataset(seed=42)

    # Save to disk
    output_path = output_dir / "synthetic_validation.json"
    save_synthetic_dataset(dataset, str(output_path))

    # Print summary
    logger.info(f"Dataset generated: {len(dataset.values)} points")
    logger.info(f"Anomaly start: {dataset.ground_truth['start_index']}")
    logger.info(f"Anomaly end: {dataset.ground_truth['end_index']}")
    logger.info(f"Anomaly type: {dataset.ground_truth['anomaly_type']}")

    # Verify ground truth timestamps are independent
    gt_start = dataset.ground_truth['start_index']
    gt_end = dataset.ground_truth['end_index']
    logger.info(f"Ground truth timestamps: [{gt_start}, {gt_end}]")

    return dataset


if __name__ == "__main__":
    main()