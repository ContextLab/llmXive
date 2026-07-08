import subprocess
import os
from pathlib import Path

def test_ruff_config_valid():
    """Verify that ruff configuration is valid and can be loaded."""
    root = Path(__file__).parent.parent
    ruff_config = root / "pyproject.toml"
    
    if not ruff_config.exists():
        # Fallback to .ruff.toml if pyproject.toml doesn't have [tool.ruff]
        alt_config = root / ".ruff.toml"
        if not alt_config.exists():
            raise FileNotFoundError("No ruff configuration found (pyproject.toml or .ruff.toml)")
    
    # Run ruff check to verify config is valid
    result = subprocess.run(
        ["ruff", "check", "--config", str(ruff_config), "--output-format=json", "."],
        cwd=root,
        capture_output=True,
        text=True
    )
    
    # Config is valid if ruff doesn't fail with a config error
    assert "Failed to parse" not in result.stderr, f"Ruff config error: {result.stderr}"

def test_black_config_valid():
    """Verify that black configuration is valid and can be loaded."""
    root = Path(__file__).parent.parent
    black_config = root / "pyproject.toml"
    
    if not black_config.exists():
        # Fallback to .black.toml
        alt_config = root / ".black.toml"
        if not alt_config.exists():
            raise FileNotFoundError("No black configuration found (pyproject.toml or .black.toml)")
    
    # Run black --check to verify config is valid
    result = subprocess.run(
        ["black", "--config", str(black_config), "--check", "--diff", "."],
        cwd=root,
        capture_output=True,
        text=True
    )
    
    # Config is valid if black doesn't fail with a config error
    assert "Invalid config" not in result.stderr, f"Black config error: {result.stderr}"
    # Note: We don't assert result.returncode == 0 because files might not be formatted yet
    # We only care that the config is valid