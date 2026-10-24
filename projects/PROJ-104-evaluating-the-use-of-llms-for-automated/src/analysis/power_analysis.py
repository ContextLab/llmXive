"""
Wrapper for the power‑analysis script located in ``code.power_analysis``.
The run‑book expects ``python -m src.analysis.power_analysis``; this module
simply calls the real ``run_power_analysis`` function and exits with a
zero status code (the function itself writes the markdown report).
"""
from __future__ import annotations

import sys

from code.power_analysis import run_power_analysis

def main() -> int:
    """Execute the power‑analysis stage and return an exit code."""
    # ``run_power_analysis`` writes the report and returns a dict; we ignore the
    # return value because the CLI contract expects only a status code.
    run_power_analysis()
    return 0

if __name__ == "__main__":
    sys.exit(main())
