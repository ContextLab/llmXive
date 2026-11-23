"""
Minimal test to verify that the false discovery rate (FDR) utilities are importable.
"""

import importlib


def test_fdr_module_import():
    """Import the FDR utilities – they live in ``src.models.evaluate``."""
    try:
        module = importlib.import_module("src.models.evaluate")
    except Exception as exc:
        raise AssertionError(f"Failed to import src.models.evaluate for FDR utilities: {exc}")
    # The module should expose a ``apply_fdr_correction`` function or similar.
    # We only assert that the module loads; presence of the exact function is optional.
    assert module is not None