import os
import json
import math
from typing import Dict, List, Any
from datetime import datetime

# Constants from the project configuration
# FPR targets defined in T015
FPR_TARGETS = [0.01, 0.05, 0.10]

# Implementation types
IMPLEMENTATIONS = ['ArrayBloomFilter', 'VectorBloomFilter', 'BitsetBloomFilter']

# Dataset sizes defined in T022
DATASET_SIZES = [10000, 50000, 100000, 500000, 1000000]

def calculate_optimal_k(p: float) -> int:
    """
    Calculate optimal number of hash functions k for a given false positive rate p.
    Formula: k = (m/n) * ln(2)
    But we derive it from the optimal m first.
    Actually, optimal k = (m/n) * ln(2) where m = -n * ln(p) / (ln(2)^2)
    So k = (-ln(p) / ln(2)) which simplifies to: k = -log2(p)
    """
    return max(1, int(round(-math.log2(p))))

def calculate_optimal_bits(n: int, p: float) -> int:
    """
    Calculate optimal number of bits m for n elements and false positive rate p.
    Formula: m = -n * ln(p) / (ln(2)^2)
    """
    if p <= 0 or p >= 1:
        raise ValueError("False positive rate p must be between 0 and 1 (exclusive)")
    
    ln_2 = math.log(2)
    m = -n * math.log(p) / (ln_2 ** 2)
    return int(math.ceil(m))

def calculate_theoretical_memory_bits(n: int, p: float, impl_type: str) -> int:
    """
    Calculate theoretical memory usage in bits for a given implementation.
    
    For ArrayBloomFilter and VectorBloomFilter:
      - These use Python lists/bytearrays which have overhead.
      - Theoretical minimum is the optimal bits calculated above.
      - However, Python lists store pointers (8 bytes per element on 64-bit),
        so actual memory is much higher. We calculate the theoretical minimum
        as the ideal bits, but note that actual implementation overhead differs.
    
    For BitsetBloomFilter:
      - Uses bitarray which is efficient (1 bit per bit).
      - Theoretical memory is exactly the optimal bits.
    
    This function returns the theoretical minimum bits required.
    """
    m = calculate_optimal_bits(n, p)
    
    # For bitset implementation, we can achieve near-optimal bit usage
    # For array/vector implementations, Python overhead is significant
    # but the theoretical minimum is still the optimal m bits
    return m

def calculate_theoretical_latency_bounds(n: int, k: int, impl_type: str) -> Dict[str, float]:
    """
    Calculate theoretical latency bounds for insert and query operations.
    
    Theoretical bounds assume:
    - Hash computation: O(k) hash functions
    - Array access: O(1)
    
    We return bounds in microseconds (theoretical minimum).
    These are lower bounds, actual implementations will be slower.
    """
    # Base hash computation time (theoretical, in microseconds)
    # This is a rough estimate based on typical CPU speeds
    hash_time_us = 0.01  # 10 nanoseconds per hash (optimistic)
    
    # Array access time (theoretical, in microseconds)
    access_time_us = 0.001  # 1 nanosecond per access (optimistic)
    
    # Total operations: k hashes + k array accesses
    total_ops = k * 2
    
    theoretical_latency_us = (hash_time_us + access_time_us) * total_ops
    
    return {
        'insert_latency_us': theoretical_latency_us,
        'query_latency_us': theoretical_latency_us,
        'operations_count': total_ops
    }

