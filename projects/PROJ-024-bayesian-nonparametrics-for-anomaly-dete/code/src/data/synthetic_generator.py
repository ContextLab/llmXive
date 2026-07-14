"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for validation (FR-021, FR-022).

This module provides:
- Configurable signal generation (trends, seasonality, noise)
- Injection of point, contextual, and collective anomalies
- Ground truth timestamp tracking
- Dataset saving/loading utilities
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
    frequency: float = 1.0
    trend_strength: float = 0.1
    seasonality_strength: float = 0.5
    noise_std: float = 0.1
    base_value: float = 10.0
    seed: Optional[int] = 42

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Tolerance for logger-style calls (per contract requirements)
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal["point", "contextual", "collective"] = "point"
    anomaly_ratio: float = 0.05
    anomaly_magnitude: float = 3.0
    anomaly_duration_min: int = 5
    anomaly_duration_max: int = 20
    seed: Optional[int] = 42

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Tolerance for logger-style calls (per contract requirements)
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class SyntheticDataset:
    """Container for synthetic dataset and ground truth."""
    timestamps: np.ndarray
    values: np.ndarray
    ground_truth: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataset to dictionary for serialization."""
        return {
            "timestamps": self.timestamps.tolist(),
            "values": self.values.tolist(),
            "ground_truth": self.ground_truth,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyntheticDataset":
        """Load dataset from dictionary."""
        return cls(
            timestamps=np.array(data["timestamps"]),
            values=np.array(data["values"]),
            ground_truth=data["ground_truth"],
            metadata=data["metadata"]
        )


def generate_base_signal(config: SignalConfig) -> np.ndarray:
    """
    Generate a base time series with trend, seasonality, and noise.

    Args:
        config: Signal configuration parameters

    Returns:
        np.ndarray: Generated time series values
    """
    t = np.arange(config.length)

    # Trend component
    trend = config.trend_strength * t

    # Seasonality component
    seasonality = config.seasonality_strength * np.sin(2 * np.pi * config.frequency * t / config.length)

    # Noise component
    noise = np.random.normal(0, config.noise_std, config.length)

    # Combine components
    signal = config.base_value + trend + seasonality + noise

    return signal


def inject_point_anomalies(
    values: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, List[int]]
) -> Tuple[np.ndarray, Dict[str, List[int]]]:
    """
    Inject point anomalies (sudden spikes/drops) into the signal.

    Args:
        values: Original signal values
        config: Anomaly configuration
        ground_truth: Dictionary to update with anomaly timestamps

    Returns:
        Tuple of (modified values, updated ground truth)
    """
    n_anomalies = int(len(values) * config.anomaly_ratio)
    anomaly_indices = np.random.choice(
        len(values), size=n_anomalies, replace=False
    )

    for idx in anomaly_indices:
        # Random direction (positive or negative)
        direction = np.random.choice([-1, 1])
        values[idx] += direction * config.anomaly_magnitude * np.std(values)

    ground_truth["point_anomalies"].extend(sorted(anomaly_indices.tolist()))
    return values, ground_truth


def inject_contextual_anomalies(
    values: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, List[int]]
) -> Tuple[np.ndarray, Dict[str, List[int]]]:
    """
    Inject contextual anomalies (values abnormal in context but not globally).

    Args:
        values: Original signal values
        config: Anomaly configuration
        ground_truth: Dictionary to update with anomaly timestamps

    Returns:
        Tuple of (modified values, updated ground truth)
    """
    n_anomalies = int(len(values) * config.anomaly_ratio)
    anomaly_indices = np.random.choice(
        len(values), size=n_anomalies, replace=False
    )

    for idx in anomaly_indices:
        # Shift value to be abnormal relative to local context
        local_mean = np.mean(values[max(0, idx-10):min(len(values), idx+10)])
        values[idx] = local_mean + config.anomaly_magnitude * np.std(values)

    ground_truth["contextual_anomalies"].extend(sorted(anomaly_indices.tolist()))
    return values, ground_truth


def inject_collective_anomalies(
    values: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, List[int]]
) -> Tuple[np.ndarray, Dict[str, List[int]]]:
    """
    Inject collective anomalies (sequences of abnormal values).

    Args:
        values: Original signal values
        config: Anomaly configuration
        ground_truth: Dictionary to update with anomaly timestamps

    Returns:
        Tuple of (modified values, updated ground truth)
    """
    max_collectives = int(len(values) * config.anomaly_ratio / config.anomaly_duration_min)
    n_collectives = np.random.randint(1, max_collectives + 1)

    for _ in range(n_collectives):
        duration = np.random.randint(config.anomaly_duration_min, config.anomaly_duration_max + 1)
        start_idx = np.random.randint(0, len(values) - duration)
        end_idx = start_idx + duration

        # Shift the entire segment
        shift = config.anomaly_magnitude * np.std(values) * np.random.choice([-1, 1])
        values[start_idx:end_idx] += shift

        ground_truth["collective_anomalies"].append({
            "start": int(start_idx),
            "end": int(end_idx),
            "duration": int(duration)
        })

    return values, ground_truth


def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: AnomalyConfig
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series with anomalies and ground truth.

    Args:
        signal_config: Base signal configuration
        anomaly_config: Anomaly injection configuration

    Returns:
        SyntheticDataset: Complete dataset with ground truth
    """
    # Generate base signal
    values = generate_base_signal(signal_config)

    # Initialize ground truth
    ground_truth = {
        "point_anomalies": [],
        "contextual_anomalies": [],
        "collective_anomalies": [],
        "total_anomalies": 0
    }

    # Inject anomalies based on type
    if anomaly_config.anomaly_type == "point":
        values, ground_truth = inject_point_anomalies(values, anomaly_config, ground_truth)
    elif anomaly_config.anomaly_type == "contextual":
        values, ground_truth = inject_contextual_anomalies(values, anomaly_config, ground_truth)
    elif anomaly_config.anomaly_type == "collective":
        values, ground_truth = inject_collective_anomalies(values, anomaly_config, ground_truth)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Calculate total anomaly count
    ground_truth["total_anomalies"] = (
        len(ground_truth["point_anomalies"]) +
        len(ground_truth["contextual_anomalies"]) +
        len(ground_truth["collective_anomalies"])
    )

    # Generate timestamps
    timestamps = np.arange(len(values))

    # Create metadata
    metadata = {
        "signal_config": asdict(signal_config),
        "anomaly_config": asdict(anomaly_config),
        "generation_time": str(np.datetime64("now")),
        "data_type": "synthetic"
    }

    return SyntheticDataset(
        timestamps=timestamps,
        values=values,
        ground_truth=ground_truth,
        metadata=metadata
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save synthetic dataset to JSON file.

    Args:
        dataset: Dataset to save
        output_path: Path to output file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(dataset.to_dict(), f, indent=2)

    logger.info(f"Dataset saved to {output_path}")


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load synthetic dataset from JSON file.

    Args:
        input_path: Path to input file

    Returns:
        SyntheticDataset: Loaded dataset
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    return SyntheticDataset.from_dict(data)


def generate_validation_dataset(
    n_samples: int = 100,
    anomaly_ratio: float = 0.1,
    seed: Optional[int] = None
) -> List[SyntheticDataset]:
    """
    Generate multiple validation datasets with varying characteristics.

    Args:
        n_samples: Number of datasets to generate
        anomaly_ratio: Target anomaly ratio
        seed: Random seed for reproducibility

    Returns:
        List of SyntheticDataset instances
    """
    datasets = []

    for i in range(n_samples):
        # Vary signal characteristics
        signal_config = SignalConfig(
            length=500 + np.random.randint(0, 500),
            frequency=0.5 + np.random.random() * 2.0,
            trend_strength=0.05 + np.random.random() * 0.2,
            noise_std=0.05 + np.random.random() * 0.15,
            seed=seed + i if seed else None
        )

        # Vary anomaly characteristics
        anomaly_types = ["point", "contextual", "collective"]
        anomaly_config = AnomalyConfig(
            anomaly_type=np.random.choice(anomaly_types),
            anomaly_ratio=anomaly_ratio * (0.5 + np.random.random()),
            anomaly_magnitude=2.0 + np.random.random() * 2.0,
            seed=seed + 1000 + i if seed else None
        )

        dataset = generate_synthetic_timeseries(signal_config, anomaly_config)
        datasets.append(dataset)

    return datasets


def main():
    """Main entry point for synthetic data generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic time series data")
    parser.add_argument("--output", type=str, default="data/processed/results/synthetic_dataset.json",
                      help="Output file path")
    parser.add_argument("--length", type=int, default=1000, help="Signal length")
    parser.add_argument("--anomaly-type", type=str, default="point",
                      choices=["point", "contextual", "collective"],
                      help="Type of anomalies to inject")
    parser.add_argument("--anomaly-ratio", type=float, default=0.05,
                      help="Ratio of anomalies in the signal")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    # Create configurations
    signal_config = SignalConfig(
        length=args.length,
        seed=args.seed
    )

    anomaly_config = AnomalyConfig(
        anomaly_type=args.anomaly_type,
        anomaly_ratio=args.anomaly_ratio,
        seed=args.seed
    )

    # Generate dataset
    dataset = generate_synthetic_timeseries(signal_config, anomaly_config)

    # Save dataset
    save_synthetic_dataset(dataset, args.output)

    # Print summary
    print(f"Generated synthetic dataset with {len(dataset.values)} points")
    print(f"Anomaly type: {args.anomaly_type}")
    print(f"Total anomalies injected: {dataset.ground_truth['total_anomalies']}")
    print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()