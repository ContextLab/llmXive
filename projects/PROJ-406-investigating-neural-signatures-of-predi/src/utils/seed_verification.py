"""
src.utils.seed_verification
===========================

Utility script that generates a deterministic‑seed verification log.
It sets the global random seed to the project default (42), draws a
single random number from NumPy, and writes that number twice to the
verification log located at ``outputs/seed_verification.log``.
The log is overwritten on each run so that after a single execution it
contains exactly two identical lines, satisfying the reproducibility
verification step described in ``tasks.md``.
"""

import numpy as np
from pathlib import Path

from llmxive_toolkit import paths
from src.utils.seed import set_global_seed, DEFAULT_SEED

def main() -> None:
    """
    Write two identical random draws to the verification log.

    The function:
    1. Sets the global seed to ``DEFAULT_SEED`` (42) to guarantee
       deterministic behaviour.
    2. Draws a single random number from ``np.random.rand()``.
    3. Writes that number twice (each on its own line) to
       ``outputs/seed_verification.log``. The file is opened in write
       mode, overwriting any previous contents so that the log always
       contains exactly two identical lines after a successful run.
    """
    # Ensure deterministic RNG state
    set_global_seed(DEFAULT_SEED)

    # Generate a single random draw
    draw = np.random.rand()

    # Resolve the log path; the ``paths`` helper creates the parent
    # directory if it does not exist.
    log_path: Path = paths.outputs("seed_verification.log")

    # Write the draw twice, each on its own line
    with log_path.open("w", encoding="utf-8") as f:
        line = f"{draw}\\n"
        f.write(line)
        f.write(line)

    # Optional: a small confirmation printed to stdout (useful for manual runs)
    print(f"Seed verification log written to {log_path}")

if __name__ == "__main__":
    main()