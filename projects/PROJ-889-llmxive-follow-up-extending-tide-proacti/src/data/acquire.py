"""
acquire.py
-------------
Wrapper module that invokes the real dataset download routine.
This script is exposed as ``python -m src.data.acquire`` in the
quick‑start guide. It simply forwards to the implementation in
``code/data/download_real.py``.
"""

from code.data.download_real import main as _download_main

def main() -> None:
    """Execute the real CodeXGLUE download routine."""
    _download_main()

if __name__ == "__main__":
    main()
