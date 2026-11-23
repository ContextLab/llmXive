"""
Integration test to verify the project directory structure is correctly set up.
"""
import os
from pathlib import Path

def test_project_root_exists():
    """Verify the project root is accessible."""
    # Assuming tests are in tests/, project root is parent of tests/
    project_root = Path(__file__).parent.parent
    assert project_root.exists(), f"Project root not found at {project_root}"

def test_required_directories_exist():
    """Verify all required directories exist."""
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "code",
        "code/config",
        "code/download",
        "code/preprocess",
        "code/centrality",
        "code/analysis",
        "code/viz",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "outputs",
        "outputs/viz",
        "logs",
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_gitignore_exists():
    """Verify .gitignore file exists."""
    project_root = Path(__file__).parent.parent
    gitignore_path = project_root / ".gitignore"
    assert gitignore_path.exists(), f".gitignore not found at {gitignore_path}"
    
    # Verify it contains expected rules
    with open(gitignore_path, "r") as f:
        content = f.read()
        assert "data/raw" in content, ".gitignore missing data/raw rule"
        assert "outputs" in content, ".gitignore missing outputs rule"
        assert "logs" in content, ".gitignore missing logs rule"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "code" / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_ruff_config_exists():
    """Verify .ruff.toml exists."""
    project_root = Path(__file__).parent.parent
    ruff_path = project_root / "code" / ".ruff.toml"
    assert ruff_path.exists(), f".ruff.toml not found at {ruff_path}"