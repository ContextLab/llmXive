"""
Performance benchmark for DPGMM streaming inference.

Compares performance across different configurations and measures
throughput, latency, and memory usage.

Usage:
    python benchmark_dp_gmm_performance.py
"""

import sys
import os
import time
import json
import tracemalloc
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.models.anomaly_score import AnomalyScore

def generate_synthetic_data(n_observations: int, n_features: int = 1, 
                            anomaly_rate: float = 0.05, seed: int = 42) -> np.ndarray:
    """Generate synthetic time series data with injected anomalies."""
    np.random.seed(seed)
    
    # Normal data
    data = np.random.randn(n_observations, n_features) * 0.5
    
    # Inject anomalies
    n_anomalies = int(n_observations * anomaly_rate)
    anomaly_indices = np.random.choice(n_observations, n_anomalies, replace=False)
    
    for idx in anomaly_indices:
        # Large deviation from normal
        data[idx] = np.random.randn(n_features) * 3 + 5
    
    return data, anomaly_indices

def benchmark_single_observation(model: DPGMMModel, observation: np.ndarray) -> Dict[str, float]:
    """Benchmark single observation update and scoring."""
    # Warm-up
    for _ in range(10):
        model.update_streaming(observation)
        model.compute_anomaly_score(observation)
    
    # Benchmark
    update_times = []
    score_times = []
    
    for _ in range(100):
        start = time.time()
        model.update_streaming(observation)
        update_times.append(time.time() - start)
        
        start = time.time()
        model.compute_anomaly_score(observation)
        score_times.append(time.time() - start)
    
    return {
        'avg_update_time_s': float(np.mean(update_times)),
        'max_update_time_s': float(np.max(update_times)),
        'avg_score_time_s': float(np.mean(score_times)),
        'max_score_time_s': float(np.max(score_times))
    }

def benchmark_throughput(model: DPGMMModel, observations: np.ndarray) -> Dict[str, float]:
    """Benchmark throughput for batch of observations."""
    start_time = time.time()
    
    scores = []
    for obs in observations:
        obs = obs.reshape(-1, 1)
        model.update_streaming(obs)
        score = model.compute_anomaly_score(obs)
        scores.append(score.score)
    
    elapsed = time.time() - start_time
    
    return {
        'total_observations': len(observations),
        'elapsed_s': elapsed,
        'throughput_obs_per_s': len(observations) / elapsed,
        'avg_time_per_obs_s': elapsed / len(observations)
    }

def benchmark_memory(observations: np.ndarray, config: DPGMMConfig) -> Dict[str, float]:
    """Benchmark memory usage during processing."""
    model = DPGMMModel(config)
    
    tracemalloc.start()
    
    for obs in observations:
        obs = obs.reshape(-1, 1)
        model.update_streaming(obs)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        'memory_current_mb': current / 1024 / 1024,
        'memory_peak_mb': peak / 1024 / 1024,
        'n_components': model.n_components,
        'total_observations': model._total_observations
    }

def run_all_benchmarks() -> Dict[str, Any]:
    """Run all performance benchmarks."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'benchmarks': {}
    }
    
    # Configuration
    config = DPGMMConfig(
        alpha=1.0,
        batch_update_threshold=50,
        cache_mahalanobis=True,
        vectorize_updates=True,
        max_components=30,
        min_component_weight=1e-6
    )
    
    # Generate test data
    n_obs = 1000
    observations, anomaly_indices = generate_synthetic_data(n_obs)
    
    print(f"Generated {n_obs} observations with {len(anomaly_indices)} anomalies")
    
    # Benchmark 1: Single observation performance
    print("\n=== Benchmark 1: Single Observation Performance ===")
    model = DPGMMModel(config)
    test_obs = observations[0].reshape(-1, 1)
    single_metrics = benchmark_single_observation(model, test_obs)
    results['benchmarks']['single_observation'] = single_metrics
    print(f"Average update time: {single_metrics['avg_update_time_s']:.6f}s")
    print(f"Average score time: {single_metrics['avg_score_time_s']:.6f}s")
    
    # Benchmark 2: Throughput
    print("\n=== Benchmark 2: Throughput ===")
    model = DPGMMModel(config)
    throughput_metrics = benchmark_throughput(model, observations)
    results['benchmarks']['throughput'] = throughput_metrics
    print(f"Throughput: {throughput_metrics['throughput_obs_per_s']:.1f} obs/s")
    
    # Benchmark 3: Memory usage
    print("\n=== Benchmark 3: Memory Usage ===")
    model = DPGMMModel(config)
    memory_metrics = benchmark_memory(observations, config)
    results['benchmarks']['memory'] = memory_metrics
    print(f"Peak memory: {memory_metrics['memory_peak_mb']:.2f} MB")
    print(f"Final components: {memory_metrics['n_components']}")
    
    # Benchmark 4: Model performance metrics
    print("\n=== Benchmark 4: Model Performance Metrics ===")
    model = DPGMMModel(config)
    for obs in observations:
        obs = obs.reshape(-1, 1)
        model.update_streaming(obs)
    
    final_metrics = model.get_performance_metrics()
    results['benchmarks']['model_metrics'] = final_metrics
    print(f"Average update time: {final_metrics['avg_update_time_s']:.6f}s")
    print(f"Average score time: {final_metrics['avg_score_time_s']:.6f}s")
    print(f"ELBO converged: {final_metrics['elbo_converged']}")
    
    # Save results
    output_path = project_root / 'data' / 'processed' / 'results' / 'performance_benchmark.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to {output_path}")
    
    return results

def main():
    """Main entry point."""
    print("=" * 60)
    print("DPGMM Performance Benchmark")
    print("=" * 60)
    
    results = run_all_benchmarks()
    
    print("\n" + "=" * 60)
    print("Benchmark Summary")
    print("=" * 60)
    print(json.dumps(results, indent=2, default=str))
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
