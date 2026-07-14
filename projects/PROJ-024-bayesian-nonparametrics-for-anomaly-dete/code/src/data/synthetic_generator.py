"""
Synthetic Time Series Generator for Anomaly Detection.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for validation of the DP-GMM anomaly detector.

Implements FR-021 and FR-022:
- FR-021: Generate synthetic time series with known anomaly injection points
- FR-022: Provide independent ground-truth timestamps for validation
"""
import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal


@dataclass
class SignalConfig:
    """Configuration for signal generation."""
    base_frequency: float = 0.1
    noise_level: float = 0.05
    trend_slope: float = 0.0
    amplitude: float = 1.0
    signal_type: Literal['sine', 'linear', 'random_walk'] = 'sine'
    
    # Allow flexible logger-like access for callers expecting different method names
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            pass
        return _noop

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'point'
    magnitude: float = 3.0
    duration: int = 10
    start_index: Optional[int] = None
    end_index: Optional[int] = None


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    timestamps: List[float]
    values: List[float]
    ground_truth_anomalies: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    checksum: Optional[str] = None


def generate_base_signal(
    n_points: int,
    config: SignalConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series signal according to the configuration.
    
    Args:
        n_points: Number of data points to generate
        config: SignalConfig with signal parameters
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (timestamps, values) arrays
    """
    if seed is not None:
        np.random.seed(seed)
        
    timestamps = np.arange(n_points)
    values = np.zeros(n_points)
    
    if config.signal_type == 'sine':
        # Sine wave with optional trend and noise
        base = config.amplitude * np.sin(2 * np.pi * config.base_frequency * timestamps)
        trend = config.trend_slope * timestamps
        noise = np.random.normal(0, config.noise_level, n_points)
        values = base + trend + noise
        
    elif config.signal_type == 'linear':
        # Linear trend with noise
        trend = config.trend_slope * timestamps
        noise = np.random.normal(0, config.noise_level, n_points)
        values = trend + noise
        
    elif config.signal_type == 'random_walk':
        # Random walk process
        steps = np.random.normal(config.trend_slope, config.noise_level, n_points)
        values = np.cumsum(steps)
    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")
        
    return timestamps, values

    return t, signal

def inject_point_anomalies(
    timestamps: np.ndarray,
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject point anomalies (spikes) into the time series.
    
    Args:
        timestamps: Array of timestamps
        values: Array of signal values
        anomaly_config: Configuration for anomaly injection
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_values, ground_truth_list)
    """
    if seed is not None:
        np.random.seed(seed)
        
    values = values.copy()
    ground_truth = []
    
    # Determine anomaly indices
    if anomaly_config.start_index is not None:
        start_idx = anomaly_config.start_index
        end_idx = anomaly_config.end_index or (start_idx + anomaly_config.duration)
    else:
        # Random location in the middle 50% of the series
        mid = len(values) // 2
        available = mid - 10
        start_idx = np.random.randint(10, available)
        end_idx = start_idx + anomaly_config.duration
        
    # Inject anomalies
    for i in range(start_idx, min(end_idx, len(values))):
        # Random direction for spike
        direction = np.random.choice([-1, 1])
        values[i] += direction * anomaly_config.magnitude * np.std(values)
        
        ground_truth.append({
            'type': 'point',
            'start_index': int(i),
            'end_index': int(i),
            'magnitude': float(direction * anomaly_config.magnitude * np.std(values)),
            'timestamp': float(timestamps[i])
        })
        
    return values, ground_truth


def inject_contextual_anomalies(
    timestamps: np.ndarray,
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject contextual anomalies (values that are anomalous in context).
    
    Args:
        timestamps: Array of timestamps
        values: Array of signal values
        anomaly_config: Configuration for anomaly injection
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_values, ground_truth_list)
    """
    if seed is not None:
        np.random.seed(seed)
        
    values = values.copy()
    ground_truth = []
    
    # Determine anomaly window
    if anomaly_config.start_index is not None:
        start_idx = anomaly_config.start_index
        end_idx = anomaly_config.end_index or (start_idx + anomaly_config.duration)
    else:
        mid = len(values) // 2
        available = mid - 10
        start_idx = np.random.randint(10, available)
        end_idx = start_idx + anomaly_config.duration
        
    # Calculate local statistics for context
    local_window = 20
    local_mean = np.mean(values[max(0, start_idx-local_window):start_idx])
    local_std = np.std(values[max(0, start_idx-local_window):start_idx])
    
    # Inject contextual anomalies (shifted from local context)
    for i in range(start_idx, min(end_idx, len(values))):
        shift = anomaly_config.magnitude * local_std
        values[i] = local_mean + shift
        
        ground_truth.append({
            'type': 'contextual',
            'start_index': int(i),
            'end_index': int(i),
            'magnitude': float(shift),
            'timestamp': float(timestamps[i]),
            'local_mean': float(local_mean),
            'local_std': float(local_std)
        })
        
    return values, ground_truth


def inject_collective_anomalies(
    timestamps: np.ndarray,
    values: np.ndarray,
    anomaly_config: AnomalyConfig,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject collective anomalies (a sequence of points that are anomalous together).
    
    Args:
        timestamps: Array of timestamps
        values: Array of signal values
        anomaly_config: Configuration for anomaly injection
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (modified_values, ground_truth_list)
    """
    if seed is not None:
        np.random.seed(seed)
        
    values = values.copy()
    ground_truth = []
    
    # Determine anomaly window
    if anomaly_config.start_index is not None:
        start_idx = anomaly_config.start_index
        end_idx = anomaly_config.end_index or (start_idx + anomaly_config.duration)
    else:
        mid = len(values) // 2
        available = mid - 10
        start_idx = np.random.randint(10, available)
        end_idx = start_idx + anomaly_config.duration
        
    # Generate a collective shift (e.g., level shift or regime change)
    shift = anomaly_config.magnitude * np.std(values)
    direction = np.random.choice([-1, 1])
    shift *= direction
    
    for i in range(start_idx, min(end_idx, len(values))):
        values[i] += shift
        
    ground_truth.append({
        'type': 'collective',
        'start_index': int(start_idx),
        'end_index': int(min(end_idx, len(values)) - 1),
        'magnitude': float(shift),
        'timestamp_start': float(timestamps[start_idx]),
        'timestamp_end': float(timestamps[min(end_idx, len(values)) - 1])
    })
    
    return values, ground_truth


def generate_synthetic_timeseries(
    n_points: int = 1000,
    signal_config: Optional[SignalConfig] = None,
    anomaly_configs: Optional[List[AnomalyConfig]] = None,
    seed: Optional[int] = None,
    output_path: Optional[Path] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with anomalies.
    
    Args:
        n_points: Total number of data points
        signal_config: Configuration for base signal
        anomaly_configs: List of anomaly configurations to inject
        seed: Random seed for reproducibility
        output_path: Optional path to save the dataset
        
    Returns:
        SyntheticDataset object containing the generated data
    """
    if seed is not None:
        np.random.seed(seed)
        
    if signal_config is None:
        signal_config = SignalConfig()
        
    if anomaly_configs is None:
        # Default: one point anomaly in the middle
        anomaly_configs = [
            AnomalyConfig(
                anomaly_type='point',
                magnitude=3.0,
                duration=5,
                start_index=n_points // 2
            )
        ]
        
    # Generate base signal
    timestamps, values = generate_base_signal(n_points, signal_config, seed)
    
    # Inject anomalies
    all_ground_truth = []
    for anom_config in anomaly_configs:
        if anom_config.anomaly_type == 'point':
            values, gt = inject_point_anomalies(timestamps, values, anom_config, seed)
        elif anom_config.anomaly_type == 'contextual':
            values, gt = inject_contextual_anomalies(timestamps, values, anom_config, seed)
        elif anom_config.anomaly_type == 'collective':
            values, gt = inject_collective_anomalies(timestamps, values, anom_config, seed)
        else:
            raise ValueError(f"Unknown anomaly type: {anom_config.anomaly_type}")
            
        all_ground_truth.extend(gt)
        
    # Create dataset object
    dataset = SyntheticDataset(
        timestamps=timestamps.tolist(),
        values=values.tolist(),
        ground_truth_anomalies=all_ground_truth,
        metadata={
            'n_points': n_points,
            'signal_type': signal_config.signal_type,
            'anomaly_count': len(anomaly_configs),
            'seed': seed,
            'generated_at': str(np.datetime64('now'))
        }
    )
    
    # Save if path provided
    if output_path is not None:
        save_synthetic_dataset(dataset, output_path)
        
    return dataset


def save_synthetic_dataset(dataset: SyntheticDataset, path: Path) -> None:
    """
    Save a synthetic dataset to disk as JSON.
    
    Args:
        dataset: The dataset to save
        path: Output file path
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data_dict = {
        'timestamps': dataset.timestamps,
        'values': dataset.values,
        'ground_truth': dataset.ground_truth_anomalies,
        'metadata': dataset.metadata
    }
    
    with open(path, 'w') as f:
        json.dump(data_dict, f, indent=2)
        
    print(f"Saved synthetic dataset to {path}")


def load_synthetic_dataset(path: Path) -> SyntheticDataset:
    """
    Load a synthetic dataset from disk.
    
    Args:
        path: Path to the JSON file
        
    Returns:
        SyntheticDataset object
    """
    with open(path, 'r') as f:
        data = json.load(f)
        
    return SyntheticDataset(
        timestamps=data['timestamps'],
        values=data['values'],
        ground_truth_anomalies=data['ground_truth'],
        metadata=data['metadata']
    )


def generate_validation_dataset(
    n_points: int = 1000,
    seed: int = 42
) -> SyntheticDataset:
    """
    Generate a standard validation dataset for testing the pipeline.
    
    Args:
        n_points: Number of points
        seed: Random seed
        
    Returns:
        SyntheticDataset with known anomaly properties
    """
    signal_cfg = SignalConfig(
        base_frequency=0.05,
        noise_level=0.1,
        trend_slope=0.0,
        amplitude=1.0,
        signal_type='sine'
    )
    
    # Create a mix of anomaly types for robust testing
    anomaly_cfgs = [
        AnomalyConfig(
            anomaly_type='point',
            magnitude=4.0,
            duration=3,
            start_index=int(n_points * 0.3)
        ),
        AnomalyConfig(
            anomaly_type='collective',
            magnitude=2.5,
            duration=20,
            start_index=int(n_points * 0.7)
        )
    ]
    
    return generate_synthetic_timeseries(
        n_points=n_points,
        signal_config=signal_cfg,
        anomaly_configs=anomaly_cfgs,
        seed=seed,
        output_path=Path('data/processed/results/validation_synthetic.json')
    )


def main():
    """Main entry point for generating synthetic datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--n_points', type=int, default=1000, help='Number of data points')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_data.json',
                      help='Output file path')
    parser.add_argument('--type', type=str, default='sine', choices=['sine', 'linear', 'random_walk'],
                      help='Signal type')
    parser.add_argument('--anomaly-type', type=str, default='point', 
                      choices=['point', 'contextual', 'collective'],
                      help='Anomaly type to inject')
    
    args = parser.parse_args()
    
    signal_cfg = SignalConfig(signal_type=args.type)
    anomaly_cfg = AnomalyConfig(
        anomaly_type=args.anomaly_type,
        magnitude=3.5,
        duration=10,
        start_index=args.n_points // 2
    )
    
    dataset = generate_synthetic_timeseries(
        n_points=args.n_points,
        signal_config=signal_cfg,
        anomaly_configs=[anomaly_cfg],
        seed=args.seed,
        output_path=Path(args.output)
    )
    
    print(f"Generated {len(dataset.timestamps)} points with {len(dataset.ground_truth_anomalies)} anomalies")
    print(f"Output saved to: {args.output}")


if __name__ == '__main__':
    main()