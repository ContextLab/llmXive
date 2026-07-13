"""
save_correlation_results.py

Thin wrapper that invokes the full correlation analysis pipeline.
This script is deliberately tiny so that it can be added to the
quick‑start run‑book without pulling in any additional logic.
"""

from __future__ import annotations

import logging

from correlation_analysis import run_correlation_analysis

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main() -> None:
    """Run the correlation analysis and exit."""
    try:
        run_correlation_analysis()
    except Exception as e:
        logging.error("Failed to generate correlation results: %s", e)
        raise

if __name__ == "__main__":
    main()
