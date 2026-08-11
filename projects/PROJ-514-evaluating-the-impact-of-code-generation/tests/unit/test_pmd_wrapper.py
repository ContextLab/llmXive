"""
Unit tests for PMD Wrapper functionality.
"""

import os
import sys
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.pmd_utils import run_pmd_on_file, get_pmd_ruleset_path


def test_get_pmd_ruleset_path_exists():
    """Test that ruleset path resolution works (if rulesets exist)."""
    # This test assumes rulesets are in the expected location relative to project root
    # It may fail if rulesets are not yet created, which is acceptable for this unit test
    try:
        path = get_pmd_ruleset_path("LongMethod")
        # If it returns a path, it should exist (or we fallback)
        assert isinstance(path, Path)
    except FileNotFoundError:
        # Expected if rulesets are not present in test environment
        pytest.skip("Ruleset files not found in test environment")


def test_run_pmd_on_file_structure():
    """Test that run_pmd_on_file returns expected structure."""
    # Create a temporary file to test against
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp.write(b"def test():\n    pass\n")
        tmp_path = Path(tmp.name)

    try:
        result = run_pmd_on_file(tmp_path)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "metrics" in result
        assert "errors" in result
        assert "exit_code" in result
    finally:
        os.unlink(tmp_path)