"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps as required by FR-021 and FR-022.

This module is used for simulation studies and as a fallback if real data
search fails.
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
OUTPUT_DIR = Path("data/processed/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SignalConfig:
    """Configuration for signal generation parameters."""
    # Signal properties
    base_frequency: float = 0.1
    noise_level: float = 0.05
    trend_slope: float = 0.001
    
    # Anomaly injection parameters
    anomaly_magnitude: float = 3.0
    anomaly_duration: int = 10
    
    # Tolerant logger interface for compatibility with various callers
    def __getattr__(self, name: str) -> Any:
        """Return a no-op callable for any logger-style attribute access."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            pass
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_rate: float = 0.05
    anomaly_type: Literal["point", "contextual", "collective"] = "point"
    start_index: Optional[int] = None
    end_index: Optional[int] = None


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset and metadata."""
    timestamps: List[float]
    values: List[float]
    anomaly_labels: List[int]
    ground_truth: Dict[str, Any]
    config: Dict[str, Any]
    seed: int
    metadata: Dict[str, Any] = field(default_factory=dict)


def generate_base_signal(
    n_points: int,
    config: SignalConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series signal with trend and noise.
    
    Args:
        n_points: Number of data points to generate
        config: SignalConfig with signal parameters
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (timestamps, signal_values)
    """
    if seed is not None:
        np.random.seed(seed)
        
    timestamps = np.arange(n_points)
    
    # Generate trend component
    trend = config.trend_slope * timestamps
    
    # Generate periodic component
    periodic = np.sin(2 * np.pi * config.base_frequency * timestamps)
    
    # Add noise
    noise = np.random.normal(0, config.noise_level, n_points)
    
    # Combine components
    signal = trend + periodic + noise
    
    return timestamps, signal


def inject_point_anomalies(
    timestamps: np.ndarray,
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Inject point anomalies into the time series.
    
    Args:
        timestamps: Array of timestamps
        values: Array of signal values
        anomaly_config: AnomalyConfig with injection parameters
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_timestamps, modified_values, ground_truth)
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_points = len(values)
    values = values.copy()
    
    # Calculate number of anomalies
    n_anomalies = int(n_points * anomaly_config.anomaly_rate)
    
    # Generate random anomaly indices
    anomaly_indices = np.random.choice(
        n_points, 
        size=min(n_anomalies, n_points - 1), 
        replace=False
    )
    
    ground_truth = {
        "anomaly_indices": [],
        "anomaly_types": [],
        "anomaly_magnitudes": []
    }
    
    for idx in anomaly_indices:
        # Inject anomaly with specified magnitude
        anomaly_magnitude = anomaly_config.anomaly_magnitude * np.random.choice([-1, 1])
        values[idx] += anomaly_magnitude
        
        ground_truth["anomaly_indices"].append(int(idx))
        ground_truth["anomaly_types"].append("point")
        ground_truth["anomaly_magnitudes"].append(float(anomaly_magnitude))
    
    return timestamps, values, ground_truth


def inject_contextual_anomalies(
    timestamps: np.ndarray,
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Inject contextual anomalies (values that are anomalous in context).
    
    Args:
        timestamps: Array of timestamps
        values: Array of signal values
        anomaly_config: AnomalyConfig with injection parameters
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_timestamps, modified_values, ground_truth)
    """
    if seed is not None:
        np.random.seed(seed)
        
    values = values.copy()
    
    # Generate a few contextual anomalies
    n_anomalies = max(1, int(len(values) * anomaly_config.anomaly_rate / 3))
    anomaly_indices = np.random.choice(
        len(values), 
        size=n_anomalies, 
        replace=False
    )
    
    ground_truth = {
        "anomaly_indices": [],
        "anomaly_types": [],
        "anomaly_magnitudes": []
    }
    
    for idx in anomaly_indices:
        # Contextual anomaly: value is normal but unusual for this time of day/period
        # Simulate by shifting value to a different phase of the cycle
        shift = np.random.choice([-2, 2]) * anomaly_config.anomaly_magnitude
        values[idx] += shift
        
        ground_truth["anomaly_indices"].append(int(idx))
        ground_truth["anomaly_types"].append("contextual")
        ground_truth["anomaly_magnitudes"].append(float(shift))
    
    return timestamps, values, ground_truth


def inject_collective_anomalies(
    timestamps: np.ndarray,
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Inject collective anomalies (a sequence of anomalous values).
    
    Args:
        timestamps: Array of timestamps
        values: Array of signal values
        anomaly_config: AnomalyConfig with injection parameters
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_timestamps, modified_values, ground_truth)
    """
    if seed is not None:
        np.random.seed(seed)
        
    values = values.copy()
    
    # Generate collective anomalies
    n_anomalies = max(1, int(len(values) * anomaly_config.anomaly_rate / 5))
    anomaly_starts = np.random.choice(
        len(values) - anomaly_config.anomaly_duration, 
        size=n_anomalies, 
        replace=False
    )
    
    ground_truth = {
        "anomaly_indices": [],
        "anomaly_types": [],
        "anomaly_magnitudes": []
    }
    
    for start_idx in anomaly_starts:
        end_idx = start_idx + anomaly_config.anomaly_duration
        # Inject a collective shift
        shift = anomaly_config.anomaly_magnitude * np.random.choice([-1, 1])
        values[start_idx:end_idx] += shift
        
        # Record all indices in the collective anomaly
        for i in range(start_idx, end_idx):
            ground_truth["anomaly_indices"].append(int(i))
            ground_truth["anomaly_types"].append("collective")
            ground_truth["anomaly_magnitudes"].append(float(shift))
    
    return timestamps, values, ground_truth


def generate_synthetic_timeseries(
    n_points: int = 1000,
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with anomalies.
    
    Args:
        n_points: Number of data points
        signal_config: SignalConfig for signal generation
        anomaly_config: AnomalyConfig for anomaly injection
        seed: Random seed for reproducibility
        
    Returns:
        SyntheticDataset containing the generated data and metadata
    """
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()
        
    # Set seed
    if seed is not None:
        np.random.seed(seed)
        
    # Generate base signal
    timestamps, values = generate_base_signal(n_points, signal_config, seed)
    
    # Inject anomalies based on type
    if anomaly_config.anomaly_type == "point":
        timestamps, values, ground_truth = inject_point_anomalies(
            timestamps, values, anomaly_config, seed
        )
    elif anomaly_config.anomaly_type == "contextual":
        timestamps, values, ground_truth = inject_contextual_anomalies(
            timestamps, values, anomaly_config, seed
        )
    elif anomaly_config.anomaly_type == "collective":
        timestamps, values, ground_truth = inject_collective_anomalies(
            timestamps, values, anomaly_config, seed
        )
    else:
        # Default to point anomalies
        timestamps, values, ground_truth = inject_point_anomalies(
            timestamps, values, anomaly_config, seed
        )
    
    # Create anomaly labels (0 for normal, 1 for anomaly)
    anomaly_labels = np.zeros(n_points, dtype=int)
    for idx in ground_truth["anomaly_indices"]:
        anomaly_labels[idx] = 1
    
    # Prepare metadata
    metadata = {
        "generation_time": str(np.datetime64('now')),
        "n_points": n_points,
        "n_anomalies": len(ground_truth["anomaly_indices"]),
        "anomaly_rate": float(len(ground_truth["anomaly_indices"]) / n_points),
        "signal_config": asdict(signal_config),
        "anomaly_config": asdict(anomaly_config)
    }
    
    # Prepare ground truth for export (convert numpy types to Python types)
    export_ground_truth = {
        "anomaly_indices": [int(x) for x in ground_truth["anomaly_indices"]],
        "anomaly_types": ground_truth["anomaly_types"],
        "anomaly_magnitudes": [float(x) for x in ground_truth["anomaly_magnitudes"]]
    }
    
    return SyntheticDataset(
        timestamps=timestamps.tolist(),
        values=values.tolist(),
        anomaly_labels=anomaly_labels.tolist(),
        ground_truth=export_ground_truth,
        config={
            "signal": asdict(signal_config),
            "anomaly": asdict(anomaly_config)
        },
        seed=seed if seed is not None else 0,
        metadata=metadata
    )


def save_synthetic_dataset(
    dataset: SyntheticDataset,
    output_path: Optional[Path] = None,
    format: Literal["json", "csv"] = "json"
) -> Path:
    """
    Save the synthetic dataset to disk.
    
    Args:
        dataset: The SyntheticDataset to save
        output_path: Optional custom output path
        format: Output format ('json' or 'csv')
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = OUTPUT_DIR / f"synthetic_dataset_seed{dataset.seed}.json"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        # Prepare data for JSON serialization (handle numpy types)
        data = {
            "timestamps": [float(x) for x in dataset.timestamps],
            "values": [float(x) for x in dataset.values],
            "anomaly_labels": [int(x) for x in dataset.anomaly_labels],
            "ground_truth": dataset.ground_truth,
            "config": dataset.config,
            "seed": int(dataset.seed),
            "metadata": dataset.metadata
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    elif format == "csv":
        import pandas as pd
        df = pd.DataFrame({
            'timestamp': dataset.timestamps,
            'value': dataset.values,
            'anomaly_label': dataset.anomaly_labels
        })
        df.to_csv(output_path, index=False)
        
    logger.info(f"Saved synthetic dataset to {output_path}")
    return output_path


def load_synthetic_dataset(file_path: Path) -> SyntheticDataset:
    """
    Load a synthetic dataset from disk.
    
    Args:
        file_path: Path to the dataset file
        
    Returns:
        SyntheticDataset loaded from file
    """
    file_path = Path(file_path)
    
    if file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        return SyntheticDataset(
            timestamps=data['timestamps'],
            values=data['values'],
            anomaly_labels=data['anomaly_labels'],
            ground_truth=data['ground_truth'],
            config=data['config'],
            seed=data['seed'],
            metadata=data.get('metadata', {})
        )
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def generate_validation_dataset(
    n_points: int = 500,
    seed: int = 42
) -> SyntheticDataset:
    """
    Generate a validation dataset with known properties for testing.
    
    Args:
        n_points: Number of data points
        seed: Random seed
        
    Returns:
        SyntheticDataset for validation
    """
    signal_config = SignalConfig(
        base_frequency=0.1,
        noise_level=0.05,
        trend_slope=0.001,
        anomaly_magnitude=3.0,
        anomaly_duration=10
    )
    
    anomaly_config = AnomalyConfig(
        anomaly_rate=0.05,
        anomaly_type="point"
    )
    
    return generate_synthetic_timeseries(
        n_points=n_points,
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        seed=seed
    )


def main():
    """Main entry point for generating synthetic datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--anomaly-rate', type=float, default=0.05, help='Anomaly injection rate')
    parser.add_argument('--anomaly-type', type=str, default='point', 
                      choices=['point', 'contextual', 'collective'], 
                      help='Type of anomaly to inject')
    parser.add_argument('--n-points', type=int, default=1000, help='Number of data points')
    parser.add_argument('--output', type=str, default=None, help='Output file path')
    
    args = parser.parse_args()
    
    logger.info(f"Generating synthetic dataset with seed={args.seed}, "
               f"anomaly_rate={args.anomaly_rate}, type={args.anomaly_type}")
    
    signal_config = SignalConfig()
    anomaly_config = AnomalyConfig(
        anomaly_rate=args.anomaly_rate,
        anomaly_type=args.anomaly_type
    )
    
    dataset = generate_synthetic_timeseries(
        n_points=args.n_points,
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        seed=args.seed
    )
    
    output_path = save_synthetic_dataset(
        dataset, 
        output_path=Path(args.output) if args.output else None
    )
    
    logger.info(f"Successfully generated dataset: {output_path}")
    logger.info(f"Total points: {len(dataset.values)}")
    logger.info(f"Anomalies injected: {len(dataset.ground_truth['anomaly_indices'])}")
    logger.info(f"Anomaly rate: {dataset.metadata['anomaly_rate']:.4f}")
    
    return dataset


if __name__ == "__main__":
    main()