"""
code/data/download.py
---------------------

Thin wrapper that re‑exports the implementation located in
``src.data.download``.  The project’s public documentation (quickstart)
refers to this path, while the test suite imports the ``src`` module.
Providing the wrapper keeps both import styles functional without
duplicating logic.
"""

from src.data.download import main as _impl_main

def main() -> None:
    """
    CLI entry point used by ``python -m code.data.download``.
    """
    _impl_main()
