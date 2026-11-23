"""
code/data/download_real.py

Thin wrapper that delegates to the real acquisition implementation in
``src.data.acquire_real``. This module exists to preserve the original
task‑level import path used by the quickstart and test suite.
"""

from src.data.acquire_real import main as acquire_real_main

def main() -> None:
    """Execute the real data acquisition process."""
    acquire_real_main()

if __name__ == "__main__":
    main()