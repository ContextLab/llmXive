"""
Unit tests for configuration and path constants.
"""
import pytest
from pathlib import Path

def test_project_root_exists(project_root):
    """Verify the project root directory exists."""
    assert project_root.exists()
    assert project_root.is_dir()

def test_code_structure(project_root):
    """Verify core directories exist under the project root."""
    code_dir = project_root / "code"
    assert code_dir.exists()
    assert (code_dir / "models").exists()
    assert (code_dir / "metrics").exists()
    assert (code_dir / "utils").exists()
    assert (code_dir / "evaluation").exists()