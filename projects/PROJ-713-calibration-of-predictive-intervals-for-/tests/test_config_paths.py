"""
test_config_paths.py
--------------------
Unit test for the configuration verification script introduced in task T001f.
The test simply imports the ``verify_config`` function and calls it; any
exception will cause the test to fail.
"""

import pytest
from code.verify_config import verify_config

def test_verify_config_runs_without_error(tmp_path, monkeypatch):
    """
    Ensure that ``verify_config`` completes without raising.
    The test runs in an isolated temporary directory to avoid side effects.
    """
    # Monkey‑patch the llmxive_toolkit.paths.path function so that it resolves
    # relative to the temporary directory created by pytest.
    from llmxive_toolkit import paths as toolkit_paths

    def fake_path(rel: str):
        # Resolve inside the temporary directory.
        return tmp_path / rel

    monkeypatch.setattr(toolkit_paths, "path", fake_path)

    # Run the verification – any exception will be caught by pytest.
    verify_config()