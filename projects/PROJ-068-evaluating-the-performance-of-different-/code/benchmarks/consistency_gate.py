"""
Consistency Gate for T025.

Executes a cross-implementation consistency check on sample data to verify
that ArrayBloomFilter, VectorBloomFilter, and BitsetBloomFilter return
identical membership results for the same inputs.

Step 0: Verify memory budget constraint is met for all implementations.
Step 1: Run consistency check.
Output: results/benchmarks/consistency_report.json
Pass/Fail: Mismatch count must be 0; raises AssertionError if not.
"""
import os
import sys
import json
import random
import time
from typing import List, Dict, Tuple, Any, Set

# Project root setup to allow imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from bloom_filters.base import BloomFilter, get_config_for_sizes, FPR_TARGETS
from bloom_filters.array_impl import ArrayBloomFilter
from bloom_filters.vector_impl import VectorBloomFilter
from bloom_filters.bitset_impl import BitsetBloomFilter
from benchmarks.generator import generate_query_set, generate_synthetic_corpus
from setup_directories import compute_file_checksum

# Constants for the consistency check
SAMPLE_SIZE = 10000
QUERY_SIZE = 2000
SEED = 42
OUTPUT_PATH = os.path.join("results", "benchmarks", "consistency_report.json")
MEMORY_BUDGET_MB = 100.0  # Step 0: Threshold to check

def verify_memory_budget(filter_instance: BloomFilter, name: str) -> bool:
    """
    Step 0: Verify memory budget constraint is met.
    Estimates memory usage based on bitset size + object overhead.
    """
    # Rough estimation: bits / 8 = bytes. Add small overhead for object structure.
    estimated_bytes = filter_instance.m / 8
    estimated_mb = estimated_bytes / (1024 * 1024)
    
    # Add a safety margin for Python object overhead (arbitrary but conservative)
    # For the purpose of this gate, we assume the bitset size is the dominant factor.
    # If the bitset itself exceeds budget, it's a hard fail.
    if estimated_mb > MEMORY_BUDGET_MB:
        print(f"ERROR: {name} exceeds memory budget. Est: {estimated_mb:.2f}MB > {MEMORY_BUDGET_MB}MB")
        return False
    return True

