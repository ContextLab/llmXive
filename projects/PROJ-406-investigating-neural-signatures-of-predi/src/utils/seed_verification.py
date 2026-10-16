"""
Seed verification script.

This script demonstrates that the global random seed utility produces
deterministic NumPy random draws. It generates two draws, each after
resetting the global seed to the same value, and appends the results to
``outputs/seed_verification.log``. The resulting log should contain two
identical lines, satisfying the reproducibility verification step for
task T000.
"""

import numpy as np
from llmxive_toolkit import paths
from src.utils.seed import set_global_seed, DEFAULT_SEED

def main() -> None:
    # Path to the verification log inside the project ``outputs`` folder.
    log_path = paths.outputs("seed_verification.log")
    # Ensure the parent directory exists (paths helper does this automatically).
    # Open in append mode so repeated runs add lines; the CI expects two lines.
    with open(log_path, "a", encoding="utf-8") as f:
        # First draw
        set_global_seed(DEFAULT_SEED)
        first = np.random.rand()
        f.write(f"{first}\\n")
        # Second draw (reset seed to the same value)
        set_global_seed(DEFAULT_SEED)
        second = np.random.rand()
        f.write(f"{second}\\n")

if __name__ == "__main__":
    main()
