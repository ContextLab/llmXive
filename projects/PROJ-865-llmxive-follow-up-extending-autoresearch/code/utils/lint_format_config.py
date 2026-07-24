"""
Configuration for linting (Ruff) and formatting (Black) tools.
This file is referenced by T003 to ensure configuration exists.
"""
import os
from pathlib import Path

def ensure_ruff_config(project_root: Path) -> Path:
    """
    Creates or updates .ruff.toml in the project root if it doesn't exist.
    """
    config_path = project_root / ".ruff.toml"
    if config_path.exists():
        return config_path

    config_content = """
    [lint]
    select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "PIE", "RET", "SIM"]
    ignore = []

    [lint.per-file-ignores]
    "tests/*" = ["S101"]  # Allow asserts in tests

    [format]
    quote-style = "double"
    indent-style = "space"
    skip-magic-trailing-comma = false
    line-ending = "auto"
    """
    config_path.write_text(config_content.strip())
    return config_path

def ensure_black_config(project_root: Path) -> Path:
    """
    Creates or updates pyproject.toml with Black configuration if missing.
    """
    config_path = project_root / "pyproject.toml"
    
    # Check if [tool.black] section exists
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" in content:
            return config_path
    
    # Read existing or create new
    if config_path.exists():
        content = config_path.read_text()
    else:
        content = ""

    black_section = """

    [tool.black]
    line-length = 88
    target-version = ['py39']
    """
    
    if "[tool.black]" not in content:
        content += black_section
        config_path.write_text(content)
    
    return config_path
