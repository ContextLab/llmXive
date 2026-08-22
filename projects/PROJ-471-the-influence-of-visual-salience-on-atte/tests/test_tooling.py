"""
Basic sanity check to ensure linter/formatter tools are installed and 
can be invoked programmatically (simulating the CI check).
"""
import subprocess
import sys
import os

def test_ruff_installed():
    """Verify ruff is available in the environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("Ruff is not installed or not runnable.")

def test_black_installed():
    """Verify black is available in the environment."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("Black is not installed or not runnable.")

def test_pyproject_exists():
    """Verify pyproject.toml exists and contains tool sections."""
    root = Path(__file__).parent.parent
    config_file = root / "pyproject.toml"
    assert config_file.exists(), "pyproject.toml not found at project root."
    
    content = config_file.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])