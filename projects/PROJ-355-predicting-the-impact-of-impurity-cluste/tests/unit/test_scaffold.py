"""
Basic scaffold verification for unit tests.

This test ensures the unit test directory structure is correctly initialized
and that the test runner can discover tests in this package.
"""

def test_unit_directory_exists():
    """Verify that the unit test directory is present."""
    import os
    from pathlib import Path
    
    # Verify the current directory is the unit test directory
    current_dir = Path(__file__).parent
    assert current_dir.name == "unit", "This test must reside in the 'unit' directory"
    assert current_dir.is_dir(), "Unit test directory must exist"
    
    # Verify the parent directory (tests) exists
    assert current_dir.parent.name == "tests", "Parent directory must be 'tests'"
    assert current_dir.parent.is_dir(), "Tests directory must exist"

def test_imports_work():
    """Verify that basic imports required for unit testing work."""
    try:
        import pytest
        import pandas as pd
        import numpy as np
    except ImportError as e:
        pytest.fail(f"Required test dependencies not installed: {e}")
