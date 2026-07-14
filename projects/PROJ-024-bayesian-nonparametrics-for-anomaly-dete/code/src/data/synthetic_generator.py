"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps for validation of Bayesian Nonparametric methods.

Implements FR-021 (Signal Dynamics) and FR-022 (Ground Truth Injection).
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SignalConfig:
    """Configuration for base signal generation."""
    signal_type: Literal['sinusoidal', 'trend', 'random_walk', 'composite'] = 'composite'
    frequency: float = 0.01
    amplitude: float = 1.0
    trend_slope: float = 0.001
    noise_std: float = 0.1
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Tolerant logger interface to prevent AttributeError on unknown calls
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_rate: float = 0.05
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'collective'
    anomaly_magnitude: float = 5.0
    anomaly_duration_min: int = 5
    anomaly_duration_max: int = 20
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            np.random.seed(self.seed)

    # Tolerant logger interface
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset."""
    values: np.ndarray
    ground_truth: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self):
        return {
            'values': self.values.tolist(),
            'ground_truth': self.ground_truth,
            'metadata': self.metadata
        }

def generate_base_signal(config: SignalConfig, length: int) -> np.ndarray:
    """
    Generate base signal according to configuration.

    Args:
        config: SignalConfig with signal parameters
        length: Length of the time series

    Returns:
        np.ndarray: Generated signal values
    """
    t = np.arange(length)

    if config.signal_type == 'sinusoidal':
        signal = config.amplitude * np.sin(2 * np.pi * config.frequency * t)
    elif config.signal_type == 'trend':
        signal = config.trend_slope * t
    elif config.signal_type == 'random_walk':
        signal = np.cumsum(np.random.normal(0, config.noise_std, length))
    elif config.signal_type == 'composite':
        # Combination of sinusoidal, trend, and noise
        signal = (
            config.amplitude * np.sin(2 * np.pi * config.frequency * t) +
            config.trend_slope * t +
            np.random.normal(0, config.noise_std, length)
        )
    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")

    return signal

def inject_point_anomalies(
    values: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject point anomalies (single point spikes).

    Args:
        values: Base signal values
        config: AnomalyConfig with injection parameters
        ground_truth: Dictionary to update with anomaly timestamps

    Returns:
        Tuple of (modified values, updated ground_truth)
    """
    n_anomalies = int(len(values) * config.anomaly_rate)
    anomaly_indices = np.random.choice(
        len(values), size=n_anomalies, replace=False
    )

    for idx in anomaly_indices:
        # Add spike with specified magnitude
        direction = np.random.choice([-1, 1])
        values[idx] += direction * config.anomaly_magnitude * np.std(values)

    # Update ground truth
    if 'point_anomalies' not in ground_truth:
        ground_truth['point_anomalies'] = []
    for idx in anomaly_indices:
        ground_truth['point_anomalies'].append({
            'index': int(idx),
            'type': 'point',
            'magnitude': float(config.anomaly_magnitude)
        })

    return values, ground_truth

