"""
Validation module to ensure all three Bloom filter implementations
produce identical membership results for the same query set.
"""
import os
import sys
import json
import random
from typing import List, Dict, Tuple, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bloom_filters.base import BloomFilter, get_config_for_sizes, FPR_TARGETS
from bloom_filters.array_impl import ArrayBloomFilter
from bloom_filters.vector_impl import VectorBloomFilter
from bloom_filters.bitset_impl import BitsetBloomFilter

# Sample data generation for validation (small scale)
def generate_test_data(count: int, seed: int = 42) -> List[str]:
    """Generate a deterministic set of test strings."""
    random.seed(seed)
    words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew"]
    data = []
    for _ in range(count):
        # Create random strings from the word list
        length = random.randint(5, 15)
        word = "".join(random.choices(words, k=length))
        data.append(word)
    return data


def run_consistency_check(
    size: int,
    fpr: float,
    test_data: Optional[List[str]] = None,
    query_ratio: float = 0.5
) -> Dict[str, Any]:
    """
    Run a consistency check between all three Bloom filter implementations.

    Args:
        size: Number of elements to insert.
        fpr: Target false positive rate.
        test_data: Optional pre-generated test data. If None, generates randomly.
        query_ratio: Ratio of test_data to use for querying (for negative queries).

    Returns:
        Dictionary containing validation results.
    """
    # Generate test data if not provided
    if test_data is None:
        test_data = generate_test_data(size * 2)  # Generate more than needed for negative queries

    insert_data = test_data[:size]
    query_data = test_data[size:]

    # Initialize all three implementations
    m, k = calculate_optimal_parameters_for_fpr(size, fpr)

    filters = {
        "ArrayBloomFilter": ArrayBloomFilter(size, fpr),
        "VectorBloomFilter": VectorBloomFilter(size, fpr),
        "BitsetBloomFilter": BitsetBloomFilter(size, fpr)
    }

    # Insert data into all filters
    for name, bf in filters.items():
        for item in insert_data:
            bf.insert(item)

    # Run consistency checks
    results = {
        "size": size,
        "fpr": fpr,
        "m": m,
        "k": k,
        "query_count": len(query_data),
        "comparisons": {}
    }

    # Compare each pair of implementations
    impl_names = list(filters.keys())
    for i in range(len(impl_names)):
        for j in range(i + 1, len(impl_names)):
            name1 = impl_names[i]
            name2 = impl_names[j]
            bf1 = filters[name1]
            bf2 = filters[name2]

            validation_result = bf1.validate_consistency(bf2, query_data)
            results["comparisons"][f"{name1}_vs_{name2}"] = validation_result

    # Overall pass/fail
    all_pass = True
    for comp_name, comp_result in results["comparisons"].items():
        if comp_result["mismatches"] > 0:
            all_pass = False
            break

    results["passed"] = all_pass
    return results


def calculate_optimal_parameters_for_fpr(n: int, p: float) -> Tuple[int, int]:
    """Calculate optimal m and k for given n and p."""
    import math
    if n <= 0:
        raise ValueError("Number of elements must be positive")
    if p <= 0 or p >= 1:
        raise ValueError("False positive rate must be between 0 and 1 (exclusive)")

    m = - (n * math.log(p)) / (math.log(2) ** 2)
    k = (m / n) * math.log(2)

    return int(math.ceil(m)), int(math.ceil(k))


def main():
    """Main entry point for the consistency validation script."""
    print("Running Bloom Filter Consistency Validation...")

    # Test configurations (small scale for validation)
    test_configs = [
        {"size": 1000, "fpr": 0.01},
        {"size": 5000, "fpr": 0.01},
        {"size": 10000, "fpr": 0.001},
    ]

    output_dir = "results/benchmarks"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "consistency_report.json")

    all_results = []
    all_passed = True

    for config in test_configs:
        print(f"Testing size={config['size']}, fpr={config['fpr']}...")
        result = run_consistency_check(config["size"], config["fpr"])
        all_results.append(result)

        if not result["passed"]:
            all_passed = False
            print(f"  ❌ FAILED: {result['comparisons']}")
        else:
            print(f"  ✅ PASSED: {result['query_count']} queries, 0 mismatches")

    # Write results to file
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults written to {output_file}")

    if not all_passed:
        print("\n⚠️  CONSISTENCY CHECK FAILED: Mismatches detected between implementations!")
        sys.exit(1)
    else:
        print("\n✅ CONSISTENCY CHECK PASSED: All implementations produce identical results.")
        sys.exit(0)


if __name__ == "__main__":
    main()
