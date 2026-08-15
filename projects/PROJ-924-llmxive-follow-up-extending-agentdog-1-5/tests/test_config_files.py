import os
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Assert .ruff.toml exists and is non-empty."""
    root = Path(__file__).resolve().parent.parent
    config_path = root / ".ruff.toml"
    assert config_path.exists(), ".ruff.toml not found"
    assert config_path.stat().st_size > 0, ".ruff.toml is empty"

def test_black_config_exists():
    """Assert pyproject.toml exists, is non-empty, and contains [tool.black]."""
    root = Path(__file__).resolve().parent.parent
    config_path = root / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml not found"
    assert config_path.stat().st_size > 0, "pyproject.toml is empty"
    
    content = config_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"

def test_pyproject_dependencies():
    """Assert pyproject.toml contains required dependencies."""
    root = Path(__file__).resolve().parent.parent
    config_path = root / "pyproject.toml"
    content = config_path.read_text()
    
    required_deps = [
        "sentence-transformers",
        "scikit-learn",
        "pandas",
        "numpy",
        "datasets",
        "jsonschema",
        "statsmodels",
        "pytest",
        "transformers",
        "accelerate"
    ]
    
    for dep in required_deps:
        assert dep in content, f"Missing dependency: {dep}"