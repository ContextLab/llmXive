"""
src/run_e2e.py
---------------
Wrapper module that provides a CLI entry point for the end‑to‑end pipeline.
Running ``python -m src.run_e2e`` invokes the implementation in
``code/src/run_e2e.py``.
"""

from code.src.run_e2e import main

if __name__ == "__main__":
    main()
