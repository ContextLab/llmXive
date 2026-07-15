import os
import sys
import time
import json
import csv
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local modules
from benchmarks.generator import generate_synthetic_corpus, generate_query_set, get_config_for_size
from benchmarks.metrics import BenchmarkRun, measure_memory, measure_latency
from bloom_filters.base import calculate_optimal_parameters, get_config_for_sizes
from bloom_filters.config import FPR_TARGETS
from bloom_filters.array_impl import ArrayBloomFilter
from bloom_filters.vector_impl import VectorBloomFilter
from bloom_filters.bitset_impl import BitsetBloomFilter

# Dataset sizes and repetitions
DATASET_SIZES = [10000, 50000, 100000, 500000, 1000000]
REPETITIONS = 5
QUERY_MULTIPLIER = 10
MIN_QUERIES = 10000

def ensure_directories():
    """Ensure required directories exist."""
    dirs = [
        'data/processed',
        'results/benchmarks',
        'results/figures'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def get_query_count(dataset_size: int) -> int:
    """
    Calculate number of queries based on dataset size.
    Rule: 10x dataset size, minimum 10k.
    """
    return max(dataset_size * QUERY_MULTIPLIER, MIN_QUERIES)

def run_single_benchmark(
    dataset_size: int,
    fpr: float,
    implementation: str,
    rep_id: int
) -> Optional[BenchmarkRun]:
    """
    Run a single benchmark configuration.
    
    Args:
        dataset_size: Number of elements in the dataset
        fpr: Target false positive rate
        implementation: One of 'ArrayBloomFilter', 'VectorBloomFilter', 'BitsetBloomFilter'
        rep_id: Repetition ID (1-5)
    
    Returns:
        BenchmarkRun object with measurements, or None if timeout/failure
    """
    try:
        # Calculate optimal parameters
        n = dataset_size
        p = fpr
        m, k = calculate_optimal_parameters(n, p)
        
        # Generate synthetic data
        corpus, query_set = generate_synthetic_corpus(n, p)
        
        # Create bloom filter instance
        if implementation == 'ArrayBloomFilter':
            bf = ArrayBloomFilter(m, k)
        elif implementation == 'VectorBloomFilter':
            bf = VectorBloomFilter(m, k)
        elif implementation == 'BitsetBloomFilter':
            bf = BitsetBloomFilter(m, k)
        else:
            raise ValueError(f"Unknown implementation: {implementation}")
        
        # Measure insertion
        insert_start = time.perf_counter()
        for item in corpus:
            bf.insert(item)
        insert_end = time.perf_counter()
        insert_time = (insert_end - insert_start) * 1000  # ms
        
        # Measure query (10x dataset size queries)
        query_count = get_query_count(dataset_size)
        queries = query_set[:query_count] if len(query_set) >= query_count else query_set + query_set[:query_count - len(query_set)]
        
        query_start = time.perf_counter()
        false_positives = 0
        for item in queries:
            if bf.contains(item) and item not in corpus:
                false_positives += 1
        query_end = time.perf_counter()
        query_time = (query_end - query_start) * 1000  # ms
        
        # Measure memory
        memory_mb = measure_memory(lambda: bf.contains(queries[0] if queries else "test"))
        
        # Calculate latency per query
        latency_ms = query_time / len(queries) if queries else 0
        
        return BenchmarkRun(
            dataset_size=dataset_size,
            fpr=fpr,
            implementation_type=implementation,
            peak_memory_mb=memory_mb,
            query_latency_ms=latency_ms,
            repetition_id=rep_id,
            query_count=len(queries),
            insert_time_ms=insert_time,
            false_positive_rate=false_positives / len(queries) if queries else 0
        )
        
    except Exception as e:
        print(f"Error in benchmark (size={dataset_size}, fpr={fpr}, impl={implementation}, rep={rep_id}): {e}")
        traceback.print_exc()
        return None

def run_all_benchmarks():
    """
    Run all benchmark configurations.
    """
    ensure_directories()
    
    results = []
    
    for dataset_size in DATASET_SIZES:
        for fpr in FPR_TARGETS:
            for impl in ['ArrayBloomFilter', 'VectorBloomFilter', 'BitsetBloomFilter']:
                for rep_id in range(1, REPETITIONS + 1):
                    print(f"Running: size={dataset_size}, fpr={fpr}, impl={impl}, rep={rep_id}")
                    
                    run = run_single_benchmark(dataset_size, fpr, impl, rep_id)
                    
                    if run:
                        results.append({
                            'dataset_size': run.dataset_size,
                            'fpr': run.fpr,
                            'implementation': run.implementation_type,
                            'memory_mb': run.peak_memory_mb,
                            'latency_ms': run.query_latency_ms,
                            'query_count': run.query_count,
                            'rep_id': run.repetition_id,
                            'insert_time_ms': run.insert_time_ms,
                            'false_positive_rate': run.false_positive_rate,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        print(f"  FAILED: size={dataset_size}, fpr={fpr}, impl={impl}, rep={rep_id}")
    
    return results

def write_results_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Write benchmark results to CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        'dataset_size', 'fpr', 'implementation',
        'memory_mb', 'latency_ms', 'query_count',
        'rep_id', 'insert_time_ms', 'false_positive_rate', 'timestamp'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow(result)

def main():
    """
    Main entry point for benchmark runner.
    """
    print("Starting benchmark suite...")
    print(f"Dataset sizes: {DATASET_SIZES}")
    print(f"FPR targets: {FPR_TARGETS}")
    print(f"Repetitions: {REPETITIONS}")
    
    results = run_all_benchmarks()
    
    if not results:
        print("No results generated. Exiting.")
        sys.exit(1)
    
    output_path = 'results/benchmarks/benchmark_results.csv'
    write_results_csv(results, output_path)
    
    print(f"\nBenchmark complete. {len(results)} runs written to: {output_path}")
    
    # Validate query counts
    for result in results:
        if result['query_count'] <= 0:
            print(f"ERROR: Invalid query_count ({result['query_count']}) detected. Aborting.")
            sys.exit(1)
    
    print("All query counts validated successfully.")

if __name__ == '__main__':
    main()
