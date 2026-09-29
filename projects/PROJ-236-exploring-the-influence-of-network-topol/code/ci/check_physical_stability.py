"""
CI verification script for the Physical Stability Filter.

This script loads atomic seed structures, applies the physical stability
filter, and ensures that no more than 5 % of the seeds are rejected.
It exits with a non‑zero status code if the rejection rate exceeds the
threshold, causing the CI pipeline to fail.
"""

import sys
from typing import List

# The public API of this module is defined in the project’s API surface.
# We import the helper functions that already exist elsewhere in the codebase.
from utils.validation import filter_stable_structures
from ci.check_physical_stability import load_seed_structures  # type: ignore

def compute_rejection_rate(seeds: List, stable_seeds: List) -> float:
    """
    Compute the fraction of seeds rejected by the physical stability filter.

    Parameters
    ----------
    seeds : List
        The original list of seed structures.
    stable_seeds : List
        The subset of ``seeds`` that passed the stability filter.

    Returns
    -------
    float
        Rejection rate in the range [0, 1].
    """
    total = len(seeds)
    if total == 0:
        # An empty seed set is considered a failure because there is nothing
        # to validate; the CI should abort.
        raise ValueError("No seed structures were found.")
    rejected = total - len(stable_seeds)
    return rejected / total

def main() -> None:
    """
    Entry point for the CI check.

    The function performs the following steps:
    1. Load all atomic seed structures.
    2. Filter them with the physical stability filter.
    3. Compute the rejection rate.
    4. Print a short report.
    5. Exit with status 0 if the rejection rate ≤ 5 %; otherwise exit with
       status 1 to fail the CI job.
    """
    try:
        # Load the raw seed structures from ``data/raw/atomic_seeds/``.
        seed_structures = load_seed_structures()
    except Exception as exc:
        print(f"Failed to load seed structures: {exc}", file=sys.stderr)
        sys.exit(1)

    # Apply the physical stability filter.
    stable_structures = filter_stable_structures(seed_structures)

    try:
        rejection_rate = compute_rejection_rate(seed_structures, stable_structures)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    total = len(seed_structures)
    passed = len(stable_structures)
    pass_percent = (passed / total) * 100
    reject_percent = rejection_rate * 100

    print(
        f"Physical stability filter: {passed}/{total} seeds passed "
        f"({pass_percent:.2f} % pass, {reject_percent:.2f} % reject)."
    )

    # CI fails if more than 5 % of seeds are rejected.
    if rejection_rate > 0.05:
        print(
            f"ERROR: Rejection rate {reject_percent:.2f}% exceeds the 5 % threshold.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Success path.
    sys.exit(0)

if __name__ == "__main__":
    main()
