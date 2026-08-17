"""
CI script to verify the Physical Stability Filter.

This script loads all atomic seed structures from the
``data/raw/atomic_seeds`` directory, applies the stability filter
defined in ``utils.validation.filter_stable_structures`` and checks
the proportion of rejected seeds.  If more than 5 % of the seeds are
rejected the script exits with a non‑zero status code so that CI
can fail the build.

The script is deliberately simple and has no side‑effects other than
printing a short summary and exiting with the appropriate status.
"""

import sys
from pathlib import Path
from typing import List

from ase import io
from utils.validation import filter_stable_structures


def load_seed_structures(seeds_dir: Path = Path("data/raw/atomic_seeds")) -> List[io.Atoms]:
    """
    Load all atomic seed structures from ``seeds_dir``.

    Parameters
    ----------
    seeds_dir:
        Directory containing atomic seed files.  Supported formats are
        any format understood by ``ase.io.read`` (e.g. ``.xyz``, ``POSCAR``).

    Returns
    -------
    List[ase.Atoms]
        List of ``Atoms`` objects, one per file found.

    Raises
    ------
    FileNotFoundError
        If ``seeds_dir`` does not exist or contains no readable files.
    """
    if not seeds_dir.is_dir():
        raise FileNotFoundError(f"Seed directory '{seeds_dir}' does not exist.")

    # ``ase.io.read`` can read a single file; we iterate over all files.
    structures = []
    for file_path in sorted(seeds_dir.iterdir()):
        # Skip hidden files or directories
        if file_path.is_file() and not file_path.name.startswith("."):
            try:
                atoms = io.read(file_path)
                structures.append(atoms)
            except Exception as exc:
                # Propagate a clear error – we do not silently skip unreadable files.
                raise RuntimeError(f"Failed to read seed file '{file_path}': {exc}") from exc

    if not structures:
        raise FileNotFoundError(f"No seed structures found in '{seeds_dir}'.")

    return structures


def main() -> None:
    """
    Entry point for the CI check.

    Loads seed structures, filters them for physical stability and
    computes the rejection rate.  If the rejection rate exceeds 5 % the
    process exits with status code 1, otherwise with status code 0.
    """
    try:
        seeds = load_seed_structures()
    except Exception as e:
        print(f"Error loading seed structures: {e}", file=sys.stderr)
        sys.exit(2)  # distinct exit code for loading failures

    total = len(seeds)
    stable = filter_stable_structures(seeds)
    stable_count = len(stable)
    rejected = total - stable_count
    rejection_rate = rejected / total if total > 0 else 0.0

    # Human‑readable summary
    print(f"Physical Stability Filter check:")
    print(f"  Total seeds          : {total}")
    print(f"  Stable seeds         : {stable_count}")
    print(f"  Rejected seeds       : {rejected}")
    print(f"  Rejection rate       : {rejection_rate:.2%}")

    # CI failure condition (>5 % rejection)
    if rejection_rate > 0.05:
        print(
            f"FAILURE: Rejection rate ({rejection_rate:.2%}) exceeds the allowed 5 %.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("PASS: Rejection rate is within the allowed threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()
