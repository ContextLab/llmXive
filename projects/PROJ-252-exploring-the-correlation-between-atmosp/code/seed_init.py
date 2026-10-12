"""
Seed initialization step (task T001).

Sets the deterministic random seeds for NumPy and the built-in ``random``
module, writes ``logs/seed_initialization.log`` confirming that the seeds
were set, prints ``Pipeline completed successfully`` and exits with code 0.
"""
import random
import sys
from datetime import datetime, timezone

import numpy as np

from llmxive_toolkit import paths

RANDOM_SEED = 42


def main() -> int:
    # Set the deterministic seeds.
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # Evidence that the seeds are actually in effect: the first draw from
    # each generator must equal the well-known first value of the seeded
    # stream for seed 42.
    py_first = random.random()
    np_first = float(np.random.random())
    seeded_ok = (
        abs(py_first - 0.6394267984578837) < 1e-12
        and abs(np_first - 0.3745401188473625) < 1e-12
    )

    log_path = paths.path("logs", "seed_initialization.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Seed initialization run at {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"random.seed({RANDOM_SEED}) set: True\n")
        f.write(f"np.random.seed({RANDOM_SEED}) set: True\n")
        f.write(f"random.seed confirmation: first draw = {py_first!r}\n")
        f.write(f"np.random.seed confirmation: first draw = {np_first!r}\n")
        f.write(f"seeds_verified: {seeded_ok}\n")

    if not seeded_ok:
        print("ERROR: seed verification failed", file=sys.stderr)
        return 1

    print("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
