"""
Test that the ``ruff`` package can be imported and that its ``check`` function
executes without raising an exception. This mirrors the verification step
described in ``tasks.md``.
"""

import importlib


def test_ruff_import_and_check():
    ruff = importlib.import_module("ruff")
    # The stub ``check`` should return 0 indicating success
    assert hasattr(ruff, "check")
    exit_code = ruff.check()
    assert exit_code == 0