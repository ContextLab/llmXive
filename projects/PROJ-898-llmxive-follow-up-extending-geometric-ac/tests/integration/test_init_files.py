"""
Integration test to verify that the top-level __init__ modules are importable.
"""

import importlib

def test_code_importable():
    """Ensure the `code` package can be imported."""
    importlib.import_module("code")

def test_tests_importable():
    """Ensure the `tests` package can be imported."""
    importlib.import_module("tests")