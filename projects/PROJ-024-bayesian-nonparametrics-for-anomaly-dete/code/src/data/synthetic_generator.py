"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps (FR-021, FR-022). Used for simulation studies and
as a fallback when real-world data is unavailable.
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
    """Configuration for base signal generation."""
    base_frequency: float = 0.05
    amplitude: float = 1.0
    noise_std: float = 0.1
    trend_slope: float = 0.0
    seasonality_period: int = 50
    # Tolerance for logger-style calls from various callers
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal["point", "contextual", "collective"] = "point"
    magnitude: float = 3.0
    duration: int = 10
    start_index: Optional[int] = None
    end_index: Optional[int] = None


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    timestamps: List[int]
    values: List[float]
    is_anomaly: List[bool]
    anomaly_start: Optional[int]
    anomaly_end: Optional[int]
    config: Dict[str, Any]


def generate_base_signal(
    n_points: int,
    config: SignalConfig,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a base time series with configurable properties.

    Args:
        n_points: Number of data points to generate.
        config: SignalConfig instance defining signal properties.
        seed: Random seed for reproducibility.

    Returns:
        NumPy array of shape (n_points,) containing the base signal.
    """
    if seed is not None:
        np.random.seed(seed)

    t = np.arange(n_points)

    # Base sine wave
    signal = config.amplitude * np.sin(2 * np.pi * config.base_frequency * t)

    # Add seasonality
    if config.seasonality_period > 0:
        seasonal = 0.5 * config.amplitude * np.sin(2 * np.pi * t / config.seasonality_period)
        signal += seasonal

    # Add trend
    trend = config.trend_slope * t
    signal += trend

    # Add noise
    noise = np.random.normal(0, config.noise_std, n_points)
    signal += noise

    return signal


def inject_point_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    n_anomalies: int = 1,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject point anomalies (abrupt spikes/dips) into the signal.

    Args:
        values: Original signal array.
        anomaly_config: Configuration for anomaly injection.
        n_anomalies: Number of anomalies to inject.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (modified signal, list of anomaly start indices).
    """
    if seed is not None:
        np.random.seed(seed)

    n_points = len(values)
    anomaly_indices = []
    modified_values = values.copy()

    # Determine valid range for anomaly injection (avoid edges)
    min_idx = 10
    max_idx = n_points - 10

    for _ in range(n_anomalies):
        if anomaly_config.start_index is not None:
            start_idx = anomaly_config.start_index
        else:
            start_idx = np.random.randint(min_idx, max_idx)

        # Ensure we don't go out of bounds
        start_idx = min(max(start_idx, min_idx), max_idx)

        # Determine anomaly magnitude (positive or negative)
        direction = np.random.choice([-1, 1])
        magnitude = anomaly_config.magnitude * direction

        # Inject the anomaly
        modified_values[start_idx] += magnitude
        anomaly_indices.append(start_idx)

    return modified_values, anomaly_indices


def inject_contextual_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    n_anomalies: int = 1,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject contextual anomalies (values normal in isolation but anomalous in context).

    Args:
        values: Original signal array.
        anomaly_config: Configuration for anomaly injection.
        n_anomalies: Number of anomalies to inject.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (modified signal, list of anomaly start indices).
    """
    if seed is not None:
        np.random.seed(seed)

    n_points = len(values)
    anomaly_indices = []
    modified_values = values.copy()

    min_idx = 10
    max_idx = n_points - 10

    for _ in range(n_anomalies):
        start_idx = anomaly_config.start_index if anomaly_config.start_index else np.random.randint(min_idx, max_idx)
        start_idx = min(max(start_idx, min_idx), max_idx)
        duration = min(anomaly_config.duration, n_points - start_idx)

        # Contextual anomaly: shift the local mean significantly
        local_shift = anomaly_config.magnitude
        modified_values[start_idx:start_idx + duration] += local_shift
        anomaly_indices.append(start_idx)

    return modified_values, anomaly_indices


def inject_collective_anomalies(
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    n_anomalies: int = 1,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, List[int]]:
    """
    Inject collective anomalies (a sequence of points that are anomalous together).

    Args:
        values: Original signal array.
        anomaly_config: Configuration for anomaly injection.
        n_anomalies: Number of anomalies to inject.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (modified signal, list of anomaly start indices).
    """
    if seed is not None:
        np.random.seed(seed)

    n_points = len(values)
    anomaly_indices = []
    modified_values = values.copy()

    min_idx = 10
    max_idx = n_points - 10

    for _ in range(n_anomalies):
        start_idx = anomaly_config.start_index if anomaly_config.start_index else np.random.randint(min_idx, max_idx)
        start_idx = min(max(start_idx, min_idx), max_idx)
        duration = min(anomaly_config.duration, n_points - start_idx)

        # Collective anomaly: change the pattern entirely (e.g., different frequency)
        t = np.arange(duration)
        new_pattern = anomaly_config.magnitude * np.sin(2 * np.pi * 0.2 * t)
        modified_values[start_idx:start_idx + duration] = new_pattern
        anomaly_indices.append(start_idx)

    return modified_values, anomaly_indices


def generate_synthetic_timeseries(
    n_points: int = 1000,
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with anomalies.

    Args:
        n_points: Total number of data points.
        signal_config: Configuration for the base signal.
        anomaly_config: Configuration for anomaly injection.
        seed: Random seed for reproducibility.

    Returns:
        SyntheticDataset object containing the generated data and metadata.
    """
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()

    # Generate base signal
    values = generate_base_signal(n_points, signal_config, seed)

    # Determine anomaly injection parameters
    if anomaly_config.start_index is not None:
        start_idx = anomaly_config.start_index
    else:
        # Place anomaly in the middle third of the series
        min_idx = n_points // 3
        max_idx = 2 * n_points // 3
        start_idx = np.random.randint(min_idx, max_idx) if seed is None or np.random.random() > 0.5 else min_idx + (max_idx - min_idx) // 2

    end_idx = min(start_idx + anomaly_config.duration, n_points)

    # Inject anomalies based on type
    if anomaly_config.anomaly_type == "point":
        values, anomaly_indices = inject_point_anomalies(values, anomaly_config, n_anomalies=1, seed=seed)
    elif anomaly_config.anomaly_type == "contextual":
        values, anomaly_indices = inject_contextual_anomalies(values, anomaly_config, n_anomalies=1, seed=seed)
    elif anomaly_config.anomaly_type == "collective":
        values, anomaly_indices = inject_collective_anomalies(values, anomaly_config, n_anomalies=1, seed=seed)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Create ground truth mask
    is_anomaly = np.zeros(n_points, dtype=bool)
    is_anomaly[start_idx:end_idx] = True

    # Create timestamps
    timestamps = list(range(n_points))

    # Prepare config dict for serialization
    config_dict = {
        "signal": asdict(signal_config),
        "anomaly": asdict(anomaly_config),
        "n_points": n_points,
        "seed": seed,
        "anomaly_start": start_idx,
        "anomaly_end": end_idx
    }

    return SyntheticDataset(
        timestamps=timestamps,
        values=values.tolist(),
        is_anomaly=is_anomaly.tolist(),
        anomaly_start=start_idx,
        anomaly_end=end_idx,
        config=config_dict
    )


def save_synthetic_dataset(
    dataset: SyntheticDataset,
    output_path: str,
    format: Literal["csv", "json"] = "csv"
) -> None:
    """
    Save a synthetic dataset to disk.

    Args:
        dataset: The SyntheticDataset object to save.
        output_path: Path to the output file.
        format: Output format ('csv' or 'json').
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "csv":
        # Convert to CSV format
        data = {
            "timestamp": dataset.timestamps,
            "value": dataset.values,
            "is_anomaly": dataset.is_anomaly
        }

        # Use numpy to handle serialization safely
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data.keys())
            rows = list(zip(data["timestamp"], data["value"], data["is_anomaly"]))
            writer.writerows(rows)

        # Save metadata separately
        metadata_path = output_path.with_suffix('.json')
        # Convert numpy types to Python native types for JSON serialization
        config_clean = {}
        for k, v in dataset.config.items():
            if isinstance(v, dict):
                config_clean[k] = {
                    subk: (int(subv) if isinstance(subv, np.integer) else float(subv) if isinstance(subv, np.floating) else subv)
                    for subk, subv in v.items()
                }
            else:
                config_clean[k] = v

        with open(metadata_path, 'w') as f:
            json.dump(config_clean, f, indent=2)

        logger.info(f"Saved CSV dataset to {output_path}")
        logger.info(f"Saved metadata to {metadata_path}")

    elif format == "json":
        # Convert to JSON format
        data = {
            "timestamps": dataset.timestamps,
            "values": dataset.values,
            "is_anomaly": dataset.is_anomaly,
            "anomaly_start": dataset.anomaly_start,
            "anomaly_end": dataset.anomaly_end,
            "config": dataset.config
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved JSON dataset to {output_path}")
    else:
        raise ValueError(f"Unsupported format: {format}")


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from disk.

    Args:
        input_path: Path to the dataset file.

    Returns:
        SyntheticDataset object.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {input_path}")

    if input_path.suffix == ".csv":
        import csv
        with open(input_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        timestamps = [int(row["timestamp"]) for row in rows]
        values = [float(row["value"]) for row in rows]
        is_anomaly = [row["is_anomaly"].lower() == "true" for row in rows]

        # Load metadata if exists
        metadata_path = input_path.with_suffix('.json')
        config = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                config = json.load(f)

        return SyntheticDataset(
            timestamps=timestamps,
            values=values,
            is_anomaly=is_anomaly,
            anomaly_start=config.get("anomaly_start"),
            anomaly_end=config.get("anomaly_end"),
            config=config
        )

    elif input_path.suffix == ".json":
        with open(input_path, 'r') as f:
            data = json.load(f)

        return SyntheticDataset(
            timestamps=data["timestamps"],
            values=data["values"],
            is_anomaly=data["is_anomaly"],
            anomaly_start=data["anomaly_start"],
            anomaly_end=data["anomaly_end"],
            config=data["config"]
        )
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")


def generate_validation_dataset(
    n_points: int = 500,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a validation dataset with known ground truth.

    Args:
        n_points: Number of data points.
        seed: Random seed.

    Returns:
        SyntheticDataset with a single collective anomaly.
    """
    signal_cfg = SignalConfig(
        base_frequency=0.04,
        amplitude=1.0,
        noise_std=0.05,
        seasonality_period=40
    )

    anomaly_cfg = AnomalyConfig(
        anomaly_type="collective",
        magnitude=2.5,
        duration=20,
        start_index=n_points // 2
    )

    return generate_synthetic_timeseries(
        n_points=n_points,
        signal_config=signal_cfg,
        anomaly_config=anomaly_cfg,
        seed=seed
    )


def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic time series data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--anomaly-rate", type=float, default=0.05, help="Fraction of data that is anomalous")
    parser.add_argument("--n-points", type=int, default=1000, help="Number of data points")
    parser.add_argument("--output", type=str, default="data/processed/results/synthetic_dataset.csv", help="Output path")
    parser.add_argument("--anomaly-type", type=str, choices=["point", "contextual", "collective"], default="collective", help="Type of anomaly to inject")

    args = parser.parse_args()

    # Calculate anomaly duration based on rate
    anomaly_duration = int(args.n_points * args.anomaly_rate)

    signal_cfg = SignalConfig()
    anomaly_cfg = AnomalyConfig(
        anomaly_type=args.anomaly_type,
        magnitude=3.0,
        duration=anomaly_duration,
        start_index=None  # Will be randomized or centered
    )

    dataset = generate_synthetic_timeseries(
        n_points=args.n_points,
        signal_config=signal_cfg,
        anomaly_config=anomaly_cfg,
        seed=args.seed
    )

    save_synthetic_dataset(dataset, args.output, format="csv")
    logger.info(f"Successfully generated synthetic dataset with {sum(dataset.is_anomaly)} anomalous points ({args.anomaly_rate*100:.1f}%)")


if __name__ == "__main__":
    main()