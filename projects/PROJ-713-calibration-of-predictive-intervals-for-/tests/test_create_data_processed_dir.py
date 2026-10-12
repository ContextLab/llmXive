"""
Unit test for ``code/create_data_processed_dir.py``.

The test calls the creation function twice to verify idempotency and
ensures no exception is raised and that the directory remains writable.
"""

import pytest

from code.create_data_processed_dir import create_and_verify_data_processed_dir

def test_idempotent_creation():
    """
    Run the directory‑creation routine twice; both calls must succeed
    without raising an exception and the resulting path must be writable.
    """
    # First invocation – should create the directory.
    path1 = create_and_verify_data_processed_dir()
    # Second invocation – should be a no‑op and still succeed.
    path2 = create_and_verify_data_processed_dir()

    # The returned Path objects should be identical.
    assert path1 == path2, "Returned paths differ between invocations"

    # Verify that the directory is indeed writable.
    # Attempt to create and delete a temporary file within the directory.
    test_file = path1 / ".tmp_write_test"
    try:
        with open(test_file, "w") as f:
            f.write("test")
    finally:
        if test_file.exists():
            test_file.unlink()