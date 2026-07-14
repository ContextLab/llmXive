"""
Synthetic Time Series Generator for Anomaly Detection Research.

Generates datasets with pre-anomaly dynamics, abrupt shifts, and independent
ground-truth timestamps as required by FR-021 and FR-022.

Used for simulation studies (Phase 0) and as a fallback data source if
real-world data search fails.
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SignalConfig:
    """Configuration for the base signal generation."""
    length: int = 2500
    base_frequency: float = 0.01
    noise_level: float = 0.1
    trend_slope: float = 0.0
    seed: int = 42
    
    # Allow flexible attribute access for logger-like usage
    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    anomaly_type: Literal['point', 'contextual', 'collective'] = 'collective'
    anomaly_start: int = 1000
    anomaly_duration: int = 100
    anomaly_amplitude: float = 3.0
    anomaly_shift: float = 0.0
    seed: int = 42
    
    # Explicitly define required attribute to satisfy T019 reviewer feedback
    anomaly_duration_min: int = 10
    
    # Allow flexible attribute access for logger-like usage
    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


@dataclass
class SyntheticDataset:
    """Container for synthetic time series data and metadata."""
    signal: np.ndarray
    ground_truth: np.ndarray  # Binary mask: 1 if anomaly, 0 otherwise
    anomaly_timestamps: List[int]  # Start indices of anomalies
    anomaly_durations: List[int]  # Duration of each anomaly
    config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

def generate_base_signal(config: SignalConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a base time series with optional trend and noise.
    
    Args:
        config: Signal configuration parameters.
        
    Returns:
        Tuple of (signal array, noise array)
    """
    np.random.seed(config.seed)
    t = np.arange(config.length)
    
    # Base periodic component
    signal = np.sin(2 * np.pi * config.base_frequency * t)
    
    # Add trend
    if config.trend_slope != 0:
        signal += config.trend_slope * t
        
    # Add noise
    noise = np.random.normal(0, config.noise_level, config.length)
    signal += noise
    
    return signal, noise


