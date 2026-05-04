"""
Memory profiling utilities for streaming observation processing.

Provides tools to track memory usage during DPGMM model training and
anomaly scoring operations. Supports profiling of 1000+ observation
streams with detailed statistics.

Per FR-005: Memory usage must remain <7GB RAM during processing.
"""

import gc
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Generator, Tuple, Union

import numpy as np

# Optional: psutil for more accurate memory tracking
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ..models.anomaly_score import AnomalyScore
from ..models.dp_gmm import DPGMMModel, DPGMMConfig
from .streaming import StreamingObservation


@dataclass
class MemorySnapshot:
    """A single memory measurement point."""
    timestamp: datetime
    elapsed_seconds: float
    memory_mb: float
    peak_memory_mb: float
    observation_count: int
    model_components: int
    gc_count: Tuple[int, int, int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'elapsed_seconds': self.elapsed_seconds,
            'memory_mb': self.memory_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'observation_count': self.observation_count,
            'model_components': self.model_components,
            'gc_count': list(self.gc_count)
        }

@dataclass
class MemoryProfileReport:
    """Complete memory profiling report for an operation."""
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_seconds: float
    snapshots: List[MemorySnapshot]
    peak_memory_mb: float
    average_memory_mb: float
    memory_growth_mb: float
    max_observation_count: int
    model_components_at_end: int
    gc_collections: Tuple[int, int, int]
    passed_7gb_limit: bool
    violation_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_duration_seconds': self.total_duration_seconds,
            'snapshot_count': len(self.snapshots),
            'peak_memory_mb': self.peak_memory_mb,
            'average_memory_mb': self.average_memory_mb,
            'memory_growth_mb': self.memory_growth_mb,
            'max_observation_count': self.max_observation_count,
            'model_components_at_end': self.model_components_at_end,
            'passed_7gb_limit': self.passed_7gb_limit,
            'violation_message': self.violation_message,
            'snapshots': [s.to_dict() for s in self.snapshots]
        }

    def save_json(self, path: Path) -> None:
        """Save report to JSON file."""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def save_csv(self, path: Path) -> None:
        """Save snapshots to CSV file."""
        import csv
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'elapsed_seconds', 'memory_mb', 'peak_memory_mb',
                'observation_count', 'model_components', 'gc_count_0', 'gc_count_1', 'gc_count_2'
            ])
            for s in self.snapshots:
                writer.writerow([
                    s.timestamp.isoformat(),
                    s.elapsed_seconds,
                    s.memory_mb,
                    s.peak_memory_mb,
                    s.observation_count,
                    s.model_components,
                    s.gc_count[0],
                    s.gc_count[1],
                    s.gc_count[2]
                ])

