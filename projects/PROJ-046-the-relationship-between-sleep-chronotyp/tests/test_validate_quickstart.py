"""
Unit tests for quickstart validation script.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code.utils_logging import get_project_root
from code.code_06_validate_quickstart import (
    check_file_exists,
    check_dir_exists,
    check_r_installed,
    check_renv_initialized,
    check_logging_infrastructure,
    validate_quickstart_content,
    run_quickstart_validation
)


@pytest.fixture
def temp_project():
    """Create a temporary project directory structure."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)

    # Create standard directory structure
    (project_root / "data").mkdir()
    (project_root / "data" / "raw").mkdir()
    (project_root / "data" / "processed").mkdir()
    (project_root / "data" / "derived").mkdir()
    (project_root / "code").mkdir()
    (project_root / "logs").mkdir()
    (project_root / "reports").mkdir()

    # Create a minimal quickstart.md
    quickstart_content = """
    # Quickstart Guide

    ## Setup
    Install R 4.3+ and run renv::init().

    ## Data Requirements
    Provide a merged CSV with required columns.

    ## Run Commands
    Rscript code/01_ingest.R

    ## Data Source Note
    This pipeline requires user-provided real data.
    """
    (project_root / "quickstart.md").write_text(quickstart_content)

    yield project_root

    # Cleanup
    shutil.rmtree(temp_dir)


def test_check_file_exists_found(temp_project):
    """Test that check_file_exists returns True for existing file."""
    passed, msg = check_file_exists(temp_project / "quickstart.md", "Test file")
    assert passed is True
    assert "✓" in msg


def test_check_file_exists_missing(temp_project):
    """Test that check_file_exists returns False for missing file."""
    passed, msg = check_file_exists(temp_project / "nonexistent.txt", "Test file")
    assert passed is False
    assert "✗" in msg


def test_check_dir_exists_found(temp_project):
    """Test that check_dir_exists returns True for existing directory."""
    passed, msg = check_dir_exists(temp_project / "code", "Test dir")
    assert passed is True
    assert "✓" in msg


def test_check_dir_exists_missing(temp_project):
    """Test that check_dir_exists returns False for missing directory."""
    passed, msg = check_dir_exists(temp_project / "nonexistent", "Test dir")
    assert passed is False
    assert "✗" in msg


def test_check_r_installed():
    """Test R installation check (may pass or fail depending on environment)."""
    passed, msg = check_r_installed()
    # Just verify it returns a tuple of (bool, str)
    assert isinstance(passed, bool)
    assert isinstance(msg, str)


def test_check_renv_initialized(temp_project):
    """Test renv initialization check."""
    # Without renv.lock
    passed, msg = check_renv_initialized(temp_project)
    assert passed is False

    # With renv.lock
    (temp_project / "renv.lock").write_text("{}")
    passed, msg = check_renv_initialized(temp_project)
    assert passed is True


def test_validate_quickstart_content_missing_sections(temp_project):
    """Test validation with missing required sections."""
    # Create a minimal quickstart without sections
    (temp_project / "quickstart.md").write_text("# Just a title")

    results = validate_quickstart_content(temp_project)
    # Should have failures for missing sections
    failures = [r for r in results if not r[0]]
    assert len(failures) > 0


def test_validate_quickstart_content_complete(temp_project):
    """Test validation with complete quickstart.md."""
    results = validate_quickstart_content(temp_project)
    # Check that file existence passed
    file_check = [r for r in results if "quickstart.md exists" in r[1]]
    assert len(file_check) == 1
    assert file_check[0][0] is True


def test_run_quickstart_validation(temp_project):
    """Test the full validation run."""
    success, messages = run_quickstart_validation(temp_project)
    assert isinstance(success, bool)
    assert isinstance(messages, list)
    assert len(messages) > 0