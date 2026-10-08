"""
Contract Test for T099c: Performance Documentation Alignment.

Verifies that the check_performance_phrase.py script correctly identifies
the presence or absence of the target phrase in documentation files.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def check_script_path(project_root):
    """Get the path to the check_performance_phrase.py script."""
    return project_root / "code" / "check_performance_phrase.py"


def test_script_exists(check_script_path):
    """Verify the check script exists."""
    assert check_script_path.exists(), "check_performance_phrase.py should exist"


def test_script_runs_successfully_when_phrase_present(check_script_path, project_root, tmp_path):
    """
    Test that the script exits 0 when the phrase is present in both files.
    """
    # Create temporary copies of plan.md and README.md with the phrase
    temp_plan = tmp_path / "plan.md"
    temp_readme = tmp_path / "README.md"

    content_with_phrase = f"""
    # Test Document

    This document states that the pipeline takes ≤ 6 hours to run.
    """

    temp_plan.write_text(content_with_phrase)
    temp_readme.write_text(content_with_phrase)

    # Temporarily move original files if they exist
    original_plan = project_root / "plan.md"
    original_readme = project_root / "README.md"

    plan_backup = None
    readme_backup = None

    if original_plan.exists():
        plan_backup = tmp_path / "plan.md.bak"
        original_plan.rename(plan_backup)

    if original_readme.exists():
        readme_backup = tmp_path / "README.md.bak"
        original_readme.rename(readme_backup)

    try:
        # Copy temp files to project root
        temp_plan.rename(original_plan)
        temp_readme.rename(original_readme)

        # Run the script
        result = subprocess.run(
            [sys.executable, str(check_script_path)],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Script should exit 0 when phrase is present. Output: {result.stdout}, Error: {result.stderr}"
        assert "All documentation files contain" in result.stdout

    finally:
        # Restore original files
        if plan_backup:
            if original_plan.exists():
                original_plan.unlink()
            plan_backup.rename(original_plan)
        if readme_backup:
            if original_readme.exists():
                original_readme.unlink()
            readme_backup.rename(original_readme)


def test_script_fails_when_phrase_missing(check_script_path, project_root, tmp_path):
    """
    Test that the script exits 1 when the phrase is missing from at least one file.
    """
    # Create temporary files WITHOUT the phrase
    temp_plan = tmp_path / "plan.md"
    temp_readme = tmp_path / "README.md"

    content_without_phrase = """
    # Test Document

    This document does not contain the required performance phrase.
    """

    temp_plan.write_text(content_without_phrase)
    temp_readme.write_text(content_without_phrase)

    # Temporarily move original files if they exist
    original_plan = project_root / "plan.md"
    original_readme = project_root / "README.md"

    plan_backup = None
    readme_backup = None

    if original_plan.exists():
        plan_backup = tmp_path / "plan.md.bak"
        original_plan.rename(plan_backup)

    if original_readme.exists():
        readme_backup = tmp_path / "README.md.bak"
        original_readme.rename(readme_backup)

    try:
        # Copy temp files to project root
        temp_plan.rename(original_plan)
        temp_readme.rename(original_readme)

        # Run the script
        result = subprocess.run(
            [sys.executable, str(check_script_path)],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 1, f"Script should exit 1 when phrase is missing. Output: {result.stdout}, Error: {result.stderr}"
        assert "FAILURE" in result.stdout

    finally:
        # Restore original files
        if plan_backup:
            if original_plan.exists():
                original_plan.unlink()
            plan_backup.rename(original_plan)
        if readme_backup:
            if original_readme.exists():
                original_readme.unlink()
            readme_backup.rename(original_readme)