class MemoryProfiler:
    """
    Memory profiler for tracking memory usage during operations.
    
    Usage:
        profiler = MemoryProfiler()
        with profiler.profile("operation_name"):
            # code to profile
            pass
        report = profiler.get_report()
    """

    def __init__(self, sample_interval_seconds: float = 0.1):
        """
        Initialize memory profiler.
        
        Args:
            sample_interval_seconds: How often to sample memory (default 0.1s)
        """
        self.sample_interval = sample_interval_seconds
        self._current_snapshots: List[MemorySnapshot] = []
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._current_observation_count: int = 0
        self._current_model_components: int = 0
        self._operation_name: str = "unnamed"
        self._profiling_active: bool = False

    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process(os.getpid()) if HAS_PSUTIL else None
        if process:
            return process.memory_info().rss / (1024 * 1024)
        else:
            # Fallback: use /proc on Linux or os.sysconf on Unix
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
            except Exception:
                # Last resort: estimate from object sizes
                return sys.getsizeof(self) / (1024 * 1024)

    def _take_snapshot(self, observation_count: Optional[int] = None,
                      model_components: Optional[int] = None) -> MemorySnapshot:
        """Take a memory snapshot at current time."""
        if self._start_time is None:
            self._start_time = datetime.now()
        
        elapsed = (datetime.now() - self._start_time).total_seconds()
        memory_mb = self._get_current_memory_mb()
        gc_counts = gc.get_count()
        
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            elapsed_seconds=elapsed,
            memory_mb=memory_mb,
            peak_memory_mb=max(s.memory_mb for s in self._current_snapshots) if self._current_snapshots else memory_mb,
            observation_count=observation_count if observation_count is not None else self._current_observation_count,
            model_components=model_components if model_components is not None else self._current_model_components,
            gc_count=gc_counts
        )
        self._current_snapshots.append(snapshot)
        return snapshot

    def start(self, operation_name: str = "operation") -> None:
        """Start profiling an operation."""
        self._operation_name = operation_name
        self._start_time = datetime.now()
        self._end_time = None
        self._current_snapshots = []
        self._current_observation_count = 0
        self._current_model_components = 0
        self._profiling_active = True
        gc.collect()
        self._take_snapshot()

    def stop(self) -> None:
        """Stop profiling and take final snapshot."""
        self._end_time = datetime.now()
        self._take_snapshot()
        self._profiling_active = False
        gc.collect()

    def record_observation(self, count: int = 1) -> MemorySnapshot:
        """Record that observations have been processed."""
        self._current_observation_count += count
        return self._take_snapshot(observation_count=self._current_observation_count)

    def record_model_components(self, components: int) -> MemorySnapshot:
        """Record current number of model components (mixture clusters)."""
        self._current_model_components = components
        return self._take_snapshot(model_components=components)

    def profile(self, operation_name: str = "operation") -> 'MemoryProfileContext':
        """Context manager for profiling an operation."""
        return MemoryProfileContext(self, operation_name)

    def get_report(self) -> MemoryProfileReport:
        """Generate profiling report from collected snapshots."""
        if not self._current_snapshots:
            self._take_snapshot()
        
        start = self._start_time or datetime.now()
        end = self._end_time or datetime.now()
        duration = (end - start).total_seconds()
        
        memories = [s.memory_mb for s in self._current_snapshots]
        peak = max(memories) if memories else 0.0
        average = sum(memories) / len(memories) if memories else 0.0
        growth = memories[-1] - memories[0] if len(memories) > 1 else 0.0
        
        max_obs = max(s.observation_count for s in self._current_snapshots) if self._current_snapshots else 0
        final_components = self._current_model_components
        final_gc = gc.get_count()
        
        limit_mb = 7 * 1024  # 7GB in MB
        passed_limit = peak < limit_mb
        
        report = MemoryProfileReport(
            start_time=start,
            end_time=end,
            total_duration_seconds=duration,
            snapshots=self._current_snapshots.copy(),
            peak_memory_mb=peak,
            average_memory_mb=average,
            memory_growth_mb=growth,
            max_observation_count=max_obs,
            model_components_at_end=final_components,
            gc_collections=final_gc,
            passed_7gb_limit=passed_limit,
            violation_message=None if passed_limit else f"Peak memory {peak:.2f}MB exceeded 7GB limit"
        )
        return report

    def reset(self) -> None:
        """Reset profiler state."""
        self._current_snapshots = []
        self._start_time = None
        self._end_time = None
        self._current_observation_count = 0
        self._current_model_components = 0
        self._profiling_active = False

class MemoryProfileContext:
    """Context manager for memory profiling."""

    def __init__(self, profiler: MemoryProfiler, operation_name: str):
        self.profiler = profiler
        self.operation_name = operation_name

    def __enter__(self) -> MemoryProfiler:
        self.profiler.start(self.operation_name)
        return self.profiler

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.profiler.stop()

def profile_1000_observations(model: DPGMMModel,
                              observations: List[np.ndarray],
                              sample_interval: float = 0.01) -> MemoryProfileReport:
    """
    Profile memory usage during processing of 1000 observations.
    
    Args:
        model: DPGMM model instance
        observations: List of observation arrays (1000 observations)
        sample_interval: Memory sampling interval in seconds
    
    Returns:
        MemoryProfileReport with detailed memory statistics
    """
    profiler = MemoryProfiler(sample_interval_seconds=sample_interval)
    profiler.start("1000_observation_processing")
    
    # Process observations with memory tracking
    for i, obs in enumerate(observations):
        # Update model with observation
        model.update(obs)
        
        # Record progress
        if i % 100 == 0:
            profiler.record_observation(count=100)
            profiler.record_model_components(model.active_components_count())
        
        # Force sampling at regular intervals
        if i % 50 == 0:
            profiler._take_snapshot(observation_count=i + 1,
                                   model_components=model.active_components_count())
    
    profiler.record_observation(count=len(observations) % 100)
    profiler.record_model_components(model.active_components_count())
    profiler.stop()
    
    return profiler.get_report()

