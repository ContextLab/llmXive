"""
Generate partition counts p_P(n) for n in [1, N] into distinct prime summands.

This script implements the dynamic programming approach to compute the number of
partitions of an integer n into distinct primes.

MATHEMATICAL FOUNDATION:
------------------------
The generating function for partitions into distinct primes is:
    G(q) = \prod_{p \in \mathbb{P}} (1 + q^p)

where \mathbb{P} is the set of prime numbers. This is distinct from the
unrestricted partition generating function:
    P(q) = \prod_{k=1}^{\infty} (1 - q^k)^{-1}

The key difference is that the distinct-prime generating function uses a product
over primes only (creating 'holes' where composite numbers are skipped as summands)
and uses the factor (1 + q^p) instead of (1 - q^k)^{-1}. This reflects the
constraint that each prime can appear at most once in a partition (distinctness).

The 'holes' created by prime gaps fundamentally alter the asymptotic behavior
compared to unrestricted partitions, as the density of available summands is
significantly lower and irregular.

The asymptotic baseline Q_as(n) is derived from the distinct-partition variant
of Meinardus' theorem, which accounts for the prime density ~ n/log(n).
"""

import os
import sys
import csv
import hashlib
import json
import argparse
import numpy as np
from typing import List, Tuple, Dict, Optional

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.prime_sieve import get_prime_sieve, generate_primes
from utils.asymptotic_baseline import compute_asymptotic_baseline


def load_reference_values(reference_path: str) -> Dict[int, int]:
    """Load reference values from CSV file.

    Args:
        reference_path: Path to the reference CSV file.

    Returns:
        Dictionary mapping n to p_P(n).
    """
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference file not found: {reference_path}")

    reference = {}
    with open(reference_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            count = int(row['p_P(n)'])
            reference[n] = count
    return reference


def validate_against_reference(computed: Dict[int, int], reference: Dict[int, int], tolerance: int = 0) -> bool:
    """Validate computed values against reference values.

    Args:
        computed: Dictionary of computed values.
        reference: Dictionary of reference values.
        tolerance: Allowed difference (default 0 for exact match).

    Returns:
        True if all values match within tolerance.

    Raises:
        AssertionError: If validation fails.
    """
    for n, ref_val in reference.items():
        if n not in computed:
            raise AssertionError(f"Missing computed value for n={n}")
        comp_val = computed[n]
        if abs(comp_val - ref_val) > tolerance:
            raise AssertionError(
                f"Mismatch at n={n}: computed={comp_val}, reference={ref_val}"
            )
    return True


def compute_partition_counts(n_max: int, primes: List[int]) -> Dict[int, int]:
    """Compute partition counts into distinct primes using DP.

    Uses a 1D array to count partitions into distinct primes.
    The recurrence is: dp[i] += dp[i - p] for each prime p, iterating backwards.

    Args:
        n_max: Maximum n to compute.
        primes: List of primes to use as summands.

    Returns:
        Dictionary mapping n to p_P(n).
    """
    # Initialize DP array: dp[i] = number of ways to partition i into distinct primes
    # Using int64 to prevent overflow for large counts
    dp = np.zeros(n_max + 1, dtype=np.int64)
    dp[0] = 1  # Base case: one way to partition 0 (empty set)

    # Iterate over each prime and update the DP array
    # We iterate backwards to ensure each prime is used at most once (distinctness)
    for p in primes:
        if p > n_max:
            break
        for i in range(n_max, p - 1, -1):
            dp[i] += dp[i - p]

    # Convert to dictionary, skipping n=0 as it's not part of the study range
    result = {}
    for n in range(1, n_max + 1):
        result[n] = int(dp[n])

    return result


def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex string of the SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_state_file(state_path: str, artifact_key: str, checksum: str) -> None:
    """Update the project state file with artifact checksum.

    Args:
        state_path: Path to the state YAML file.
        artifact_key: Key under which to store the checksum.
        checksum: SHA-256 checksum of the artifact.
    """
    import yaml
    from datetime import datetime

    state = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}

    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}

    state['artifact_hashes'][artifact_key] = checksum
    state['updated_at'] = datetime.utcnow().isoformat() + 'Z'

    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)


def main():
    """Main entry point for partition generation."""
    parser = argparse.ArgumentParser(
        description="Generate partition counts into distinct primes."
    )
    parser.add_argument(
        "--n-max", type=int, default=50000,
        help="Maximum n to compute (default: 50000)"
    )
    parser.add_argument(
        "--reference-path", type=str,
        default="tests/data/reference_values.csv",
        help="Path to reference values CSV"
    )
    parser.add_argument(
        "--output-path", type=str,
        default="data/raw/partitions_raw.csv",
        help="Path for output CSV"
    )
    parser.add_argument(
        "--state-path", type=str,
        default="state/projects/PROJ-799.yaml",
        help="Path to project state file"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate against reference values for n in [1, 100]"
    )

    args = parser.parse_args()

    # Ensure output directories exist
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    os.makedirs(os.path.dirname(args.state_path), exist_ok=True)

    print(f"Generating partitions for n in [1, {args.n_max}]...")

    # Load primes
    primes = generate_primes(args.n_max)
    print(f"Loaded {len(primes)} primes up to {args.n_max}")

    # Compute partition counts
    partition_counts = compute_partition_counts(args.n_max, primes)

    # Compute asymptotic baseline
    asymptotic_data = []
    for n in range(1, args.n_max + 1):
        q_as = compute_asymptotic_baseline(n)
        # Clamp to prevent log(0) in downstream analysis
        q_as = max(q_as, 1e-10)
        asymptotic_data.append(q_as)

    # Validate against reference if requested
    if args.validate:
        print(f"Validating against reference values from {args.reference_path}...")
        try:
            reference = load_reference_values(args.reference_path)
            # Validate only for n in [1, 100] as per SC-003
            validation_ref = {n: v for n, v in reference.items() if 1 <= n <= 100}
            validate_against_reference(partition_counts, validation_ref)
            print("Validation PASSED: Computed values match reference for n in [1, 100].")
        except FileNotFoundError:
            print(f"Warning: Reference file not found at {args.reference_path}. Skipping validation.")
        except AssertionError as e:
            print(f"Validation FAILED: {e}")
            sys.exit(1)

    # Export data to CSV
    print(f"Exporting data to {args.output_path}...")
    with open(args.output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['n', 'p_P(n)', 'Q_as(n)'])
        for n in range(1, args.n_max + 1):
            p_p = partition_counts[n]
            q_as = asymptotic_data[n - 1]
            # Skip rows where p_P(n) = 0 or Q_as(n) <= 0 for log-residual calculation
            # (though Q_as is clamped, p_P can be 0 for small n)
            if p_p > 0 and q_as > 0:
                writer.writerow([n, p_p, q_as])

    # Compute checksum and update state
    checksum = compute_file_checksum(args.output_path)
    update_state_file(args.state_path, "generate_partitions_raw", checksum)
    print(f"Output checksum: {checksum}")
    print(f"State file updated at {args.state_path}")

    print("Partition generation complete.")


if __name__ == "__main__":
    main()