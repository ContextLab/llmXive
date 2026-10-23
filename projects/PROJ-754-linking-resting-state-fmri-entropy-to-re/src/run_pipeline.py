"""
Compatibility wrapper for the historic ``src.run_pipeline`` import.

The original implementation lives in ``code.src.run_pipeline``.  This
module simply forwards the ``main`` function so that external code (e.g.
the test suite) can ``import src.run_pipeline`` without having to know the
new location.
"""
from code.src.run_pipeline import main  # noqa: F401
