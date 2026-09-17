import os
import pytest
from pathlib import Path

# Helper to resolve the project root relative to the test file
# The tests are in projects/PROJ-924-.../tests/
# The config files are in the project root (same level as tests/)
def get_project_root():
    # Assume tests/ is a direct child of the project root
    return Path(__file__).resolve().parent.parent

def test_ruff_config_exists():
    """Verify that .ruff.toml exists and is non-empty."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    
    assert config_path.exists(), f"File not found: {config_path}"
    assert config_path.stat().st_size > 0, f"File is empty: {config_path}"

def test_pyproject_config_exists():
    """Verify that pyproject.toml exists and is non-empty."""
    root = get_project_root()
    config_path = root / "pyproject.toml"
    
    assert config_path.exists(), f"File not found: {config_path}"
    assert config_path.stat().st_size > 0, f"File is empty: {config_path}"

if __name__ == "__main__":
    # Allow running directly with python -m pytest or python test_config_files.py
    pytest.main([__file__, "-v"])