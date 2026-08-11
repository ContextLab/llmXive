"""
Generate exact partition counts p_P(n) for n in [1, n_max] into distinct prime summands.
Also compute the asymptotic baseline Q_as(n) using the distinct-partition variant
of Meinardus' theorem.

Generating Function:
The generating function for partitions into distinct prime summands is:
    G(q) = \prod_{p \in \mathbb{P}} (1 + q^p)
where \mathbb{P} is the set of prime numbers.

This is fundamentally different from the unrestricted partition function p(n),
whose generating function is:
    P(q) = \prod_{k=1}^{\infty} (1 - q^k)^{-1}

The distinct prime constraint imposes sparsity in the summands, leading to
a different asymptotic growth rate and statistical properties.
"""

import os
import sys
import csv
import hashlib
import json
import argparse
import logging
from typing import List, Dict, Any, Optional

import numpy as np

# Add parent directory to path for imports if running as script
if os.path.basename(os.getcwd()) == 'code':
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    # Assume running from project root or similar
    code_dir = os.path.dirname(os.path.abspath(__file__))
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)

from utils.prime_sieve import generate_primes
from utils.asymptotic_baseline import compute_asymptotic_baseline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_reference_values(filepath: str) -> Dict[int, int]:
    """Load reference values from CSV file."""
    ref_values = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Reference file not found: {filepath}")
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            count = int(row['p_P(n)'])
            ref_values[n] = count
    return ref_values

def validate_against_reference(computed: Dict[int, int], reference: Dict[int, int]) -> bool:
    """Validate computed values against reference for overlapping n."""
    common_n = set(computed.keys()) & set(reference.keys())
    if not common_n:
        logger.warning("No overlapping n values between computed and reference.")
        return True
    
    mismatches = []
    for n in sorted(common_n):
        if computed[n] != reference[n]:
            mismatches.append((n, computed[n], reference[n]))
    
    if mismatches:
        logger.error(f"Found {len(mismatches)} mismatches against reference values.")
        for n, c, r in mismatches[:5]:  # Log first 5
            logger.error(f"  n={n}: computed={c}, reference={r}")
        return False
    
    logger.info(f"Validation passed for {len(common_n)} overlapping n values.")
    return True

def compute_partition_counts(n_max: int, primes: List[int]) -> Dict[int, int]:
    """
    Compute p_P(n) for n in [1, n_max] using dynamic programming.
    Uses 1D array for memory efficiency, iterating only over primes.
    """
    # Initialize DP array: dp[i] = number of ways to partition i into distinct primes
    # Use int64 to prevent overflow for large counts
    dp = np.zeros(n_max + 1, dtype=np.int64)
    dp[0] = 1  # Base case: one way to partition 0 (empty set)
    
    # Iterate over each prime and update DP table
    # This enforces the "distinct" constraint because each prime is used at most once
    for p in primes:
        if p > n_max:
            break
        # Update from right to left to avoid reusing the same prime
        for i in range(n_max, p - 1, -1):
            dp[i] += dp[i - p]
    
    # Convert to dictionary, skipping n=0
    result = {}
    for n in range(1, n_max + 1):
        result[n] = int(dp[n])
    
    return result

def compute_asymptotic_baseline_series(n_max: int) -> Dict[int, float]:
    """Compute Q_as(n) for n in [1, n_max]."""
    result = {}
    for n in range(1, n_max + 1):
        q_as = compute_asymptotic_baseline(n)
        # Clamp to prevent log(0) in downstream steps
        result[n] = max(q_as, 1e-300)
    return result

def validate_partition_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate partition data and exclude invalid rows.
    Excludes rows where p_P(n) <= 0 or Q_as(n) <= 0.
    """
    valid_data = []
    excluded_count = 0
    
    for row in data:
        p_P_n = row.get('p_P(n)', 0)
        Q_as_n = row.get('Q_as(n)', 0)
        
        if p_P_n <= 0 or Q_as_n <= 0:
            excluded_count += 1
            continue
        
        valid_data.append(row)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows with non-positive counts.")
    
    return valid_data

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(checksum: str, artifact_key: str = "generate_partitions_raw"):
    """Update the project state file with the new checksum."""
    state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                              "state", "projects", "PROJ-799.yaml")
    
    # Ensure state directory exists
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    
    state_data = {}
    if os.path.exists(state_path):
        import yaml
        try:
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    state_data["artifact_hashes"][artifact_key] = checksum
    state_data["updated_at"] = __import__('datetime').datetime.now().isoformat()
    
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger.info(f"Updated state file with checksum for {artifact_key}")

def export_data(data: List[Dict[str, Any]], output_path: str):
    """Export partition data to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['n', 'p_P(n)', 'Q_as(n)']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Exported {len(data)} records to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate partition counts into distinct prime summands.'
    )
    parser.add_argument(
        '--n-max',
        type=int,
        default=50000,
        help='Maximum n value to compute partitions for (default: 50000)'
    )
    
    args = parser.parse_args()
    n_max = args.n_max
    
    # Log the chosen n_max
    logger.info(f"Starting partition generation with n_max = {n_max}")
    print(f"Running with n_max = {n_max}")
    
    # Determine paths relative to project structure
    # Assuming script is in code/ directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    utils_dir = os.path.join(project_root, "code", "utils")
    data_raw_dir = os.path.join(project_root, "data", "raw")
    tests_data_dir = os.path.join(project_root, "tests", "data")
    
    # Generate primes up to n_max
    logger.info(f"Generating primes up to {n_max}...")
    primes = generate_primes(n_max)
    logger.info(f"Found {len(primes)} primes up to {n_max}")
    
    # Load reference values for validation
    reference_path = os.path.join(tests_data_dir, "reference_values.csv")
    try:
        reference_values = load_reference_values(reference_path)
        logger.info(f"Loaded {len(reference_values)} reference values from {reference_path}")
    except FileNotFoundError:
        logger.warning(f"Reference file not found at {reference_path}. Skipping validation.")
        reference_values = {}
    
    # Compute partition counts
    logger.info("Computing partition counts using DP...")
    partition_counts = compute_partition_counts(n_max, primes)
    
    # Validate against reference if available
    if reference_values:
        validate_against_reference(partition_counts, reference_values)
    
    # Compute asymptotic baseline
    logger.info("Computing asymptotic baseline Q_as(n)...")
    asymptotic_baseline = compute_asymptotic_baseline_series(n_max)
    
    # Combine data
    data = []
    for n in range(1, n_max + 1):
        data.append({
            'n': n,
            'p_P(n)': partition_counts[n],
            'Q_as(n)': asymptotic_baseline[n]
        })
    
    # Validate data
    valid_data = validate_partition_data(data)
    
    # Export data
    output_path = os.path.join(data_raw_dir, "partitions_raw.csv")
    export_data(valid_data, output_path)
    
    # Compute checksum and update state
    checksum = compute_file_checksum(output_path)
    update_state_file(checksum)
    
    logger.info("Partition generation completed successfully.")
    print(f"Completed. Output written to {output_path}")

if __name__ == "__main__":
    main()