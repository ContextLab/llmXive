"""Thin wrapper to expose the ``code.run_pipeline`` entry point under the
top‑level ``src`` namespace.

The original project used ``src.run_pipeline`` as the canonical module
for the quick‑start commands (e.g. ``python -m src.run_pipeline``).  This
wrapper simply forwards to the implementation in ``code.run_pipeline``.
"""
from __future__ import annotations

from code.run_pipeline import main as _real_main

def main() -> int:
    """Execute the real pipeline and return its exit status."""
    return _real_main()

if __name__ == "__main__":
    raise SystemExit(main())