def profile_model_operations(model: DPGMMModel,
                             n_iterations: int = 100,
                             sample_interval: float = 0.05) -> MemoryProfileReport:
    """
    Profile memory during model operations (ELBO computation, updates).
    
    Args:
        model: DPGMM model instance
        n_iterations: Number of iterations to profile
        sample_interval: Memory sampling interval
    
    Returns:
        MemoryProfileReport
    """
    profiler = MemoryProfiler(sample_interval_seconds=sample_interval)
    profiler.start("model_operations")
    
    for i in range(n_iterations):
        # Perform model operation
        elbo = model.compute_elbo()
        
        if i % 10 == 0:
            profiler.record_model_components(model.active_components_count())
            profiler._take_snapshot(model_components=model.active_components_count())
    
    profiler.stop()
    return profiler.get_report()

def generate_synthetic_observations(n_observations: int = 1000,
                                    n_features: int = 2,
                                    seed: int = 42) -> List[np.ndarray]:
    """
    Generate synthetic observations for memory profiling.
    
    Args:
        n_observations: Number of observations to generate
        n_features: Dimensionality of each observation
        seed: Random seed for reproducibility
    
    Returns:
        List of observation arrays
    """
    np.random.seed(seed)
    observations = []
    
    for i in range(n_observations):
        # Create observations with some structure (multiple clusters)
        cluster = i % 5
        mean = np.array([cluster, cluster * 2])[:n_features]
        obs = np.random.normal(mean, 0.5, n_features)
        observations.append(obs)
    
    return observations

def create_streaming_observation(value: float,
                                 timestamp: Optional[datetime] = None) -> StreamingObservation:
    """
    Create a streaming observation for memory profiling.
    
    Args:
        value: Observation value
        timestamp: Optional timestamp (defaults to now)
    
    Returns:
        StreamingObservation instance
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return StreamingObservation(
        value=value,
        timestamp=timestamp,
        metadata={'source': 'memory_profiling'}
    )

def process_observation(model: DPGMMModel,
                        observation: Union[np.ndarray, StreamingObservation]) -> AnomalyScore:
    """
    Process a single observation through the model with memory tracking.
    
    Args:
        model: DPGMM model instance
        observation: Observation to process
    
    Returns:
        AnomalyScore for the observation
    """
    if isinstance(observation, StreamingObservation):
        # Convert to numpy array if needed
        obs_array = np.array([observation.value])
    else:
        obs_array = observation
    
    # Update model
    model.update(obs_array)
    
    # Compute anomaly score
    score = model.compute_score(obs_array)
    
    return score

def main() -> None:
    """Main entry point for memory profiling demonstration."""
    import json
    
    # Setup
    config = DPGMMConfig(
        n_features=2,
        max_components=10,
        concentration_prior=1.0
    )
    
    model = DPGMMModel(config)
    
    # Generate synthetic data
    print("Generating 1000 synthetic observations...")
    observations = generate_synthetic_observations(n_observations=1000, n_features=2)
    
    # Profile memory
    print("Profiling memory usage during 1000 observation processing...")
    report = profile_1000_observations(model, observations)
    
    # Print summary
    print(f"\n=== Memory Profile Report ===")
    print(f"Operation: 1000 observation processing")
    print(f"Duration: {report.total_duration_seconds:.2f} seconds")
    print(f"Peak Memory: {report.peak_memory_mb:.2f} MB")
    print(f"Average Memory: {report.average_memory_mb:.2f} MB")
    print(f"Memory Growth: {report.memory_growth_mb:.2f} MB")
    print(f"Max Observations: {report.max_observation_count}")
    print(f"Final Model Components: {report.model_components_at_end}")
    print(f"7GB Limit Passed: {report.passed_7gb_limit}")
    
    if report.violation_message:
        print(f"WARNING: {report.violation_message}")
    
    # Save reports
    output_dir = Path("data/processed/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"memory_profile_{timestamp}.json"
    csv_path = output_dir / f"memory_profile_{timestamp}.csv"
    
    report.save_json(json_path)
    report.save_csv(csv_path)
    
    print(f"\nReports saved:")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")

if __name__ == "__main__":
    main()
