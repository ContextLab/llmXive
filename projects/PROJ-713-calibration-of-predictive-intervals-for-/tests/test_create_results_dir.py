"""Test that the results directory is created idempotently and is writable."""

import os
from pathlib import Path

# Import the function from the script we just created.
from code.create_results_dir import create_and_verify_results_dir


def test_create_results_dir_idempotent(tmp_path, monkeypatch):
    """
    The test runs the directory‑creation function twice and asserts that:
    1. No exception is raised on the second call.
    2. The directory exists.
    3. The directory is writable.
    """
    # Change the working directory to a temporary directory so we do not affect
    # the real project layout during the test run.
    monkeypatch.chdir(tmp_path)

    # First call – should create the directory.
    first_path = create_and_verify_results_dir()
    assert first_path == tmp_path / "results"
    assert first_path.is_dir()
    assert os.access(first_path, os.W_OK)

    # Second call – should be a no‑op but still succeed.
    second_path = create_and_verify_results_dir()
    assert second_path == first_path
    assert second_path.is_dir()
    assert os.access(second_path, os.W_OK)