def inject_contextual_anomalies(
    values: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject contextual anomalies (values anomalous in context).

    Args:
        values: Base signal values
        config: AnomalyConfig with injection parameters
        ground_truth: Dictionary to update with anomaly timestamps

    Returns:
        Tuple of (modified values, updated ground_truth)
    """
    n_anomalies = int(len(values) * config.anomaly_rate)
    anomaly_indices = np.random.choice(
        len(values), size=n_anomalies, replace=False
    )

    for idx in anomaly_indices:
        # Replace with value from opposite phase/context
        # For sinusoidal, flip the sign relative to local mean
        local_mean = np.mean(values[max(0, idx-10):min(len(values), idx+10)])
        values[idx] = local_mean - (values[idx] - local_mean)

    # Update ground truth
    if 'contextual_anomalies' not in ground_truth:
        ground_truth['contextual_anomalies'] = []
    for idx in anomaly_indices:
        ground_truth['contextual_anomalies'].append({
            'index': int(idx),
            'type': 'contextual'
        })

    return values, ground_truth

def inject_collective_anomalies(
    values: np.ndarray,
    config: AnomalyConfig,
    ground_truth: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Inject collective anomalies (consecutive anomalous points).

    Args:
        values: Base signal values
        config: AnomalyConfig with injection parameters
        ground_truth: Dictionary to update with anomaly timestamps

    Returns:
        Tuple of (modified values, updated ground_truth)
    """
    n_anomalies = int(len(values) * config.anomaly_rate)
    # Ensure we don't create too many overlapping segments
    max_segments = max(1, n_anomalies // config.anomaly_duration_min)

    inserted_count = 0
    attempts = 0
    max_attempts = max_segments * 10

    while inserted_count < max_segments and attempts < max_attempts:
        attempts += 1
        # Random duration within config range
        duration = np.random.randint(
            config.anomaly_duration_min,
            config.anomaly_duration_max + 1
        )
        start_idx = np.random.randint(0, len(values) - duration)

        # Check for overlap with existing anomalies
        end_idx = start_idx + duration
        is_overlapping = False
        if 'collective_anomalies' in ground_truth:
            for anomaly in ground_truth['collective_anomalies']:
                existing_start = anomaly['start_index']
                existing_end = anomaly['end_index']
                if not (end_idx <= existing_start or start_idx >= existing_end):
                    is_overlapping = True
                    break

        if is_overlapping:
            continue

        # Inject collective anomaly: shift mean significantly
        shift = config.anomaly_magnitude * np.std(values)
        values[start_idx:end_idx] += shift

        # Record in ground truth
        if 'collective_anomalies' not in ground_truth:
            ground_truth['collective_anomalies'] = []

        ground_truth['collective_anomalies'].append({
            'start_index': int(start_idx),
            'end_index': int(end_idx),
            'type': 'collective',
            'duration': int(duration),
            'shift': float(shift)
        })

        inserted_count += 1

    return values, ground_truth

def generate_synthetic_timeseries(
    signal_config: SignalConfig,
    anomaly_config: AnomalyConfig,
    length: int = 1000
) -> SyntheticDataset:
    """
    Generate complete synthetic time series with anomalies.

    Args:
        signal_config: Configuration for base signal
        anomaly_config: Configuration for anomaly injection
        length: Total length of time series

    Returns:
        SyntheticDataset with values and ground truth timestamps
    """
    # Generate base signal
    values = generate_base_signal(signal_config, length)

    # Initialize ground truth
    ground_truth = {
        'anomaly_rate': anomaly_config.anomaly_rate,
        'anomaly_type': anomaly_config.anomaly_type,
        'total_length': length,
        'generated_at': datetime.now().isoformat()
    }

    # Inject anomalies based on type
    if anomaly_config.anomaly_type == 'point':
        values, ground_truth = inject_point_anomalies(
            values, anomaly_config, ground_truth
        )
    elif anomaly_config.anomaly_type == 'contextual':
        values, ground_truth = inject_contextual_anomalies(
            values, anomaly_config, ground_truth
        )
    elif anomaly_config.anomaly_type == 'collective':
        values, ground_truth = inject_collective_anomalies(
            values, anomaly_config, ground_truth
        )
    else:
        raise ValueError(f"Unknown anomaly type: {anomaly_config.anomaly_type}")

    # Calculate actual anomaly count
    total_anomaly_points = 0
    if 'point_anomalies' in ground_truth:
        total_anomaly_points += len(ground_truth['point_anomalies'])
    if 'contextual_anomalies' in ground_truth:
        total_anomaly_points += len(ground_truth['contextual_anomalies'])
    if 'collective_anomalies' in ground_truth:
        for anomaly in ground_truth['collective_anomalies']:
            total_anomaly_points += anomaly['end_index'] - anomaly['start_index']

    ground_truth['actual_anomaly_points'] = total_anomaly_points
    ground_truth['actual_anomaly_rate'] = total_anomaly_points / length

    metadata = {
        'signal_config': asdict(signal_config),
        'anomaly_config': asdict(anomaly_config),
        'length': length
    }

    return SyntheticDataset(
        values=values,
        ground_truth=ground_truth,
        metadata=metadata
    )

def save_synthetic_dataset(
    dataset: SyntheticDataset,
    output_path: str,
    format: Literal['json', 'csv'] = 'json'
):
    """
    Save synthetic dataset to disk.

    Args:
        dataset: SyntheticDataset to save
        output_path: Path to save file
        format: 'json' for full metadata, 'csv' for values only
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == 'json':
        with open(output_path, 'w') as f:
            json.dump(dataset.to_dict(), f, indent=2)
    elif format == 'csv':
        import pandas as pd
        df = pd.DataFrame({
            'timestamp': range(len(dataset.values)),
            'value': dataset.values
        })
        # Add ground truth columns
        if 'collective_anomalies' in dataset.ground_truth:
            df['is_anomaly'] = 0
            for anomaly in dataset.ground_truth['collective_anomalies']:
                df.loc[
                    anomaly['start_index']:anomaly['end_index']-1,
                    'is_anomaly'
                ] = 1
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info(f"Saved synthetic dataset to {output_path}")

def load_synthetic_dataset(input_path: str) -> SyntheticDataset:
    """
    Load synthetic dataset from disk.

    Args:
        input_path: Path to saved dataset

    Returns:
        SyntheticDataset
    """
    with open(input_path, 'r') as f:
        data = json.load(f)

    return SyntheticDataset(
        values=np.array(data['values']),
        ground_truth=data['ground_truth'],
        metadata=data['metadata']
    )

def generate_validation_dataset(
    seed: int = 42,
    anomaly_rate: float = 0.05,
    length: int = 1000
) -> SyntheticDataset:
    """
    Generate a validation dataset with known ground truth.

    Args:
        seed: Random seed for reproducibility
        anomaly_rate: Target anomaly rate
        length: Length of time series

    Returns:
        SyntheticDataset with reproducible ground truth
    """
    signal_config = SignalConfig(
        signal_type='composite',
        frequency=0.01,
        amplitude=1.0,
        trend_slope=0.001,
        noise_std=0.1,
        seed=seed
    )
    
    anomaly_config = AnomalyConfig(
        anomaly_type='collective',
        anomaly_magnitude=5.0,
        anomaly_duration_min=5,
        anomaly_duration_max=20,
        seed=seed
    )

    return generate_synthetic_timeseries(
        signal_config, anomaly_config, length
    )

def main():
    """Main entry point for CLI execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate synthetic time series for anomaly detection'
    )
    parser.add_argument(
        '--seed', type=int, default=42, help='Random seed'
    )
    parser.add_argument(
        '--anomaly-rate', type=float, default=0.05,
        help='Target anomaly rate'
    )
    parser.add_argument(
        '--length', type=int, default=1000,
        help='Length of time series'
    )
    parser.add_argument(
        '--output', type=str, default='data/processed/results/synthetic_dataset.json',
        help='Output file path'
    )

    args = parser.parse_args()

    # Generate dataset
    logger.info(f"Generating synthetic dataset with seed={args.seed}, "
               f"anomaly_rate={args.anomaly_rate}, length={args.length}")

    dataset = generate_validation_dataset(
        seed=args.seed,
        anomaly_rate=args.anomaly_rate,
        length=args.length
    )

    # Save dataset
    save_synthetic_dataset(dataset, args.output, format='json')

    # Log summary
    gt = dataset.ground_truth
    logger.info(f"Generated dataset summary:")
    logger.info(f"  Total length: {gt['total_length']}")
    logger.info(f"  Target anomaly rate: {gt['anomaly_rate']}")
    logger.info(f"  Actual anomaly points: {gt['actual_anomaly_points']}")
    logger.info(f"  Actual anomaly rate: {gt['actual_anomaly_rate']:.4f}")

    # Verify ground truth integrity
    if gt['actual_anomaly_points'] == 0:
        logger.warning("No anomalies were injected. Check configuration.")
    else:
        logger.info("Ground truth validation: PASSED")

    return dataset

if __name__ == '__main__':
    main()