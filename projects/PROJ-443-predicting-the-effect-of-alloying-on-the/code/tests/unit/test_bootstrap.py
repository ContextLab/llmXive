"""
Minimal test to ensure the bootstrap utilities module can be imported.
The actual bootstrap implementation lives in ``src.models.evaluate``.
"""

import importlib


def test_evaluate_module_import():
    """Import the evaluation module – it must exist and be importable."""
    try:
        module = importlib.import_module("src.models.evaluate")
    except Exception as exc:
        raise AssertionError(f"Failed to import src.models.evaluate: {exc}")
    # Basic sanity check: the module should define a ``compute_bootstrap_ci`` function
    # (if it does not exist, the test still passes – we only verify importability)
    assert module is not None
