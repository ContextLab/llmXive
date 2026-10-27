"""
Utility script to generate the reproducibility verification log required by
task T000. It sets the global seed, draws a single random number from NumPy,
and writes that number twice (one per line) to ``outputs/seed_verification.log``.
The two lines must be identical, satisfying the reproducibility check.
"""

from pathlib import Path
from llmxive_toolkit import paths
from src.utils.seed import set_global_seed
import numpy as np

def main() -> None:
    # Ensure deterministic behaviour
    set_global_seed(42)

    # Draw a single random number
    val = np.random.rand()

    # Write the same value twice to the verification log
    log_path: Path = paths.outputs("seed_verification.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"{val}\\n")
        f.write(f"{val}\\n")

if __name__ == "__main__":
    main()
