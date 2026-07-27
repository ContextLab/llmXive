"""
Benchmark script to measure and verify runtime optimization (SC-005).
Compares chunked I/O vs full load performance.
"""
import os
import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path
from src.data.preprocess import run_preprocessing_pipeline
from src.models.gamm_fit import run_gamm_pipeline

def generate_large_synthetic_data(output_dir: Path, n_rows: int = 1000000):
    """Generate a large synthetic dataset for benchmarking."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating synthetic dataset with {n_rows} rows...")
    
    # Generate synthetic eBird data
    np.random.seed(42)
    species_list = ['Turdus_migratorius', 'Setophaga_cerulea', 'Cardinalis_cardinalis']
    
    data = {
        'species': np.random.choice(species_list, n_rows),
        'lat': np.random.uniform(25, 50, n_rows),
        'lon': np.random.uniform(-120, -70, n_rows),
        'date': pd.date_range('2020-01-01', periods=n_rows, freq='H'),
        'count': np.random.poisson(5, n_rows),
        'checklist_id': [f'CHECK_{i}' for i in range(n_rows)]
    }
    
    df = pd.DataFrame(data)
    ebird_file = output_dir / "raw" / "ebird" / "observations.csv"
    ebird_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ebird_file, index=False)
    
    logger.info(f"Synthetic data generated: {ebird_file}")
    return str(ebird_file)

def benchmark_chunked_vs_full(data_dir: Path, output_dir: Path):
    """Benchmark chunked I/O vs full load for preprocessing."""
    results = {}
    
    # Benchmark full load (if memory allows)
    try:
        logger.info("Benchmarking full load approach...")
        start_time = time.time()
        # Simulate full load by reading all at once
        df_full = pd.read_csv(data_dir / "raw" / "ebird" / "observations.csv")
        full_load_time = time.time() - start_time
        results['full_load_time'] = full_load_time
        logger.info(f"Full load time: {full_load_time:.2f}s")
    except MemoryError:
        results['full_load_time'] = None
        logger.warning("Full load failed due to memory constraints")
    
    # Benchmark chunked approach
    logger.info("Benchmarking chunked I/O approach...")
    start_time = time.time()
    try:
        run_preprocessing_pipeline(data_dir, output_dir)
        chunked_time = time.time() - start_time
        results['chunked_time'] = chunked_time
        logger.info(f"Chunked I/O time: {chunked_time:.2f}s")
    except Exception as e:
        results['chunked_time'] = None
        logger.error(f"Chunked I/O failed: {e}")
    
    return results

def main():
    """Main benchmarking routine."""
    print("=" * 60)
    print("Runtime Optimization Benchmark (SC-005)")
    print("=" * 60)
    
    # Setup
    base_dir = Path("data")
    benchmark_dir = base_dir / "benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate test data
    generate_large_synthetic_data(benchmark_dir, n_rows=500000)
    
    # Run benchmarks
    results = benchmark_chunked_vs_full(benchmark_dir, benchmark_dir / "processed")
    
    # Report results
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    for key, value in results.items():
        if value is not None:
            print(f"{key}: {value:.2f}s")
        else:
            print(f"{key}: N/A")
    
    # Verify target
    target_time = 4 * 3600  # 4 hours in seconds
    if results.get('chunked_time') and results['chunked_time'] < target_time:
        print(f"\n✓ Target met: Runtime {results['chunked_time']:.2f}s < {target_time}s (4h)")
    else:
        print(f"\n✗ Target not met: Runtime exceeds 4h threshold")
    
    # Save results
    import json
    with open(benchmark_dir / "benchmark_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nBenchmark results saved to: {benchmark_dir / 'benchmark_results.json'}")

if __name__ == "__main__":
    main()
