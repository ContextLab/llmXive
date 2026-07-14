"""
Synthetic time-series generator for anomaly detection research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps as required by FR-021 and FR-022.

Used for simulation studies and as a fallback if real data search fails.
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    signal_type: Literal['sine', 'linear', 'random_walk', 'arima'] = 'sine'
    amplitude: float = 1.0
    frequency: float = 0.1
    noise_std: float = 0.1
    trend_slope: float = 0.0
    # Allow any logger-like attribute access gracefully
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'point'
    magnitude: float = 3.0
    duration: int = 10
    start_index: Optional[int] = None  # If None, will be randomized
    rate: float = 0.05  # Anomaly rate for random generation

@dataclass
class SyntheticDataset:
    """Container for synthetic dataset and metadata."""
    data: np.ndarray
    timestamps: np.ndarray
    ground_truth: Dict[str, Any]
    config: Dict[str, Any]

def generate_base_signal(n_points: int, config: SignalConfig, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a base time-series signal."""
    t = np.arange(n_points)
    
    if config.signal_type == 'sine':
        base = config.amplitude * np.sin(2 * np.pi * config.frequency * t)
    elif config.signal_type == 'linear':
        base = config.trend_slope * t
    elif config.signal_type == 'random_walk':
        steps = rng.normal(0, config.noise_std, n_points)
        base = np.cumsum(steps)
    elif config.signal_type == 'arima':
        # Simple AR(1) process
        base = np.zeros(n_points)
        phi = 0.9
        for i in range(1, n_points):
            base[i] = phi * base[i-1] + rng.normal(0, config.noise_std)
    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")
    
    noise = rng.normal(0, config.noise_std, n_points)
    signal = base + noise
    
    return signal, t

def inject_point_anomalies(
    data: np.ndarray, 
    config: AnomalyConfig, 
    rng: np.random.Generator
) -> Tuple[np.ndarray, List[int]]:
    """Inject point anomalies (single abrupt shifts)."""
    n_points = len(data)
    anomaly_indices = []
    
    if config.start_index is not None:
        # Fixed location for reproducibility
        indices = [config.start_index]
    else:
        # Random location based on rate
        n_anomalies = int(n_points * config.rate)
        indices = rng.choice(range(10, n_points - 10), size=n_anomalies, replace=False)
    
    for idx in indices:
        # Create abrupt shift
        shift = rng.choice([-1, 1]) * config.magnitude * rng.uniform(0.8, 1.2)
        data[idx] += shift
        anomaly_indices.append(idx)
    
    return data, anomaly_indices

def inject_contextual_anomalies(
    data: np.ndarray, 
    config: AnomalyConfig, 
    rng: np.random.Generator
) -> Tuple[np.ndarray, List[int]]:
    """Inject contextual anomalies (values abnormal in context)."""
    n_points = len(data)
    anomaly_indices = []
    
    if config.start_index is not None:
        start = config.start_index
        end = min(start + config.duration, n_points)
        indices = list(range(start, end))
    else:
        n_anomalies = int(n_points * config.rate)
        start = rng.integers(10, n_points - 10)
        indices = list(range(start, min(start + config.duration, n_points)))
    
    # Inject values that are contextually abnormal (e.g., flat line in oscillating signal)
    for idx in indices:
        data[idx] = rng.normal(0, 0.01)  # Near-zero in a varying signal
        anomaly_indices.append(idx)
    
    return data, anomaly_indices

def inject_collective_anomalies(
    data: np.ndarray, 
    config: AnomalyConfig, 
    rng: np.random.Generator
) -> Tuple[np.ndarray, List[int]]:
    """Inject collective anomalies (sequence of abnormal behavior)."""
    n_points = len(data)
    anomaly_indices = []
    
    if config.start_index is not None:
        start = config.start_index
    else:
        start = rng.integers(20, n_points - config.duration - 20)
    
    end = min(start + config.duration, n_points)
    segment = data[start:end]
    
    # Create a collective shift (e.g., mean shift)
    shift = rng.choice([-1, 1]) * config.magnitude
    data[start:end] = segment + shift
    
    anomaly_indices = list(range(start, end))
    
    return data, anomaly_indices

