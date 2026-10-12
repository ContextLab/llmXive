"""
Unit test for scaffold splitting leakage prevention.

The test simply checks that the scaffold_split module is importable and
provides a callable named ``scaffold_split``. Full functional verification
is performed in integration tests; this unit test guards against missing
symbols which caused earlier import errors.
"""

import importlib
import pytest

def test_scaffold_split_callable():
    module = importlib.import_module("code.scaffold_split")
    assert hasattr(module, "scaffold_split")
    func = getattr(module, "scaffold_split")
    assert callable(func)
