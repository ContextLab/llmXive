"""CI check for the Physical Stability Filter.

This script loads atomic seed structures from ``data/raw/atomic_seeds/``,
applies the stability filter defined in ``utils.validation.filter_stable_structures``,
and verifies that no more than 5 % of the seeds are rejected.  The script exits
with a non‑zero status code if the rejection rate exceeds the allowed threshold,
causing the continuous‑integration pipeline to fail.

Usage (as part of CI):
    python code/ci/check_physical_stability.py
"""
import sys
from pathlib import Path

from ase import io
from utils.validation import filter_stable_structures

# Directory containing the atomic seed files (XYZ, POSCAR, etc.).
SEEDS_DIR = Path("data/raw/atomic_seeds")


def load_seed_structures(seeds_dir: Path):
    """Load all atomic structures from *seeds_dir*.

    Returns
    -------
    List[ase.Atoms]
        A list of ``Atoms`` objects, one per file found in the directory.
    """
    if not seeds_dir.is_dir():
        raise FileNotFoundError(f"Seeds directory does not exist: {seeds_dir}")

    structures = []
    for file_path in seeds_dir.iterdir():
        if file_path.is_file() and not file_path.name.startswith("."):
            try:
                atoms = io.read(file_path)
                structures.append(atoms)
            except Exception as exc:
                # Propagate the error – a failure to read a seed should abort CI.
                raise RuntimeError(f"Failed to read seed file {file_path}: {exc}") from exc
    return structures


def main():
    # Load seed structures.
    try:
        seed_structures = load_seed_structures(SEEDS_DIR)
    except Exception as e:
        print(f"[ERROR] Unable to load seed structures: {e}", file=sys.stderr)
        sys.exit(2)

    total_seeds = len(seed_structures)
    if total_seeds == 0:
        print("[ERROR] No seed files found in the expected directory.", file=sys.stderr)
        sys.exit(2)

    # Apply the physical stability filter.
    stable_structures = filter_stable_structures(seed_structures)

    stable_count = len(stable_structures)
    rejected_count = total_seeds - stable_count
    pass_rate = stable_count / total_seeds

    # Reporting.
    print(f"Total seeds processed: {total_seeds}")
    print(f"Stable seeds: {stable_count}")
    print(f"Rejected seeds: {rejected_count}")
    print(f"Pass rate: {pass_rate:.2%}")

    # CI gate: fail if more than 5 % are rejected (i.e., pass rate < 95 %).
    if pass_rate < 0.95:
        print(
            f"[FAIL] Physical stability filter rejected {rejected_count} "
            f"out of {total_seeds} seeds (>5 % rejection).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[PASS] Physical stability filter acceptance rate meets the required threshold.")
    sys.exit(0)


if __name__ == "__main__":
    main()