def generate_synthetic_timeseries(
    n_points: int = 1000,
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None,
    seed: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time-series dataset with anomalies.
    
    Args:
        n_points: Number of time points
        signal_config: Configuration for base signal
        anomaly_config: Configuration for anomaly injection
        seed: Random seed for reproducibility
        
    Returns:
        SyntheticDataset containing data, timestamps, and ground truth
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    
    # Default configs
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()
    
    # Generate base signal
    data, timestamps = generate_base_signal(n_points, signal_config, rng)
    
    # Inject anomalies
    anomaly_type = anomaly_config.anomaly_type
    if anomaly_type == 'point':
        data, gt_indices = inject_point_anomalies(data, anomaly_config, rng)
    elif anomaly_type == 'contextual':
        data, gt_indices = inject_contextual_anomalies(data, anomaly_config, rng)
    elif anomaly_type == 'collective':
        data, gt_indices = inject_collective_anomalies(data, anomaly_config, rng)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_type}")
    
    # Build ground truth
    ground_truth = {
        'anomaly_type': anomaly_type,
        'anomaly_indices': gt_indices,
        'anomaly_count': len(gt_indices),
        'anomaly_rate': len(gt_indices) / n_points,
        'signal_type': signal_config.signal_type,
        'n_points': n_points
    }
    
    # Build config snapshot
    config_snapshot = {
        'signal': asdict(signal_config),
        'anomaly': asdict(anomaly_config),
        'seed': seed
    }
    
    return SyntheticDataset(
        data=data,
        timestamps=timestamps,
        ground_truth=ground_truth,
        config=config_snapshot
    )

def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """Save synthetic dataset to disk as CSV and JSON metadata."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save data as CSV
    csv_path = output_path.with_suffix('.csv')
    with open(csv_path, 'w') as f:
        f.write('timestamp,value,is_anomaly\n')
        for t, v in zip(dataset.timestamps, dataset.data):
            is_anom = 1 if int(t) in dataset.ground_truth['anomaly_indices'] else 0
            f.write(f'{t},{v:.6f},{is_anom}\n')
    
    # Save metadata as JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump({
            'ground_truth': dataset.ground_truth,
            'config': dataset.config,
            'data_path': str(csv_path)
        }, f, indent=2)
    
    logger.info(f"Saved synthetic dataset to {csv_path}")
    logger.info(f"Saved metadata to {json_path}")

def load_synthetic_dataset(data_path: str) -> SyntheticDataset:
    """Load synthetic dataset from disk."""
    data_path = Path(data_path)
    csv_path = data_path.with_suffix('.csv')
    json_path = data_path.with_suffix('.json')
    
    if not csv_path.exists() or not json_path.exists():
        raise FileNotFoundError(f"Dataset files not found: {csv_path}, {json_path}")
    
    # Load metadata
    with open(json_path, 'r') as f:
        metadata = json.load(f)
    
    # Load data
    timestamps = []
    values = []
    with open(csv_path, 'r') as f:
        header = f.readline()  # Skip header
        for line in f:
            parts = line.strip().split(',')
            timestamps.append(float(parts[0]))
            values.append(float(parts[1]))
    
    return SyntheticDataset(
        data=np.array(values),
        timestamps=np.array(timestamps),
        ground_truth=metadata['ground_truth'],
        config=metadata['config']
    )

def generate_validation_dataset(
    n_points: int = 500,
    seed: int = 42
) -> SyntheticDataset:
    """Generate a validation dataset with known properties."""
    signal_config = SignalConfig(
        signal_type='sine',
        amplitude=1.0,
        frequency=0.05,
        noise_std=0.1
    )
    
    # Create anomalies at known locations for validation
    anomaly_config = AnomalyConfig(
        anomaly_type='point',
        magnitude=3.0,
        start_index=250  # Known anomaly location
    )
    
    return generate_synthetic_timeseries(
        n_points=n_points,
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        seed=seed
    )

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic time-series data for anomaly detection'
    )
    parser.add_argument('--n_points', type=int, default=1000, help='Number of data points')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_data.csv', help='Output file path')
    parser.add_argument('--type', type=str, default='sine', choices=['sine', 'linear', 'random_walk'], help='Signal type')
    parser.add_argument('--anomaly-type', type=str, default='point', choices=['point', 'contextual', 'collective'], help='Anomaly type')
    parser.add_argument('--anomaly-magnitude', type=float, default=3.0, help='Anomaly magnitude')
    parser.add_argument('--anomaly-rate', type=float, default=0.05, help='Anomaly rate (fraction of points)')
    
    args = parser.parse_args()
    
    logger.info(f"Generating synthetic dataset: {args.type} signal with {args.anomaly_type} anomalies")
    
    signal_config = SignalConfig(
        signal_type=args.type,
        noise_std=0.1
    )
    
    anomaly_config = AnomalyConfig(
        anomaly_type=args.anomaly_type,
        magnitude=args.anomaly_magnitude,
        rate=args.anomaly_rate
    )
    
    dataset = generate_synthetic_timeseries(
        n_points=args.n_points,
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        seed=args.seed
    )
    
    save_synthetic_dataset(dataset, args.output)
    
    logger.info(f"Dataset generated successfully: {len(dataset.data)} points, {dataset.ground_truth['anomaly_count']} anomalies")

if __name__ == '__main__':
    main()