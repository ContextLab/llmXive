"""
Tests for ``code/bootstrap.py``.
The test runs the bootstrap script in an isolated temporary directory and
checks that the expected folder structure and ``requirements.txt`` are
created.
"""

import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def temp_cwd(tmp_path, monkeypatch):
    """Change the current working directory to a temporary folder."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def load_bootstrap_module():
    """Dynamically import ``bootstrap.py`` without side‑effects."""
    spec = importlib.util.spec_from_file_location(
        "bootstrap", Path("code/bootstrap.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap"] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_bootstrap_creates_structure_and_requirements(temp_cwd):
    # Import after the cwd has been changed so relative paths resolve correctly.
    bootstrap = load_bootstrap_module()

    # Run the main function (it will call sys.exit; capture the SystemExit).
    with pytest.raises(SystemExit) as excinfo:
        bootstrap.main()
    assert excinfo.value.code == 0

    # Expected directories
    expected_dirs = [
        Path("code"),
        Path("data/raw"),
        Path("data/interim"),
        Path("data/processed"),
        Path("data/results"),
        Path("code/tests"),
        Path("docs"),
    ]
    for d in expected_dirs:
        assert (temp_cwd / d).is_dir(), f"Directory {d} was not created"

    # Check that the requirements file exists and contains a known package.
    req_path = temp_cwd / "requirements.txt"
    assert req_path.is_file(), "requirements.txt was not created"
    content = req_path.read_text()
    assert "torch==" in content, "Pinned torch version missing"
    assert "python==3.11" in content, "Python version pin missing"