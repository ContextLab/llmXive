"""
correlations_main_runner.py
---------------------------
Small wrapper that simply calls ``correlations.main``.  The quick‑start
script expects a ``main`` function in this module, so we expose it here.
"""
import logging
from analysis.correlations import main as correlations_main

def main() -> None:
    """Entry point used by ``code/main.py`` or the quick‑start run‑book."""
    logging.basicConfig(level=logging.INFO)
    correlations_main()

if __name__ == "__main__":
    main()