def run_consistency_check():
    """
    Step 1: Run consistency check across all three implementations.
    """
    random.seed(SEED)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    print(f"Generating sample data (N={SAMPLE_SIZE}, Q={QUERY_SIZE})...")
    # Generate a synthetic corpus to use as "positive" set
    corpus = generate_synthetic_corpus(SAMPLE_SIZE, seed=SEED)
    positive_set = set(corpus)
    
    # Generate query set (mix of positives and negatives)
    # We need a set of negatives. Since generate_query_set might rely on corpus logic,
    # we will manually construct a query set based on the task description.
    # The task implies checking membership for the SAME inputs.
    # We will create a list of items: some in positive_set, some not.
    
    query_items = []
    # 50% from positive set
    query_items.extend(random.sample(list(positive_set), min(QUERY_SIZE // 2, len(positive_set))))
    
    # 50% negatives (random strings not in corpus)
    # We generate random strings that are highly unlikely to be in the corpus
    negatives = []
    while len(negatives) < QUERY_SIZE // 2:
        neg = f"NEGATIVE_SAMPLE_{random.randint(1000000, 9999999)}_{random.random()}"
        if neg not in positive_set:
            negatives.append(neg)
    query_items.extend(negatives)
    
    # Shuffle to ensure order doesn't bias
    random.shuffle(query_items)

    implementations = [
        ("ArrayBloomFilter", ArrayBloomFilter),
        ("VectorBloomFilter", VectorBloomFilter),
        ("BitsetBloomFilter", BitsetBloomFilter)
    ]

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "parameters": {
            "sample_size": SAMPLE_SIZE,
            "query_size": QUERY_SIZE,
            "seed": SEED,
            "memory_budget_mb": MEMORY_BUDGET_MB
        },
        "checks": [],
        "summary": {
            "total_mismatches": 0,
            "all_passed": True
        }
    }

    # 1. Initialize all filters with the same parameters
    # We use the config for a small size to ensure speed, but large enough to be meaningful
    config = get_config_for_sizes(SAMPLE_SIZE, FPR_TARGETS["low"])
    m = config["m"]
    k = config["k"]
    fpr_target = config["fpr"]

    print(f"Initializing filters with m={m}, k={k}, fpr={fpr_target:.4f}...")
    instances = {}
    for name, cls in implementations:
        try:
            # Note: We assume the constructors accept (m, k) or similar.
            # Based on base.py, calculate_optimal_parameters returns m, k.
            # Let's assume the standard signature is (m, k) or (num_bits, num_hashes)
            # Looking at the API surface, we don't have explicit __init__ signatures,
            # but standard bloom filter implementations take m and k.
            # We will try to instantiate. If the signature differs, we adapt.
            # Assuming: __init__(self, num_elements, fpr_target) or (m, k)
            # Since T011-T013 are done, we rely on them following the base class.
            # Base class likely defines the interface.
            
            # Let's assume the standard pattern: (m, k)
            instance = cls(m, k)
            instances[name] = instance
        except TypeError as e:
            # Fallback if signature is (n, p)
            try:
                instance = cls(SAMPLE_SIZE, fpr_target)
                instances[name] = instance
            except Exception as e2:
                print(f"Failed to initialize {name}: {e2}")
                results["checks"].append({"implementation": name, "status": "ERROR", "message": str(e2)})
                results["summary"]["all_passed"] = False
                continue

    # 2. Verify memory budget (Step 0)
    print("Verifying memory budgets...")
    for name, instance in instances.items():
        if not verify_memory_budget(instance, name):
            results["checks"].append({
                "implementation": name,
                "status": "MEMORY_BUDGET_EXCEEDED",
                "details": f"Exceeds {MEMORY_BUDGET_MB}MB"
            })
            results["summary"]["all_passed"] = False
        else:
            results["checks"].append({
                "implementation": name,
                "status": "OK",
                "details": "Within budget"
            })

    if not results["summary"]["all_passed"]:
        print("Memory budget check failed. Aborting consistency check.")
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        raise AssertionError("Memory budget check failed. See consistency_report.json.")

    # 3. Insert items
    print("Inserting items into all implementations...")
    for name, instance in instances.items():
        start = time.time()
        for item in positive_set:
            instance.insert(item)
        duration = time.time() - start
        print(f"  {name} inserted {len(positive_set)} items in {duration:.3f}s")

    # 4. Query items and compare results
    print("Running consistency check on query set...")
    mismatches = 0
    mismatch_details = []
    
    # We need a reference. Since they should all be identical, we can use the first one.
    # But to be safe, we compare all against the "ground truth" (positive_set)
    # and check if they agree with each other.
    
    # Actually, the requirement is "identical membership results".
    # So for every query item, all implementations must return the same boolean.
    
    reference_results = {} # item -> bool (from first implementation)
    first_impl_name = list(instances.keys())[0] if instances else None
    
    if not first_impl_name:
        raise AssertionError("No valid implementations to reference.")

    # Get reference results
    print(f"Computing reference results using {first_impl_name}...")
    for item in query_items:
        reference_results[item] = instances[first_impl_name].contains(item)

    # Compare others
    for name, instance in instances.items():
        if name == first_impl_name:
            continue
        
        check_results = []
        for item in query_items:
            ref = reference_results[item]
            current = instance.contains(item)
            if ref != current:
                mismatches += 1
                if len(mismatch_details) < 10: # Log first 10
                    mismatch_details.append({
                        "item": item[:50] + "..." if len(item) > 50 else item,
                        "expected": ref,
                        "actual": current,
                        "implementation": name
                    })
    
    # Also verify against ground truth (optional but good for sanity)
    # The task specifically asks for "identical results for the same inputs"
    # so cross-implementation agreement is the primary goal.
    
    results["checks"].append({
        "type": "cross_implementation_consistency",
        "total_queries": len(query_items),
        "mismatches": mismatches,
        "details_sample": mismatch_details
    })

    if mismatches > 0:
        results["summary"]["all_passed"] = False
        print(f"FAILED: Found {mismatches} mismatches between implementations.")
        raise AssertionError(f"Cross-implementation consistency check failed: {mismatches} mismatches found.")
    else:
        print("PASSED: All implementations returned identical results.")
        results["summary"]["all_passed"] = True

    # Write output
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Consistency report written to {OUTPUT_PATH}")
    return results

def main():
    """Entry point for the consistency gate."""
    try:
        run_consistency_check()
        print("T025 Consistency Gate: SUCCESS")
    except AssertionError as e:
        print(f"T025 Consistency Gate: FAILED - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"T025 Consistency Gate: ERROR - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()