def generate_theoretical_baselines() -> List[Dict[str, Any]]:
    """
    Generate theoretical baseline calculations for all configurations.
    
    Returns a list of dictionaries containing:
    - dataset_size: n
    - fpr: p
    - implementation: impl_type
    - optimal_bits: m
    - bits_per_element: m/n
    - optimal_k: k
    - theoretical_memory_bytes: m / 8
    - theoretical_latency_bounds: dict with insert/query latencies
    - timestamp: when calculation was performed
    """
    results = []
    timestamp = datetime.now().isoformat()
    
    for n in DATASET_SIZES:
        for p in FPR_TARGETS:
            k = calculate_optimal_k(p)
            m = calculate_optimal_bits(n, p)
            bits_per_element = m / n
            memory_bytes = m / 8.0
            
            latency_bounds = calculate_theoretical_latency_bounds(n, k, 'BitsetBloomFilter')
            
            for impl_type in IMPLEMENTATIONS:
                result = {
                    'dataset_size': n,
                    'fpr': p,
                    'implementation': impl_type,
                    'optimal_bits': m,
                    'bits_per_element': bits_per_element,
                    'optimal_k': k,
                    'theoretical_memory_bytes': memory_bytes,
                    'theoretical_memory_bits': m,
                    'theoretical_latency_bounds': latency_bounds,
                    'timestamp': timestamp
                }
                results.append(result)
    
    return results

def write_theoretical_baselines_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Write theoretical baseline results to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        'dataset_size', 'fpr', 'implementation', 
        'optimal_bits', 'bits_per_element', 'optimal_k',
        'theoretical_memory_bytes', 'theoretical_memory_bits',
        'insert_latency_us', 'query_latency_us', 'operations_count',
        'timestamp'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                'dataset_size': result['dataset_size'],
                'fpr': result['fpr'],
                'implementation': result['implementation'],
                'optimal_bits': result['optimal_bits'],
                'bits_per_element': result['bits_per_element'],
                'optimal_k': result['optimal_k'],
                'theoretical_memory_bytes': result['theoretical_memory_bytes'],
                'theoretical_memory_bits': result['theoretical_memory_bits'],
                'insert_latency_us': result['theoretical_latency_bounds']['insert_latency_us'],
                'query_latency_us': result['theoretical_latency_bounds']['query_latency_us'],
                'operations_count': result['theoretical_latency_bounds']['operations_count'],
                'timestamp': result['timestamp']
            }
            writer.writerow(row)

def write_theoretical_baselines_json(results: List[Dict[str, Any]], output_path: str):
    """
    Write theoretical baseline results to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as jsonfile:
        json.dump(results, jsonfile, indent=2)

def main():
    """
    Main function to generate theoretical baselines and write to results directory.
    """
    # Define output paths
    results_dir = 'results/benchmarks'
    csv_output = os.path.join(results_dir, 'theoretical_baselines.csv')
    json_output = os.path.join(results_dir, 'theoretical_baselines.json')
    
    print("Generating theoretical baselines...")
    print(f"Dataset sizes: {DATASET_SIZES}")
    print(f"FPR targets: {FPR_TARGETS}")
    print(f"Implementations: {IMPLEMENTATIONS}")
    
    # Generate baselines
    results = generate_theoretical_baselines()
    
    # Write outputs
    write_theoretical_baselines_csv(results, csv_output)
    write_theoretical_baselines_json(results, json_output)
    
    print(f"Theoretical baselines written to:")
    print(f"  CSV: {csv_output}")
    print(f"  JSON: {json_output}")
    
    # Print summary
    print(f"\nTotal configurations: {len(results)}")
    print(f"  Dataset sizes: {len(DATASET_SIZES)}")
    print(f"  FPR targets: {len(FPR_TARGETS)}")
    print(f"  Implementations: {len(IMPLEMENTATIONS)}")
    
    # Verify formula: bits = n * log2(1/p) / ln(2)^2
    # This is equivalent to: bits = -n * ln(p) / (ln(2)^2)
    sample_n = 100000
    sample_p = 0.01
    sample_k = calculate_optimal_k(sample_p)
    sample_m = calculate_optimal_bits(sample_n, sample_p)
    
    print(f"\nVerification for n={sample_n}, p={sample_p}:")
    print(f"  Optimal k: {sample_k}")
    print(f"  Optimal m (bits): {sample_m}")
    print(f"  Bits per element: {sample_m / sample_n:.2f}")
    print(f"  Memory (bytes): {sample_m / 8:.2f}")

if __name__ == '__main__':
    main()
