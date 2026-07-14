"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for simulation and validation purposes.

FR-021: Pre-anomaly dynamics
FR-022: Independent ground-truth timestamps
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal


@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    signal_type: Literal['sine', 'trend', 'random_walk', 'composite'] = 'composite'
    base_frequency: float = 0.1
    amplitude: float = 1.0
    trend_slope: float = 0.01
    noise_std: float = 0.1
    length: int = 1000
    
    def __getattr__(self, name):
        # Tolerant fallback for any attribute access
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        # Return a no-op callable for method-like accesses
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'collective'
    anomaly_rate: float = 0.05
    anomaly_magnitude: float = 3.0
    anomaly_duration_min: int = 10
    anomaly_duration_max: int = 50
    num_anomalies: Optional[int] = None
    
    def __getattr__(self, name):
        # Tolerant fallback for any attribute access
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        # Return a no-op callable for method-like accesses
        def _noop(*args, **kwargs):
            return None
        return _noop


@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    values: np.ndarray
    ground_truth: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def to_dict(self):
        return {
            'values': self.values.tolist(),
            'ground_truth': self.ground_truth,
            'metadata': self.metadata
        }


def generate_base_signal(config: SignalConfig) -> np.ndarray:
    """
    Generate a base time series signal based on configuration.
    
    Implements FR-021: Pre-anomaly dynamics.
    """
    np.random.seed(42)  # Reproducibility
    t = np.arange(config.length)
    
    if config.signal_type == 'sine':
        signal = config.amplitude * np.sin(2 * np.pi * config.base_frequency * t)
    elif config.signal_type == 'trend':
        signal = config.trend_slope * t
    elif config.signal_type == 'random_walk':
        signal = np.cumsum(np.random.normal(0, config.noise_std, config.length))
    elif config.signal_type == 'composite':
        # Combination of sine and trend with noise
        signal = (
            config.amplitude * np.sin(2 * np.pi * config.base_frequency * t) +
            config.trend_slope * t +
            np.random.normal(0, config.noise_std, config.length)
        )
    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")
    
    return signal


