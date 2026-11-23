"""
Unit test for the idempotent creation of the `tests/` directory.
The test imports the creation function and calls it twice, asserting
that the directory exists and remains writable.
"""

import os
from pathlib import Path

# Import the function from the script we just created.
from code.create_tests_dir import create_and_verify_tests_dir


def test_create_tests_dir_idempotent():
    """
    Verify that calling `create_and_verify_tests_dir` multiple times
    does not raise an exception and leaves the `tests/` directory
    existent and writable.
    """
    # First call – should create the directory.
    create_and_verify_tests_dir()

    # Second call – should be a no‑op (idempotent) and still succeed.
    create_and_verify_tests_dir()

    # Final assertions about the directory's existence and permissions.
    tests_path = Path("tests")
    assert tests_path.is_dir(), "tests/ directory was not created"
    assert os.access(tests_path, os.W_OK), "tests/ directory is not writable"