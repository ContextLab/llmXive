"""
Entry‑point module to allow ``python -m ruff`` execution.
It simply forwards to :func:`ruff.main`.
"""

from . import main

if __name__ == "__main__":
    main()