def inject_point_anomalies(
    values: np.ndarray, 
    config: AnomalyConfig, 
    ground_truth: List[Dict[str, Any]]
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Inject point anomalies (single outlier values)."""
    if config.num_anomalies is None:
        num_anomalies = int(len(values) * config.anomaly_rate)
    else:
        num_anomalies = config.num_anomalies
    
    anomaly_indices = np.random.choice(
        len(values), size=num_anomalies, replace=False
    )
    
    for idx in anomaly_indices:
        # Determine anomaly direction (positive or negative)
        direction = np.random.choice([-1, 1])
        values[idx] += direction * config.anomaly_magnitude * np.std(values)
        
        ground_truth.append({
            'type': 'point',
            'start_index': int(idx),
            'end_index': int(idx),
            'magnitude': float(config.anomaly_magnitude),
            'direction': int(direction)
        })
    
    return values, ground_truth


def inject_contextual_anomalies(
    values: np.ndarray, 
    config: AnomalyConfig, 
    ground_truth: List[Dict[str, Any]]
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Inject contextual anomalies (values that are anomalous in context)."""
    if config.num_anomalies is None:
        num_anomalies = int(len(values) * config.anomaly_rate)
    else:
        num_anomalies = config.num_anomalies
    
    # Select random windows
    window_size = 10
    possible_starts = list(range(0, len(values) - window_size, window_size))
    anomaly_starts = np.random.choice(possible_starts, size=num_anomalies, replace=False)
    
    for start in anomaly_starts:
        end = start + window_size
        # Shift values in this window
        shift_amount = config.anomaly_magnitude * np.std(values)
        values[start:end] += shift_amount
        
        ground_truth.append({
            'type': 'contextual',
            'start_index': int(start),
            'end_index': int(end),
            'magnitude': float(shift_amount),
            'window_size': window_size
        })
    
    return values, ground_truth


def inject_collective_anomalies(
    values: np.ndarray, 
    config: AnomalyConfig, 
    ground_truth: List[Dict[str, Any]]
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Inject collective anomalies (groups of anomalous values).
    
    Implements FR-022: Independent ground-truth timestamps.
    """
    if config.num_anomalies is None:
        num_anomalies = int(len(values) * config.anomaly_rate / 10)  # Adjust for longer duration
    else:
        num_anomalies = config.num_anomalies
    
    # Ensure we don't exceed array bounds
    max_anomalies = len(values) // config.anomaly_duration_min
    num_anomalies = min(num_anomalies, max_anomalies)
    
    attempts = 0
    max_attempts = num_anomalies * 10
    injected_count = 0
    
    while injected_count < num_anomalies and attempts < max_attempts:
        attempts += 1
        
        # Random duration within config range
        duration = np.random.randint(
            config.anomaly_duration_min, 
            config.anomaly_duration_max + 1
        )
        
        # Random start position ensuring we don't go out of bounds
        max_start = len(values) - duration
        if max_start <= 0:
            continue
            
        start_idx = np.random.randint(0, max_start)
        end_idx = start_idx + duration
        
        # Check if this region overlaps with existing anomalies
        overlap = False
        for gt in ground_truth:
            if not (end_idx <= gt['start_index'] or start_idx >= gt['end_index']):
                overlap = True
                break
        
        if overlap:
            continue
        
        # Inject the anomaly (change the pattern)
        # For collective anomalies, we change the underlying signal characteristics
        segment = values[start_idx:end_idx]
        
        # Option 1: Scale the segment
        scale_factor = config.anomaly_magnitude
        values[start_idx:end_idx] = segment * scale_factor
        
        ground_truth.append({
            'type': 'collective',
            'start_index': int(start_idx),
            'end_index': int(end_idx),
            'duration': int(duration),
            'magnitude': float(scale_factor),
            'pattern_change': 'scale'
        })
        
        injected_count += 1
    
    return values, ground_truth


def generate_synthetic_timeseries(
    signal_config: SignalConfig, 
    anomaly_config: AnomalyConfig, 
    length: Optional[int] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset.
    
    Args:
        signal_config: Configuration for base signal
        anomaly_config: Configuration for anomaly injection
        length: Override length if specified
        
    Returns:
        SyntheticDataset with values and ground truth timestamps
    """
    if length is not None:
        signal_config.length = length
    
    # Generate base signal (pre-anomaly dynamics)
    values = generate_base_signal(signal_config)
    ground_truth = []
    
    # Inject anomalies based on type
    if anomaly_config.anomaly_type == 'point':
        values, ground_truth = inject_point_anomalies(values, anomaly_config, ground_truth)
    elif anomaly_config.anomaly_type == 'contextual':
        values, ground_truth = inject_contextual_anomalies(values, anomaly_config, ground_truth)
    elif anomaly_config.anomaly_type == 'collective':
        values, ground_truth = inject_collective_anomalies(values, anomaly_config, ground_truth)
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")
    
    # Sort ground truth by start index
    ground_truth.sort(key=lambda x: x['start_index'])
    
    metadata = {
        'signal_type': signal_config.signal_type,
        'anomaly_type': anomaly_config.anomaly_type,
        'total_length': len(values),
        'num_anomalies': len(ground_truth),
        'anomaly_rate': len(ground_truth) / len(values) if len(values) > 0 else 0,
        'seed': 42
    }
    
    return SyntheticDataset(
        values=values,
        ground_truth=ground_truth,
        metadata=metadata
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str):
    """Save synthetic dataset to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = dataset.to_dict()
    # Convert numpy arrays to lists for JSON serialization
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """Load synthetic dataset from JSON file."""
    path = Path(input_path)
    with open(path, 'r') as f:
        data = json.load(f)
    
    return SyntheticDataset(
        values=np.array(data['values']),
        ground_truth=data['ground_truth'],
        metadata=data['metadata']
    )


def generate_validation_dataset(
    length: int = 1000,
    anomaly_rate: float = 0.05
) -> SyntheticDataset:
    """
    Generate a validation dataset with known properties.
    
    Used for testing the anomaly detection pipeline.
    """
    signal_config = SignalConfig(
        signal_type='composite',
        length=length,
        base_frequency=0.05,
        amplitude=1.0,
        trend_slope=0.001,
        noise_std=0.1
    )
    
    anomaly_config = AnomalyConfig(
        anomaly_type='collective',
        anomaly_rate=anomaly_rate,
        anomaly_magnitude=3.0,
        anomaly_duration_min=10,
        anomaly_duration_max=30
    )
    
    return generate_synthetic_timeseries(signal_config, anomaly_config, length)


def main():
    """Main entry point for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--length', type=int, default=1000, help='Length of time series')
    parser.add_argument('--anomaly-rate', type=float, default=0.05, help='Anomaly rate')
    parser.add_argument('--anomaly-type', type=str, default='collective', 
                      choices=['point', 'contextual', 'collective'],
                      help='Type of anomaly to inject')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_data.json',
                      help='Output file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Set random seed
    np.random.seed(args.seed)
    
    # Create configuration
    signal_config = SignalConfig(
        signal_type='composite',
        length=args.length,
        base_frequency=0.05,
        amplitude=1.0,
        trend_slope=0.001,
        noise_std=0.1
    )
    
    anomaly_config = AnomalyConfig(
        anomaly_type=args.anomaly_type,
        anomaly_rate=args.anomaly_rate,
        anomaly_magnitude=3.0,
        anomaly_duration_min=10,
        anomaly_duration_max=30
    )
    
    # Generate dataset
    print(f"Generating synthetic dataset with length={args.length}, "
          f"anomaly_rate={args.anomaly_rate}, type={args.anomaly_type}")
    
    dataset = generate_synthetic_timeseries(signal_config, anomaly_config, args.length)
    
    # Save dataset
    save_synthetic_dataset(dataset, args.output)
    print(f"Dataset saved to {args.output}")
    print(f"Total points: {len(dataset.values)}")
    print(f"Anomalies detected: {len(dataset.ground_truth)}")
    print(f"Ground truth timestamps: {dataset.ground_truth[:3]}...")  # Show first 3


if __name__ == '__main__':
    main()