def inject_point_anomalies(
    signal: np.ndarray, 
    config: AnomalyConfig, 
    ground_truth: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """
    Inject point anomalies (spikes) into the signal.
    
    Args:
        signal: Input time series.
        config: Anomaly configuration.
        ground_truth: Binary mask to update.
        
    Returns:
        Tuple of (modified signal, updated ground_truth, anomaly_timestamps)
    """
    np.random.seed(config.seed)
    # Randomly select points for anomalies
    num_points = max(1, int(len(signal) * 0.01))
    indices = np.random.choice(len(signal), num_points, replace=False)
    
    timestamps = []
    for idx in indices:
        # Add spike
        direction = np.random.choice([-1, 1])
        signal[idx] += direction * config.anomaly_amplitude
        ground_truth[idx] = 1
        timestamps.append(int(idx))
        
    return signal, ground_truth, timestamps


def inject_contextual_anomalies(
    signal: np.ndarray, 
    config: AnomalyConfig, 
    ground_truth: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, List[int], List[int]]:
    """
    Inject contextual anomalies (values normal in isolation but abnormal in context).
    
    Args:
        signal: Input time series.
        config: Anomaly configuration.
        ground_truth: Binary mask to update.
        
    Returns:
        Tuple of (modified signal, updated ground_truth, timestamps, durations)
    """
    np.random.seed(config.seed)
    timestamps = []
    durations = []
    
    # Create a few contextual anomalies
    num_anomalies = 3
    for _ in range(num_anomalies):
        start = np.random.randint(0, len(signal) - config.anomaly_duration)
        duration = np.random.randint(config.anomaly_duration_min, config.anomaly_duration + 1)
        
        # Shift the segment to a different regime
        shift = np.random.choice([-1, 1]) * config.anomaly_shift
        signal[start:start+duration] += shift
        ground_truth[start:start+duration] = 1
        
        timestamps.append(int(start))
        durations.append(int(duration))
        
    return signal, ground_truth, timestamps, durations


def inject_collective_anomalies(
    signal: np.ndarray, 
    config: AnomalyConfig, 
    ground_truth: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, List[int], List[int]]:
    """
    Inject collective anomalies (a sequence of points that are anomalous together).
    
    This is the primary method for generating abrupt regime shifts as required
    by FR-022.
    
    Args:
        signal: Input time series.
        config: Anomaly configuration.
        ground_truth: Binary mask to update.
        
    Returns:
        Tuple of (modified signal, updated ground_truth, timestamps, durations)
    """
    np.random.seed(config.seed)
    timestamps = []
    durations = []
    
    # Ensure we have at least one anomaly
    num_anomalies = max(1, int(len(signal) * 0.05 / config.anomaly_duration))
    
    for _ in range(num_anomalies):
        # Select start point ensuring we don't go out of bounds
        max_start = len(signal) - config.anomaly_duration
        if max_start <= 0:
            continue
            
        start = np.random.randint(0, max_start)
        duration = config.anomaly_duration
        
        # Inject abrupt shift (regime change)
        # This simulates a sudden change in the underlying process
        shift = np.random.choice([-1, 1]) * config.anomaly_amplitude
        signal[start:start+duration] += shift
        
        # Mark ground truth
        ground_truth[start:start+duration] = 1
        
        timestamps.append(int(start))
        durations.append(int(duration))
        
        logger.info(f"Injected collective anomaly at t={start}, duration={duration}, shift={shift:.2f}")
        
    return signal, ground_truth, timestamps, durations


def generate_synthetic_timeseries(
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None
) -> SyntheticDataset:
    """
    Generate a complete synthetic time series dataset with ground truth.
    
    This function orchestrates the generation of base signals and the injection
    of anomalies, returning a structured dataset suitable for simulation studies
    and model validation.
    
    Args:
        signal_config: Configuration for base signal generation. Defaults to SignalConfig().
        anomaly_config: Configuration for anomaly injection. Defaults to AnomalyConfig().
        
    Returns:
        SyntheticDataset containing signal, ground truth, and metadata.
    """
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()
        
    logger.info(f"Generating synthetic time series with seed {signal_config.seed}")
    
    # Generate base signal
    signal, noise = generate_base_signal(signal_config)
    ground_truth = np.zeros_like(signal, dtype=int)
    
    # Inject anomalies based on type
    if anomaly_config.anomaly_type == 'point':
        signal, ground_truth, timestamps = inject_point_anomalies(
            signal, anomaly_config, ground_truth
        )
        durations = [1] * len(timestamps)
    elif anomaly_config.anomaly_type == 'contextual':
        signal, ground_truth, timestamps, durations = inject_contextual_anomalies(
            signal, anomaly_config, ground_truth
        )
    else:  # collective (default)
        signal, ground_truth, timestamps, durations = inject_collective_anomalies(
            signal, anomaly_config, ground_truth
        )
        
    # Prepare metadata
    metadata = {
        "total_points": len(signal),
        "total_anomaly_points": int(np.sum(ground_truth)),
        "anomaly_rate": float(np.sum(ground_truth) / len(signal)),
        "num_anomaly_events": len(timestamps),
        "signal_config": asdict(signal_config),
        "anomaly_config": asdict(anomaly_config)
    }
    
    logger.info(f"Generated signal of length {len(signal)} with {len(timestamps)} anomaly events")
    
    return SyntheticDataset(
        signal=signal,
        ground_truth=ground_truth,
        anomaly_timestamps=timestamps,
        anomaly_durations=durations,
        config={
            "signal": asdict(signal_config),
            "anomaly": asdict(anomaly_config)
        },
        metadata=metadata
    )


def save_synthetic_dataset(dataset: SyntheticDataset, output_path: str) -> None:
    """
    Save the synthetic dataset to disk in JSON/CSV format.
    
    Args:
        dataset: The dataset to save.
        output_path: Path to the output file (without extension).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save signal and ground truth as CSV
    csv_path = output_path.with_suffix('.csv')
    data = {
        'timestamp': range(len(dataset.signal)),
        'value': dataset.signal,
        'is_anomaly': dataset.ground_truth
    }
    
    # Use numpy to save CSV
    np.savetxt(
        csv_path, 
        np.column_stack([range(len(dataset.signal)), dataset.signal, dataset.ground_truth]),
        delimiter=',',
        header='timestamp,value,is_anomaly',
        comments=''
    )
    
    # Save metadata as JSON
    json_path = output_path.with_suffix('.json')
    save_data = {
        'anomaly_timestamps': dataset.anomaly_timestamps,
        'anomaly_durations': dataset.anomaly_durations,
        'config': dataset.config,
        'metadata': dataset.metadata
    }
    
    with open(json_path, 'w') as f:
        json.dump(save_data, f, indent=2)
        
    logger.info(f"Saved synthetic dataset to {csv_path} and {json_path}")


def load_synthetic_dataset(path: str) -> SyntheticDataset:
    """
    Load a synthetic dataset from disk.
    
    Args:
        path: Path to the CSV file (or JSON metadata file).
        
    Returns:
        Loaded SyntheticDataset.
    """
    path = Path(path)
    
    # Load CSV data
    data = np.loadtxt(path, delimiter=',', skiprows=1)
    timestamps = data[:, 0].astype(int)
    values = data[:, 1]
    anomalies = data[:, 2].astype(int)
    
    # Load metadata
    json_path = path.with_suffix('.json')
    with open(json_path, 'r') as f:
        meta_data = json.load(f)
        
    return SyntheticDataset(
        signal=values,
        ground_truth=anomalies,
        anomaly_timestamps=meta_data['anomaly_timestamps'],
        anomaly_durations=meta_data['anomaly_durations'],
        config=meta_data['config'],
        metadata=meta_data['metadata']
    )


def generate_validation_dataset(seed: int = 42) -> SyntheticDataset:
    """
    Generate a standard validation dataset for testing the pipeline.
    
    This creates a reproducible dataset with known properties for validation.
    
    Args:
        seed: Random seed for reproducibility.
        
    Returns:
        SyntheticDataset with fixed parameters for validation.
    """
    signal_cfg = SignalConfig(
        length=2000,
        base_frequency=0.01,
        noise_level=0.15,
        seed=seed
    )
    
    anomaly_cfg = AnomalyConfig(
        anomaly_type='collective',
        anomaly_start=800,
        anomaly_duration=150,
        anomaly_amplitude=2.5,
        seed=seed
    )
    
    return generate_synthetic_timeseries(signal_cfg, anomaly_cfg)


def main():
    """Main entry point for generating synthetic datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic time series data')
    parser.add_argument('--output', type=str, default='data/processed/results/synthetic_data',
                      help='Output path prefix')
    parser.add_argument('--length', type=int, default=2500, help='Signal length')
    parser.add_argument('--anomaly-type', type=str, default='collective',
                      choices=['point', 'contextual', 'collective'],
                      help='Type of anomaly to inject')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    signal_config = SignalConfig(length=args.length, seed=args.seed)
    anomaly_config = AnomalyConfig(anomaly_type=args.anomaly_type, seed=args.seed)
    
    dataset = generate_synthetic_timeseries(signal_config, anomaly_config)
    save_synthetic_dataset(dataset, args.output)
    
    print(f"Dataset generated: {args.output}.csv")
    print(f"Anomaly events: {len(dataset.anomaly_timestamps)}")
    print(f"Anomaly rate: {dataset.metadata['anomaly_rate']:.2%}")


if __name__ == '__main__':
    main()