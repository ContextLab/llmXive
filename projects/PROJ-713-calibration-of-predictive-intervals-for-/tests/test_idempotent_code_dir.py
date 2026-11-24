"""
Test that the `create_and_verify_code_dir` function is idempotent.
The script should be runnable twice without raising any exceptions,
and the `code/` directory must remain writable after the second call.
"""

import os
import pytest
from pathlib import Path

# Import the function from the project script
from create_code_dir import create_and_verify_code_dir


def test_create_code_dir_idempotent(tmp_path, monkeypatch):
    """
    Run the directory‑creation routine twice and assert that no error is raised.
    The test also checks that the resulting directory is writable.
    """
    # Ensure the working directory is the project root for the script
    project_root = Path(__file__).resolve().parents[2]  # <project>/tests/..
    monkeypatch.chdir(project_root)

    # First invocation – should create the directory
    create_and_verify_code_dir()

    # Second invocation – must be idempotent (no exception)
    create_and_verify_code_dir()

    # Verify that the `code/` directory exists and is writable
    code_dir = Path("code")
    assert code_dir.is_dir(), "code directory was not created"
    assert os.access(code_dir, os.W_OK), "code directory is not writable"


if __name__ == "__main__":
    # When run directly, execute the test manually
    pytest.main([__file__])