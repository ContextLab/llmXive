"""
Test that the CI workflow file exists and defines a `validate` job.
"""

import pathlib

import pytest


@pytest.fixture
def repo_root():
    """
    Resolve the repository root directory relative to this test file.
    """
    # This test lives in <repo_root>/tests/
    return pathlib.Path(__file__).resolve().parents[1]


def test_ci_workflow_exists(repo_root):
    """
    The CI workflow file must exist at .github/workflows/ci.yml.
    """
    ci_path = repo_root / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), f"CI workflow file not found at {ci_path}"


def test_ci_workflow_contains_validate_job(repo_root):
    """
    The CI workflow must contain a job named `validate`.
    """
    ci_path = repo_root / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), f"CI workflow file not found at {ci_path}"

    content = ci_path.read_text(encoding="utf-8")
    # Look for a top‑level job key named `validate:` (allowing indentation)
    lines = [line.strip() for line in content.splitlines()]
    assert any(line.startswith("validate:") for line in lines), (
        "CI workflow does not define a `validate` job. "
        "Expected a line starting with `validate:` in the jobs section."
    )