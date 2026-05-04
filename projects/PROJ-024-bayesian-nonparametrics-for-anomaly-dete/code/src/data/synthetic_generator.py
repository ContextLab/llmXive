"""
Synthetic Anomaly Dataset Generator for Time Series Anomaly Detection Validation

Generates synthetic time series data with known ground truth anomaly labels
for testing and validating DPGMM and baseline anomaly detection models.

Supports three anomaly types:
- Point anomalies: Individual outliers that deviate significantly from normal
- Contextual anomalies: Normal values in wrong context (e.g., high value during low period)
- Collective anomalies: Groups of consecutive anomalous points

Usage:
    from src.data.synthetic_generator import generate_validation_dataset, save_synthetic_dataset

    # Generate validation dataset with known ground truth
    data, labels, config = generate_validation_dataset(
        n_samples=1000,
        anomaly_rate=0.05,
        seed=42
    )

    # Save to disk
    save_synthetic_dataset(data, labels, config, "data/validation/test_dataset.json")
"""

import os
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Tuple, Dict, List, Optional, Any, Literal
import hashlib

# ============================================================================
# Data Classes for Configuration
# ============================================================================

@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection parameters."""
    anomaly_rate: float = 0.05  # Overall anomaly rate (0-1)
    point_anomaly_rate: float = 0.02  # Fraction of point anomalies
    contextual_anomaly_rate: float = 0.02  # Fraction of contextual anomalies
    collective_anomaly_rate: float = 0.01  # Fraction of collective anomalies
    
    # Point anomaly parameters
    point_anomaly_magnitude: float = 5.0  # Standard deviations from mean
    point_anomaly_std_deviation: float = 0.5  # Variance in magnitude
    
    # Contextual anomaly parameters
    context_window_size: int = 10  # Window for context calculation
    contextual_threshold: float = 3.0  # Z-score threshold for context violation
    
    # Collective anomaly parameters
    collective_anomaly_min_length: int = 5  # Minimum consecutive anomalous points
    collective_anomaly_max_length: int = 20  # Maximum consecutive anomalous points
    collective_anomaly_shift: float = 2.0  # Mean shift for collective anomalies
    
    # Random seed for reproducibility
    seed: int = 42
    
    # Anomaly type distribution
    anomaly_types: List[Literal["point", "contextual", "collective"]] = field(
        default_factory=lambda: ["point", "contextual", "collective"]
    )

@dataclass
class SignalConfig:
    """Configuration for base signal generation parameters."""
    signal_type: Literal["sine", "random_walk", "ar1", "mixed"] = "sine"
    n_samples: int = 1000  # Number of samples to generate
    frequency: float = 0.1  # Frequency for sine waves (cycles per sample)
    amplitude: float = 1.0  # Amplitude for sine waves
    noise_std: float = 0.1  # Standard deviation of Gaussian noise
    trend_slope: float = 0.0  # Linear trend slope
    
    # Random walk parameters
    drift: float = 0.0  # Drift term for random walk
    random_walk_std: float = 0.1  # Step standard deviation
    
    # AR(1) parameters
    ar_coefficient: float = 0.9  # AR(1) coefficient
    ar_noise_std: float = 0.1  # AR noise standard deviation
    
    # Mixed signal configuration
    mixed_signal_weights: List[float] = field(default_factory=lambda: [0.5, 0.3, 0.2])
    
    # Random seed
    seed: int = 42

@dataclass
class SyntheticDataset:
    """Container for generated synthetic dataset with metadata."""
    data: np.ndarray  # Time series values
    labels: np.ndarray  # Binary anomaly labels (0=normal, 1=anomaly)
    anomaly_types: np.ndarray  # Anomaly type labels (0=normal, 1=point, 2=contextual, 3=collective)
    config: Dict[str, Any]  # Combined configuration
    metadata: Dict[str, Any]  # Additional metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "data": self.data.tolist(),
            "labels": self.labels.tolist(),
            "anomaly_types": self.anomaly_types.tolist(),
            "config": self.config,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "SyntheticDataset":
        """Create from dictionary."""
        return cls(
            data=np.array(data_dict["data"]),
            labels=np.array(data_dict["labels"]),
            anomaly_types=np.array(data_dict["anomaly_types"]),
            config=data_dict["config"],
            metadata=data_dict["metadata"]
        )

# ============================================================================
# Signal Generation Functions
# ============================================================================

def generate_base_signal(config: SignalConfig) -> np.ndarray:
    """
    Generate base time series signal without anomalies.

    Args:
        config: SignalConfig with signal generation parameters

    Returns:
        numpy array of shape (n_samples,) containing the base signal
    """
    np.random.seed(config.seed)
    n = config.n_samples
    t = np.arange(n)

    if config.signal_type == "sine":
        # Pure sine wave with noise
        signal = config.amplitude * np.sin(2 * np.pi * config.frequency * t)
        signal += config.trend_slope * t
        signal += np.random.normal(0, config.noise_std, n)

    elif config.signal_type == "random_walk":
        # Random walk with drift
        steps = np.random.normal(config.drift, config.random_walk_std, n)
        signal = np.cumsum(steps)
        signal += config.trend_slope * t
        signal += np.random.normal(0, config.noise_std, n)

    elif config.signal_type == "ar1":
        # AR(1) process
        signal = np.zeros(n)
        signal[0] = np.random.normal(0, config.ar_noise_std)
        for i in range(1, n):
            signal[i] = config.ar_coefficient * signal[i-1] + \
                       np.random.normal(0, config.ar_noise_std)
        signal += config.trend_slope * t

    elif config.signal_type == "mixed":
        # Combination of multiple signal types
        weights = config.mixed_signal_weights
        n_sine = int(n * weights[0])
        n_rw = int(n * weights[1])
        n_ar = n - n_sine - n_rw

        sine_part = config.amplitude * np.sin(2 * np.pi * config.frequency * t[:n_sine])
        rw_steps = np.random.normal(config.drift, config.random_walk_std, n_rw)
        rw_part = np.cumsum(rw_steps)

        ar_part = np.zeros(n_ar)
        ar_part[0] = np.random.normal(0, config.ar_noise_std)
        for i in range(1, n_ar):
            ar_part[i] = config.ar_coefficient * ar_part[i-1] + \
                        np.random.normal(0, config.ar_noise_std)

        signal = np.concatenate([sine_part, rw_part, ar_part])
        signal += config.trend_slope * t
        signal += np.random.normal(0, config.noise_std, n)

    else:
        raise ValueError(f"Unknown signal type: {config.signal_type}")

    return signal

# ============================================================================
# Anomaly Injection Functions
# ============================================================================

def inject_point_anomalies(
    data: np.ndarray,
    anomaly_config: AnomalyConfig
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Inject point anomalies (individual outliers) into the time series.

    Args:
        data: Base time series array
        anomaly_config: AnomalyConfig with point anomaly parameters

    Returns:
        Tuple of (modified_data, anomaly_labels, anomaly_type_labels)
        - anomaly_labels: 1 where anomaly, 0 otherwise
        - anomaly_type_labels: 1 for point anomaly, 0 otherwise
    """
    np.random.seed(anomaly_config.seed)
    n = len(data)
    n_point_anomalies = int(n * anomaly_config.point_anomaly_rate)

    # Select random indices for point anomalies
    available_indices = list(range(n))
    anomaly_indices = np.random.choice(
        available_indices,
        size=n_point_anomalies,
        replace=False
    )

    # Create anomaly labels
    anomaly_labels = np.zeros(n, dtype=int)
    anomaly_type_labels = np.zeros(n, dtype=int)  # 1 = point anomaly

    modified_data = data.copy()

    for idx in anomaly_indices:
        # Random magnitude with some variance
        magnitude = np.random.normal(
            anomaly_config.point_anomaly_magnitude,
            anomaly_config.point_anomaly_std_deviation
        )
        # Random direction (positive or negative)
        direction = np.random.choice([-1, 1])
        # Calculate deviation based on local statistics
        local_std = np.std(data[max(0, idx-10):min(n, idx+10)])
        local_std = max(local_std, 1e-6)  # Prevent division by zero
        deviation = direction * magnitude * local_std

        modified_data[idx] += deviation
        anomaly_labels[idx] = 1
        anomaly_type_labels[idx] = 1

    return modified_data, anomaly_labels, anomaly_type_labels

