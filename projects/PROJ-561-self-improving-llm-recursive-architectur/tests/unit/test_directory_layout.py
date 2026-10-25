"""
Unit test to verify that the project directory layout required by T001 exists.
"""
import os
import pytest

def test_layout_exists():
    required_dirs = [
        "code/tests/unit",
        "data/raw",
        "results",
        "state"
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Directory missing: {d}"
    # Verify that __init__.py files were created in each package directory
    init_paths = [
        "code/__init__.py",
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py"
    ]
    for p in init_paths:
        assert os.path.isfile(p), f"Missing __init__.py: {p}"