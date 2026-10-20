"""
Dummy script used by the test suite to verify the benchmark instrumentation.

It simply performs a modest amount of deterministic work inside the
``benchmark`` context manager, causing a JSON report
``results/reports/benchmark_dummy.json`` to be created with numeric
``wall_time_sec`` and ``peak_memory_mb`` fields.
"""

import sys
import time
import logging
from pathlib import Path

# Make the project's code/ package importable regardless of the
# working directory the script is launched from.
_CODE_DIR = Path(__file__).resolve().parent.parent / "code"
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from benchmark import benchmark

# Configure a minimal logger for the script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _workload():
    """
    Perform a deterministic, CPU-bound workload that runs quickly.

    The exact numbers are not important; they just ensure the block
    takes a measurable amount of time and allocates a little memory
    so the peak-memory reading is meaningful.
    """
    total = 0
    for i in range(500_000):
        total += i * i
    # Sleep a tiny amount to guarantee a non-zero wall-clock duration
    time.sleep(0.01)
    return total


def main():
    logger.info("Running dummy benchmark...")
    with benchmark("dummy"):
        _ = _workload()
    logger.info(
        "Dummy benchmark completed. Report written to "
        "results/reports/benchmark_dummy.json"
    )


if __name__ == "__main__":
    main()