def inject_contextual_anomalies(
    data: np.ndarray,
    anomaly_config: AnomalyConfig
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Inject contextual anomalies (values normal in absolute terms but anomalous
    in context) into the time series.

    Args:
        data: Base time series array
        anomaly_config: AnomalyConfig with contextual anomaly parameters

    Returns:
        Tuple of (modified_data, anomaly_labels, anomaly_type_labels)
        - anomaly_labels: 1 where anomaly, 0 otherwise
        - anomaly_type_labels: 2 for contextual anomaly, 0 otherwise
    """
    np.random.seed(anomaly_config.seed + 1000)  # Different seed
    n = len(data)
    n_contextual_anomalies = int(n * anomaly_config.contextual_anomaly_rate)

    # Calculate rolling statistics for context
    window_size = anomaly_config.context_window_size
    rolling_mean = np.zeros(n)
    rolling_std = np.zeros(n)

    for i in range(n):
        start = max(0, i - window_size)
        end = min(n, i + window_size)
        rolling_mean[i] = np.mean(data[start:end])
        rolling_std[i] = np.std(data[start:end])
        rolling_std[i] = max(rolling_std[i], 1e-6)

    # Select indices where contextual anomalies will be injected
    available_indices = list(range(window_size, n - window_size))
    anomaly_indices = np.random.choice(
        available_indices,
        size=n_contextual_anomalies,
        replace=False
    )

    anomaly_labels = np.zeros(n, dtype=int)
    anomaly_type_labels = np.zeros(n, dtype=int)  # 2 = contextual anomaly
    modified_data = data.copy()

    for idx in anomaly_indices:
        # Create value that is anomalous in context
        # Shift by threshold * local_std to violate context
        context_shift = anomaly_config.contextual_threshold * rolling_std[idx]
        direction = np.random.choice([-1, 1])
        modified_data[idx] = rolling_mean[idx] + direction * context_shift

        anomaly_labels[idx] = 1
        anomaly_type_labels[idx] = 2

    return modified_data, anomaly_labels, anomaly_type_labels

def inject_collective_anomalies(
    data: np.ndarray,
    anomaly_config: AnomalyConfig
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Inject collective anomalies (groups of consecutive anomalous points) into
    the time series.

    Args:
        data: Base time series array
        anomaly_config: AnomalyConfig with collective anomaly parameters

    Returns:
        Tuple of (modified_data, anomaly_labels, anomaly_type_labels)
        - anomaly_labels: 1 where anomaly, 0 otherwise
        - anomaly_type_labels: 3 for collective anomaly, 0 otherwise
    """
    np.random.seed(anomaly_config.seed + 2000)  # Different seed
    n = len(data)
    n_collective_anomalies = int(n * anomaly_config.collective_anomaly_rate)
    n_collective_segments = max(1, n_collective_anomalies // 5)  # At least 1 segment

    anomaly_labels = np.zeros(n, dtype=int)
    anomaly_type_labels = np.zeros(n, dtype=int)  # 3 = collective anomaly
    modified_data = data.copy()

    # Calculate available space for collective anomalies
    min_length = anomaly_config.collective_anomaly_min_length
    max_length = anomaly_config.collective_anomaly_max_length

    # Generate collective anomaly segments
    segments = []
    attempts = 0
    while len(segments) < n_collective_segments and attempts < 100:
        attempts += 1
        # Random segment length
        seg_length = np.random.randint(min_length, min(max_length + 1, n - len(segments) * min_length))
        # Random start position (avoid overlap)
        available_starts = [i for i in range(n - seg_length)
                          if all(abs(i - s[0]) > s[1] for s in segments)]

        if not available_starts:
            continue

        start_idx = np.random.choice(available_starts)
        segments.append((start_idx, seg_length))

    # Inject each segment
    for start_idx, seg_length in segments:
        # Calculate collective shift
        segment_std = np.std(data[start_idx:start_idx + seg_length])
        segment_std = max(segment_std, 1e-6)
        shift = anomaly_config.collective_anomaly_shift * segment_std
        direction = np.random.choice([-1, 1])

        # Apply shift to all points in segment
        modified_data[start_idx:start_idx + seg_length] += direction * shift

        # Update labels
        anomaly_labels[start_idx:start_idx + seg_length] = 1
        anomaly_type_labels[start_idx:start_idx + seg_length] = 3

    return modified_data, anomaly_labels, anomaly_type_labels

# ============================================================================
# Main Generation Function
# ============================================================================

def generate_synthetic_timeseries(
    signal_config: Optional[SignalConfig] = None,
    anomaly_config: Optional[AnomalyConfig] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate complete synthetic time series with anomalies and ground truth labels.

    Args:
        signal_config: SignalConfig for base signal generation
        anomaly_config: AnomalyConfig for anomaly injection

    Returns:
        Tuple of (data, anomaly_labels, anomaly_type_labels)
        - data: Time series values (n_samples,)
        - anomaly_labels: Binary labels (0=normal, 1=anomaly)
        - anomaly_type_labels: Type labels (0=normal, 1=point, 2=contextual, 3=collective)
    """
    # Use defaults if not provided
    if signal_config is None:
        signal_config = SignalConfig()
    if anomaly_config is None:
        anomaly_config = AnomalyConfig()

    # Generate base signal
    data = generate_base_signal(signal_config)

    # Initialize labels
    anomaly_labels = np.zeros(len(data), dtype=int)
    anomaly_type_labels = np.zeros(len(data), dtype=int)

    # Inject anomalies in order (collective first to avoid overlap issues)
    if "collective" in anomaly_config.anomaly_types:
        data, col_labels, col_types = inject_collective_anomalies(data, anomaly_config)
        anomaly_labels = np.maximum(anomaly_labels, col_labels)
        anomaly_type_labels = np.maximum(anomaly_type_labels, col_types)

    if "contextual" in anomaly_config.anomaly_types:
        data, ctx_labels, ctx_types = inject_contextual_anomalies(data, anomaly_config)
        anomaly_labels = np.maximum(anomaly_labels, ctx_labels)
        # Only update type if not already collective
        mask = anomaly_type_labels == 0
        anomaly_type_labels[mask] = np.maximum(anomaly_type_labels[mask], ctx_types[mask])

    if "point" in anomaly_config.anomaly_types:
        data, pt_labels, pt_types = inject_point_anomalies(data, anomaly_config)
        anomaly_labels = np.maximum(anomaly_labels, pt_labels)
        # Only update type if not already collective or contextual
        mask = anomaly_type_labels == 0
        anomaly_type_labels[mask] = np.maximum(anomaly_type_labels[mask], pt_types[mask])

    return data, anomaly_labels, anomaly_type_labels

# ============================================================================
# Save/Load Functions
# ============================================================================

def save_synthetic_dataset(
    data: np.ndarray,
    labels: np.ndarray,
    anomaly_types: np.ndarray,
    config: Dict[str, Any],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save synthetic dataset to JSON file.

    Args:
        data: Time series values
        labels: Binary anomaly labels
        anomaly_types: Anomaly type labels
        config: Configuration dictionary
        output_path: Path to save the dataset
        metadata: Optional additional metadata

    Returns:
        Path to saved file
    """
    dataset = SyntheticDataset(
        data=data,
        labels=labels,
        anomaly_types=anomaly_types,
        config=config,
        metadata=metadata or {}
    )

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    with open(output_path, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)

    # Also save a simple CSV version for quick inspection
    csv_path = output_path.with_suffix('.csv')
    np.savetxt(
        csv_path,
        np.column_stack([data, labels, anomaly_types]),
        delimiter=',',
        header='value,label,anomaly_type',
        comments=''
    )

    # Calculate and record checksum
    checksum = hashlib.sha256(output_path.read_bytes()).hexdigest()
    with open(output_path.with_suffix('.checksum'), 'w') as f:
        f.write(checksum)

    return str(output_path)

def load_synthetic_dataset(filepath: str) -> SyntheticDataset:
    """
    Load synthetic dataset from JSON file.

    Args:
        filepath: Path to the dataset file

    Returns:
        SyntheticDataset object
    """
    filepath = Path(filepath)

    with open(filepath, 'r') as f:
        data_dict = json.load(f)

    return SyntheticDataset.from_dict(data_dict)

# ============================================================================
# Validation Dataset Generator
# ============================================================================

def generate_validation_dataset(
    n_samples: int = 1000,
    anomaly_rate: float = 0.05,
    signal_type: Literal["sine", "random_walk", "ar1", "mixed"] = "sine",
    seed: int = 42,
    output_path: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Generate a validation dataset with known ground truth for model evaluation.

    This is the main entry point for creating test datasets with controlled
    anomaly characteristics.

    Args:
        n_samples: Number of samples in the time series
        anomaly_rate: Overall anomaly rate (0-1)
        signal_type: Type of base signal to generate
        seed: Random seed for reproducibility
        output_path: Optional path to save the dataset

    Returns:
        Tuple of (data, labels, config)
        - data: Time series values
        - labels: Binary anomaly labels
        - config: Configuration used for generation
    """
    # Create signal configuration
    signal_config = SignalConfig(
        signal_type=signal_type,
        n_samples=n_samples,
        seed=seed
    )

    # Distribute anomaly rate across types
    anomaly_config = AnomalyConfig(
        anomaly_rate=anomaly_rate,
        point_anomaly_rate=anomaly_rate * 0.4,
        contextual_anomaly_rate=anomaly_rate * 0.3,
        collective_anomaly_rate=anomaly_rate * 0.3,
        seed=seed
    )

    # Generate data
    data, labels, anomaly_types = generate_synthetic_timeseries(
        signal_config=signal_config,
        anomaly_config=anomaly_config
    )

    # Prepare configuration
    config = {
        "signal": asdict(signal_config),
        "anomaly": asdict(anomaly_config),
        "generation_seed": seed,
        "actual_anomaly_rate": float(np.mean(labels)),
        "n_samples": n_samples,
        "n_anomalies": int(np.sum(labels)),
        "n_point_anomalies": int(np.sum(anomaly_types == 1)),
        "n_contextual_anomalies": int(np.sum(anomaly_types == 2)),
        "n_collective_anomalies": int(np.sum(anomaly_types == 3))
    }

    # Save if path provided
    if output_path:
      save_synthetic_dataset(
          data=data,
          labels=labels,
          anomaly_types=anomaly_types,
          config=config,
          output_path=output_path,
          metadata={
              "generated_at": str(datetime.now()),
              "generator_version": "1.0.0"
          }
      )

    return data, labels, config

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """
    Command-line entry point for generating synthetic validation datasets.

    Usage:
        python -m data.synthetic_generator --n_samples 1000 --anomaly_rate 0.05 --output data/validation/test_dataset.json
    """
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description="Generate synthetic time series dataset with known anomaly ground truth"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=1000,
        help="Number of samples in the time series"
    )
    parser.add_argument(
        "--anomaly_rate",
        type=float,
        default=0.05,
        help="Overall anomaly rate (0-1)"
    )
    parser.add_argument(
        "--signal_type",
        type=str,
        choices=["sine", "random_walk", "ar1", "mixed"],
        default="sine",
        help="Type of base signal to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/validation/synthetic_dataset.json",
        help="Output path for the dataset"
    )

    args = parser.parse_args()

    print(f"Generating synthetic dataset...")
    print(f"  Samples: {args.n_samples}")
    print(f"  Anomaly rate: {args.anomaly_rate}")
    print(f"  Signal type: {args.signal_type}")
    print(f"  Seed: {args.seed}")

    data, labels, config = generate_validation_dataset(
        n_samples=args.n_samples,
        anomaly_rate=args.anomaly_rate,
        signal_type=args.signal_type,
        seed=args.seed,
        output_path=args.output
    )

    print(f"\nDataset generated successfully!")
    print(f"  Actual anomaly rate: {config['actual_anomaly_rate']:.4f}")
    print(f"  Number of anomalies: {config['n_anomalies']}")
    print(f"  Point anomalies: {config['n_point_anomalies']}")
    print(f"  Contextual anomalies: {config['n_contextual_anomalies']}")
    print(f"  Collective anomalies: {config['n_collective_anomalies']}")
    print(f"  Saved to: {args.output}")

    return data, labels, config


if __name__ == "__main__":
    main()
