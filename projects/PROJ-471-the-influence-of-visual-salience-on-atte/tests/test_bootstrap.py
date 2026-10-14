"""
Unit test for the bootstrap script (T001).

The test runs the bootstrap entry point and then checks that:
* All required directories exist.
* ``code/requirements.txt`` exists and contains the expected pinned
  dependencies (at least the Python version line).
* The ``code/main.py`` layout verification would succeed after bootstrap.
"""
import sys
import importlib
from pathlib import Path

from llmxive_toolkit import paths

# Import the bootstrap module without executing the script's __main__ block
bootstrap = importlib.import_module("code.bootstrap")

def test_bootstrap_creates_layout_and_requirements(tmp_path, monkeypatch):
    """
    Run the bootstrap ``main`` function and verify side‑effects.
    """
    # Ensure a clean temporary directory is used as project root for the test.
    # Monkey‑patch the llmxive_toolkit.paths functions to point inside the temp dir.
    monkeypatch.setattr(paths, "root", Path(tmp_path))
    # Re‑define the shortcut helpers to use the patched root.
    monkeypatch.setattr(paths, "code", lambda *parts: Path(tmp_path, "code", *parts))
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, "data", *parts))
    monkeypatch.setattr(paths, "docs", lambda *parts: Path(tmp_path, "docs", *parts))

    # Run bootstrap
    bootstrap.main()

    # Expected directories
    expected_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("interim"),
        paths.data("processed"),
        paths.data("results"),
        paths.code("tests"),
        paths.docs(),
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} to exist after bootstrap"

    # Check requirements.txt
    req_path = paths.code("requirements.txt")
    assert req_path.is_file(), "requirements.txt should be created in code/"

    # Verify that the file contains at least the Python version line
    content = req_path.read_text()
    assert "python==3.11" in content, "Pinned Python version missing from requirements.txt"

    # Verify that code/main.py would succeed in its layout check
    from code import main as main_module
    # Monkey‑patch logger to avoid noisy output during the test
    monkeypatch.setattr(main_module, "log", type("DummyLog", (), {"error": lambda *a, **kw: None, "info": lambda *a, **kw: None}))
    # The internal verification function should return True after bootstrap
    assert main_module._verify_layout() is True