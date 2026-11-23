"""Unit tests for the project-level .gitignore (T002).

Verifies that data/raw/, data/processed/, data/artifacts/ contents,
compiled artifacts, and Python caches are all excluded by ignore rules.
"""
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = PROJECT_ROOT / ".gitignore"


def _git_check_ignore(path: str) -> str:
    """Run `git check-ignore -v <path>` from the project root."""
    result = subprocess.run(
        ["git", "check-ignore", "-v", path],
          cwd=str(PROJECT_ROOT),
          capture_output=True,
          text=True,
      )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def test_gitignore_exists():
    assert GITIGNORE.exists(), ".gitignore must exist at the project root"
    content = GITIGNORE.read_text()
    assert "data/raw" in content
    assert "data/processed" in content
    assert "data/artifacts" in content


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/some_model.nc",
        "data/processed/standardized_model.parquet",
        "data/artifacts/mode_1.png",
    ],
)
def test_data_directories_ignored(path):
    out = _git_check_ignore(path)
    assert out, f"expected {path} to be ignored by a .gitignore rule"


@pytest.mark.parametrize(
    "path",
    [
        "code/__pycache__/config.cpython-311.pyc",
        "code/config.cpython-311.pyc",
        "code/native.so",
    ],
)
def test_compiled_artifacts_and_caches_ignored(path):
    out = _git_check_ignore(path)
    assert out, f"expected {path} to be ignored by a .gitignore rule"