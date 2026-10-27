"""
Utility script to generate the reproducibility verification log required by
task T000. It sets the global seed, draws two random numbers from NumPy,
and writes both numbers (one per line) to ``outputs/seed_verification.log``.
The two lines must be identical, satisfying the reproducibility check.
"""

from pathlib import Path
from llmxive_toolkit import paths
from src.utils.seed import set_global_seed
import numpy as np

def main() -> None:
    # Ensure deterministic behaviour
    set_global_seed(42)

    # Draw two random numbers
    val1 = np.random.rand()
    val2 = np.random.rand()

    # Write to the verification log
    log_path: Path = paths.outputs("seed_verification.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"{val1}\\n")
        f.write(f"{val2}\\n")

    # Simple sanity check – the two values should be identical
    assert np.isclose(val1, val2), "Seed reproducibility check failed!"

if __name__ == "__main__":
    main()
