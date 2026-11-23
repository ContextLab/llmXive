import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_lint_files_present():
    """Verify that ruff and black configuration files exist in the project root."""
    ruff_config = PROJECT_ROOT / ".ruff.toml"
    pyproject_config = PROJECT_ROOT / "pyproject.toml"

    assert ruff_config.exists(), f"Ruff config missing: {ruff_config}"
    assert pyproject_config.exists(), f"Pyproject config missing: {pyproject_config}"

    # Verify content is not empty
    assert ruff_config.stat().st_size > 0, "Ruff config is empty"
    assert pyproject_config.stat().st_size > 0, "Pyproject config is empty"

    # Verify specific sections exist in content
    ruff_content = ruff_config.read_text()
    assert "[lint]" in ruff_content or "select" in ruff_content, "Ruff config missing [lint] section"

    pyproject_content = pyproject_config.read_text()
    assert "[tool.black]" in pyproject_content, "Pyproject missing [tool.black] section"
    assert "[tool.ruff]" in pyproject_content, "Pyproject missing [tool.ruff] section"