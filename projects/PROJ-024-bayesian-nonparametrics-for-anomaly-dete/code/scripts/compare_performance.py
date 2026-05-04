"""
Compare performance before and after optimization.

This script runs benchmarks with different configurations to
demonstrate the performance improvements from optimization.
"""

import sys
import os
import time
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.models.anomaly_score import AnomalyScore

def generate_test_data(n_observations: int, n_features: int = 1) -> np.ndarray:
    """Generate test data for performance comparison."""
    np.random.seed(42)
    data = np.random.randn(n_observations, n_features) * 0.5
    return data

def benchmark_configuration(config: DPGMMConfig, observations: np.ndarray, 
                            name: str) -> Dict[str, Any]:
    """Benchmark a specific configuration."""
    print(f"\n=== Testing: {name} ===")
    
    model = DPGMMModel(config)
    
    start_time = time.time()
    scores = []
    
    for obs in observations:
        obs = obs.reshape(-1, 1)
        model.update_streaming(obs)
        score = model.compute_anomaly_score(obs)
        scores.append(score.score)
    
    elapsed = time.time() - start_time
    metrics = model.get_performance_metrics()
    
    result = {
        'name': name,
        'config': {
            'cache_mahalanobis': config.cache_mahalanobis,
            'vectorize_updates': config.vectorize_updates,
            'batch_update_threshold': config.batch_update_threshold
        },
        'elapsed_s': elapsed,
        'throughput_obs_per_s': len(observations) / elapsed,
        'avg_update_time_s': metrics['avg_update_time_s'],
        'avg_score_time_s': metrics['avg_score_time_s'],
        'n_components': metrics['n_components'],
        'cache_size': metrics['cache_size']
    }
    
    print(f"  Throughput: {result['throughput_obs_per_s']:.1f} obs/s")
    print(f"  Avg update time: {result['avg_update_time_s']:.6f}s")
    print(f"  Avg score time: {result['avg_score_time_s']:.6f}s")
    
    return result

def main():
    """Run performance comparison across configurations."""
    print("=" * 70)
    print("DPGMM Performance Comparison")
    print("=" * 70)
    
    # Generate test data
    n_obs = 500
    observations = generate_test_data(n_obs)
    print(f"\nTesting with {n_obs} observations")
    
    # Configuration 1: No optimization
    config_slow = DPGMMConfig(
        alpha=1.0,
        cache_mahalanobis=False,
        vectorize_updates=False,
        batch_update_threshold=1000  # Disable batching
    )
    
    # Configuration 2: With optimization
    config_fast = DPGMMConfig(
        alpha=1.0,
        cache_mahalanobis=True,
        vectorize_updates=True,
        batch_update_threshold=50
    )
    
    # Run benchmarks
    results = []
    
    result1 = benchmark_configuration(config_slow, observations, "Baseline (no optimization)")
    results.append(result1)
    
    result2 = benchmark_configuration(config_fast, observations, "Optimized (with caching & vectorization)")
    results.append(result2)
    
    # Compute improvement
    speedup = result1['throughput_obs_per_s'] / result2['throughput_obs_per_s']
    
    print("\n" + "=" * 70)
    print("Performance Comparison Summary")
    print("=" * 70)
    print(f"Baseline throughput: {result1['throughput_obs_per_s']:.1f} obs/s")
    print(f"Optimized throughput: {result2['throughput_obs_per_s']:.1f} obs/s")
    print(f"Speedup: {speedup:.2f}x")
    
    # Save results
    output_path = project_root / 'data' / 'processed' / 'results' / 'performance_comparison.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    comparison_result = {
        'timestamp': datetime.now().isoformat(),
        'n_observations': n_obs,
        'results': results,
        'speedup': speedup
    }
    
    with open(output_path, 'w') as f:
        json.dump(comparison_result, f, indent=2, default=str)
    
    print(f"\nResults saved to {output_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
