"""
Tests for the project skeleton and dependency lock.

Verifies that the required files exist and contain the expected
command for running the full pipeline.
"""

import pathlib


def _project_root() -> pathlib.Path:
    """
    Returns the absolute path to the project root directory,
    two levels up from this test file (tests/ -> project root).
    """
    return pathlib.Path(__file__).resolve().parents[2]


def test_requirements_txt_exists():
    """Check that the pinned requirements file is present."""
    req_path = _project_root() / "requirements.txt"
    assert req_path.is_file(), f"requirements.txt not found at {req_path}"


def test_quickstart_contains_run_command():
    """Ensure the quickstart guide includes the full‑run command."""
    qs_path = _project_root() / "docs" / "quickstart.md"
    assert qs_path.is_file(), f"quickstart.md not found at {qs_path}"
    content = qs_path.read_text(encoding="utf-8")
    expected_cmd = "python code/main.py --full-run"
    assert expected_cmd in content, (
        f"Expected command '{expected_cmd}' not found in quickstart.md"
    )


def test_code_package_is_importable():
    """Import the top‑level `code` package to confirm it is a valid module."""
    import importlib
    import sys

    root = _project_root()
    sys.path.insert(0, str(root))
    try:
        module = importlib.import_module("code")
        assert hasattr(module, "main"), "code package should expose a main() function"
    finally:
        sys.path.pop(0)