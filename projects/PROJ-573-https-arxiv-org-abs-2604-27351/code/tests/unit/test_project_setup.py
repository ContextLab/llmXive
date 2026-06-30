"""
Tests for project initialization and structure validation.
"""
import os
import sys
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_project_structure_exists():
    """Verify that the required project directory structure exists."""
    root = Path(__file__).parent.parent.parent
    required_dirs = [
        "src", "tests", "data", "data/processed", "state",
        "contracts", "src/benchmark", "src/models", "src/tasks",
        "src/evaluation", "src/utils", "src/benchmark/config",
        "src/benchmark/config/modalities", "src/research", "src/validators"
    ]
    for d in required_dirs:
        path = root / d
        assert path.exists(), f"Required directory missing: {path}"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and contains Python 3.11 config."""
    root = Path(__file__).parent.parent.parent
    config_path = root / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml not found"
    
    content = config_path.read_text()
    assert "py311" in content, "Python 3.11 target version not configured"
    assert "line-length = 88" in content, "Black line length not configured"

def test_requirements_exists():
    """Verify that requirements.txt exists."""
    root = Path(__file__).parent.parent.parent
    req_path = root / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"

    content = req_path.read_text()
    # Check for key dependencies
    assert "datasets" in content
    assert "pandas" in content
    assert "numpy" in content
    assert "pyyaml" in content

def test_setup_script_exists():
    """Verify that setup_project.py exists and is importable."""
    root = Path(__file__).parent.parent.parent
    setup_path = root / "setup_project.py"
    assert setup_path.exists(), "setup_project.py not found"
    
    # Verify it can be imported
    sys.path.insert(0, str(root))
    try:
        import setup_project
        assert hasattr(setup_project, 'main')
    finally:
        sys.path.remove(str(root))
