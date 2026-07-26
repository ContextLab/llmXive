import subprocess
import sys
from pathlib import Path
import pytest
import tomli

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

def test_black_config_valid(project_root):
    """Verify black configuration is present and valid in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config
    assert "black" in config["tool"]
    assert config["tool"]["black"]["target-version"] == ["py311"]
    assert config["tool"]["black"]["line-length"] == 100

def test_ruff_config_valid(project_root):
    """Verify ruff configuration is present and valid in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config
    assert "ruff" in config["tool"]
    assert config["tool"]["ruff"]["target-version"] == "py311"
    assert config["tool"]["ruff"]["line-length"] == 100

def test_black_check_on_test_file(project_root):
    """Run black check on this test file to ensure formatting compliance."""
    test_file = Path(__file__).relative_to(project_root)
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(test_file)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # If black is not installed, skip (env might not have it yet, but config is valid)
    if result.returncode == 127:
        pytest.skip("black not installed in environment")
    # Return code 0 means OK, 1 means needs formatting. We assert it's 0.
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_ruff_check_on_test_file(project_root):
    """Run ruff check on this test file to ensure linting compliance."""
    test_file = Path(__file__).relative_to(project_root)
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(test_file)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # If ruff is not installed, skip
    if result.returncode == 127:
        pytest.skip("ruff not installed in environment")
    # Return code 0 means OK
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"