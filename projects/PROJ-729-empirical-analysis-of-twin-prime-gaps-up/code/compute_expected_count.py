"""T013b-b: Compute and save the Hardy-Littlewood expected twin prime count.

Calls calculate_hardy_littlewood_expected_count(10**9) from
code/generate_primes.py (implemented in T013b-a), logs the result,
and saves it to data/results/expected_count.json with key
"expected_count".
"""

import sys
import json
from pathlib import Path

# Allow running from repo root or project directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import get_config, ensure_directories
from utils import setup_logging, exit_with_error
from generate_primes import calculate_hardy_littlewood_expected_count

# Twin‑prime constant (Hardy–Littlewood C₂)
HARDY_LITTLEWOOD_CONSTANT = 0.660161815846869573927812110014

def get_theoretical_count(x: float) -> float:
    """Return the Hardy‑Littlewood expected count of twin prime pairs up to x.

    The standard Hardy–Littlewood conjecture for twin primes is

        π₂(x) ≈ 2·C₂·x / (log x)²

    where C₂ is the twin‑prime constant defined above.
    """
    if x <= 2:
        return 0.0
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError(f"x must be a real number, got {type(x).__name__}")
    x = float(x)
    if x != x or x == float('inf'):
        raise ValueError("x must be a finite number")
    import math
    return 2.0 * HARDY_LITTLEWOOD_CONSTANT * x / (math.log(x) ** 2)

def get_actual_count(limit):
    """Placeholder for actual count retrieval (not used in this module).

    Reads the actual count from data/raw/twin_primes.csv if it exists,
    otherwise raises FileNotFoundError.
    """
    config = get_config()
    csv_path = Path(config["paths"]["raw"]) / "twin_primes.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Generated dataset not found at {csv_path}; "
            f"run code/generate_primes.py first."
        )
    with open(csv_path, "r") as f:
        # Skip header
        next(f)
        return sum(1 for _ in f)


def main():
    logger = setup_logging()
    try:
        config = get_config()
        ensure_directories([config["paths"]["results"]])

        limit = int(config["limits"]["max_prime"])
        expected_count = get_theoretical_count(limit)
        logger.info(
            "Hardy‑Littlewood expected twin prime count up to %d: %.2f",
            limit,
            expected_count,
        )
        print(
            f"Hardy‑Littlewood expected twin prime count up to {limit}: "
            f"{expected_count:.6f}"
        )

        output_path = Path(config["paths"]["results"]) / "expected_count.json"
        with open(output_path, "w") as f:
            json.dump({"expected_count": expected_count}, f, indent=2)
        logger.info("Saved expected count to %s", output_path)
    except Exception as exc:  # fail loudly, no fallback
        exit_with_error(f"Failed to compute/save expected count: {exc}", 1)


if __name__ == "__main__":
    main()