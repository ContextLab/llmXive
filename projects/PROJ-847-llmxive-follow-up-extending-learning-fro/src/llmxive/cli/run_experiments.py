"""Legacy entry‑point that forwards to the new implementation.

Allows execution via ``python -m src.llmxive.cli.run_experiments``.
"""
from __future__ import annotations

import sys

from code.run_experiments import main

if __name__ == "__main__":
    sys.exit(main())
