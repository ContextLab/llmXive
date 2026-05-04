"""
Memory profiling script for 1000 observation processing (T022).

This script verifies the <7GB RAM limit requirement (FR-005) by:
1. Generating synthetic time series data with known anomalies
2. Processing 1000 observations through the DPGMM model
3. Profiling memory usage throughout the process
4. Reporting whether memory stays under the 7GB limit

Usage: python profile_memory_1000_obs.py
"""
import sys
import gc
import time
from pathlib import Path
from typing import Generator, Dict, Any

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

import numpy as np
from utils.memory_profiler import profile_memory_usage, MemoryProfileResult
from src.models.dpgmm import DPGMMModel
from src.utils.streaming import StreamingObservation

# Constants for reproducible results
RANDOM_SEED = 42
NUM_OBSERVATIONS = 1000
MEMORY_LIMIT_MB = 7000.0  # 7GB per FR-005
ANOMALY_RATE = 0.05  # 5% anomalies in synthetic data

def generate_synthetic_observations(n: int) -> Generator[Dict[str, Any], None, None]:
    """
    Generate synthetic time series observations with embedded anomalies.
    
    Yields:
        Dict with 'timestamp', 'value', 'is_anomaly' keys
    """
    np.random.seed(RANDOM_SEED)
    
    # Base signal: sinusoidal with noise
    t = np.linspace(0, 10 * np.pi, n)
    base_signal = 10 * np.sin(t) + np.random.normal(0, 1, n)
    
    # Inject anomalies at known positions
    anomaly_indices = np.random.choice(
        n, size=int(n * ANOMALY_RATE), replace=False
    )
    anomaly_set = set(anomaly_indices)
    
    for i in range(n):
        value = base_signal[i]
        is_anomaly = i in anomaly_set
        
        if is_anomaly:
            # Large spike for anomaly
            value += np.random.choice([-1, 1]) * np.random.uniform(15, 25)
        
        yield {
            'timestamp': i,
            'value': float(value),
            'is_anomaly': is_anomaly
        }

def create_streaming_observation(obs_dict: Dict[str, Any]) -> StreamingObservation:
    """Convert dict to StreamingObservation for model processing."""
    return StreamingObservation(
        timestamp=obs_dict['timestamp'],
        value=obs_dict['value'],
        metadata={'is_anomaly': obs_dict['is_anomaly']}
    )

def process_observation(obs: StreamingObservation, model: DPGMMModel) -> None:
    """
    Process a single observation through the DPGMM model.
    
    This includes:
    1. Updating the model posterior
    2. Computing anomaly score
    3. (No storage of results - streaming only)
    """
    model.update(obs)
    _ = model.score(obs)  # Compute score but don't store

def main():
    """
    Main profiling routine for 1000 observation memory test.
    
    This script MUST complete its full work when invoked as:
        python profile_memory_1000_obs.py
    
    No arguments are required.
    """
    print("="*60)
    print("MEMORY PROFILING TEST FOR 1000 OBSERVATIONS")
    print("="*60)
    print(f"Target: {NUM_OBSERVATIONS} observations")
    print(f"Memory limit: {MEMORY_LIMIT_MB} MB (7GB)")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Expected anomaly rate: {ANOMALY_RATE*100:.1f}%")
    print()
    
    # Initialize DPGMM model
    print("Initializing DPGMM model...")
    model = DPGMMModel(
        n_components_max=10,
        concentration_prior=1.0,
        random_seed=RANDOM_SEED
    )
    
    # Create observation generator
    obs_generator = generate_synthetic_observations(NUM_OBSERVATIONS)
    
    # Profile memory during processing
    print(f"Processing {NUM_OBSERVATIONS} observations with memory profiling...")
    gc.collect()  # Clean slate before profiling
    
    def callback(obs_dict):
        obs = create_streaming_observation(obs_dict)
        process_observation(obs, model)
    
    result: MemoryProfileResult = profile_memory_usage(
        observations=obs_generator,
        callback=callback,
        snapshot_interval=100,  # Snapshot every 100 observations
        limit_mb=MEMORY_LIMIT_MB,
        verbose=True
    )
    
    # Verify results
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    summary = result.summary()
    
    if result.exceeds_limit:
        print(f"❌ FAILED: Peak memory {summary['peak_memory_mb']:.2f} MB exceeds {MEMORY_LIMIT_MB} MB limit")
        return 1
    else:
        margin = MEMORY_LIMIT_MB - summary['peak_memory_mb']
        print(f"✓ PASSED: Peak memory {summary['peak_memory_mb']:.2f} MB is within {MEMORY_LIMIT_MB} MB limit")
        print(f"  Margin: {margin:.2f} MB ({margin/MEMORY_LIMIT_MB*100:.1f}% headroom)")
    
    # Additional metrics
    print(f"\nMemory efficiency:")
    print(f"  Memory per observation: {summary['avg_memory_per_observation_kb']:.2f} KB")
    print(f"  Total growth: {summary['memory_growth_mb']:.2f} MB")
    
    # Save detailed results
    results_dir = code_dir / 'data' / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    csv_path = results_dir / f'memory_profile_{NUM_OBSERVATIONS}obs_{timestamp}.csv'
    
    with open(csv_path, 'w') as f:
        f.write(result.to_csv())
    
    print(f"\nDetailed CSV saved to: {csv_path}")
    
    # Save JSON summary
    import json
    json_path = results_dir / f'memory_profile_{NUM_OBSERVATIONS}obs_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"JSON summary saved to: {json_path}")
    
    print("\n" + "="*60)
    print("MEMORY PROFILING COMPLETE")
    print("="*60)
    
    return 0 if not result.exceeds_limit else 1

if __name__ == '__main__':
    sys.exit(main())
