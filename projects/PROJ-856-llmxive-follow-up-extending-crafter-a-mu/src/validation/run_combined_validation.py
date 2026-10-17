"""
Compatibility wrapper.

The original quick‑start documentation refers to ``src.validation.run_validation``.
This module simply re‑exports the same entry point so that both names work.
"""

from .run_validation import main

if __name__ == "__main__":
    raise SystemExit(main())