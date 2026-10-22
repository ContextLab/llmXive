"""
code/pipeline/run.py
--------------------

Thin wrapper that re‑exports the implementation located in
``src.pipeline.run``.  The public documentation (quickstart) refers
to this path, while the test suite imports the ``src`` module.
Providing the wrapper keeps both import styles functional without
duplicating logic.
"""

from src.pipeline.run import main as _impl_main

def main() -> None:
    """
    CLI entry point used by ``python -m code.pipeline.run``.
    """
    _impl_main()