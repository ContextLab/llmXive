"""
Tests for verify_constitution.py (T000c).
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code/src to path for imports if not already there
# Assuming tests are run from project root or code root
code_src_path = Path(__file__).parent.parent / "code" / "src"
if str(code_src_path) not in sys.path:
    sys.path.insert(0, str(code_src_path))

from verify_constitution import (
    verify_amendment_marker,
    verify_constitution_update,
    main,
    PROJECT_ROOT,
    CONSTITUTION_PATH,
    AMENDMENT_MARKER_PATH
)

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory structure mimicking the project root."""
    # Create necessary subdirectories
    constitutions_dir = tmp_path / "constitutions"
    constitutions_dir.mkdir()
    return tmp_path

def test_verify_amendment_marker_exists(temp_project_root):
    """Test that verify_amendment_marker returns True when marker exists."""
    # Create the marker file
    marker_file = temp_project_root / "amendment_ratified.md"
    marker_file.write_text("Ratified by human review.\n")

    # Mock the global path variables
    with patch('verify_constitution.AMENDMENT_MARKER_PATH', marker_file):
        result = verify_amendment_marker()
        assert result is True

def test_verify_amendment_marker_missing(temp_project_root):
    """Test that verify_amendment_marker returns False when marker is missing."""
    # Ensure marker file does NOT exist
    marker_file = temp_project_root / "amendment_ratified.md"
    if marker_file.exists():
        marker_file.unlink()

    with patch('verify_constitution.AMENDMENT_MARKER_PATH', marker_file):
        result = verify_amendment_marker()
        assert result is False

def test_verify_constitution_update_missing_file(temp_project_root):
    """Test that verify_constitution_update returns False if file is missing."""
    const_file = temp_project_root / "constitutions" / "FR-030.md"
    # Ensure file does not exist

    with patch('verify_constitution.CONSTITUTION_PATH', const_file):
        result = verify_constitution_update()
        assert result is False

def test_verify_constitution_update_missing_fragments(temp_project_root):
    """Test that verify_constitution_update returns False if required text is missing."""
    const_file = temp_project_root / "constitutions" / "FR-030.md"
    # Write content without the required fragments
    const_file.write_text("Principle VI: Old text with Pearson and McNemar.\n")

    with patch('verify_constitution.CONSTITUTION_PATH', const_file):
        result = verify_constitution_update()
        assert result is False

def test_verify_constitution_update_success(temp_project_root):
    """Test that verify_constitution_update returns True if all fragments are present."""
    const_file = temp_project_root / "constitutions" / "FR-030.md"
    # Write content with all required fragments
    content = """
    # Constitution FR-030

    ## Principle VI
    Statistical analysis must use Point-Biserial correlation and Permutation tests.
    Version: 1.1
    """
    const_file.write_text(content)

    with patch('verify_constitution.CONSTITUTION_PATH', const_file):
        result = verify_constitution_update()
        assert result is True

def test_main_success(temp_project_root):
    """Test that main returns 0 on success."""
    marker_file = temp_project_root / "amendment_ratified.md"
    marker_file.write_text("Ratified.\n")

    const_file = temp_project_root / "constitutions" / "FR-030.md"
    const_file.write_text("Principle VI: Point-Biserial and Permutation.\n")

    with patch('verify_constitution.PROJECT_ROOT', temp_project_root):
        with patch('verify_constitution.AMENDMENT_MARKER_PATH', marker_file):
            with patch('verify_constitution.CONSTITUTION_PATH', const_file):
                result = main()
                assert result == 0

def test_main_failure_marker_missing(temp_project_root):
    """Test that main returns 1 if marker is missing."""
    const_file = temp_project_root / "constitutions" / "FR-030.md"
    const_file.write_text("Principle VI: Point-Biserial and Permutation.\n")

    # Marker file does not exist
    with patch('verify_constitution.PROJECT_ROOT', temp_project_root):
        with patch('verify_constitution.AMENDMENT_MARKER_PATH', temp_project_root / "nonexistent.md"):
            with patch('verify_constitution.CONSTITUTION_PATH', const_file):
                result = main()
                assert result == 1

def test_main_failure_constitution_missing(temp_project_root):
    """Test that main returns 1 if constitution is missing."""
    marker_file = temp_project_root / "amendment_ratified.md"
    marker_file.write_text("Ratified.\n")

    const_file = temp_project_root / "constitutions" / "FR-030.md"
    # File does not exist

    with patch('verify_constitution.PROJECT_ROOT', temp_project_root):
        with patch('verify_constitution.AMENDMENT_MARKER_PATH', marker_file):
            with patch('verify_constitution.CONSTITUTION_PATH', const_file):
                result = main()
                assert result == 1
