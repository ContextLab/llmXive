import logging
import sys
from pathlib import Path
from analysis import run_baseline_analysis

logger = logging.getLogger(__name__)

def main() -> int:
    """
    Executes baseline analysis and writes the raw output JSON.
    Returns 0 on success, non‑zero on failure.
    """
    try:
        # Use default arguments – the function handles defaults internally.
        run_baseline_analysis()
        return 0
    except Exception as e:
        logger.exception("Baseline analysis failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
