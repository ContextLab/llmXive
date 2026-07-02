"""
Unit tests for T016: acquisition_stats.py
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We assume the test runner is invoked from the project root or code/ directory
# Adjust import path if necessary based on how tests are run
import sys
# Add parent directory to path if running from tests/unit
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# We need to mock the utils module if it's not fully set up in test environment
# But for this task, we focus on the logic of acquisition_stats
# Since acquisition_stats imports from utils, we must ensure utils is importable
# or mock the specific import.
# For this test, we assume utils.py is available as per project structure.

try:
    from acquisition_stats import count_valid_repos, calculate_success_rate, estimate_excluded_count
except ImportError:
    # Fallback if running in a specific environment where imports differ
    import importlib.util
    spec = importlib.util.spec_from_file_location("acquisition_stats", parent_dir / "code" / "acquisition_stats.py")
    acquisition_stats = importlib.util.module_from_spec(spec)
    # We can't easily load it without resolving all dependencies in a simple test block
    # So we will test the pure logic functions if we can import them, 
    # or skip if the environment isn't ready.
    # For the purpose of this artifact, we assume the environment allows importing.
    pass

def test_count_valid_repos_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir)
        result = count_valid_repos(raw_dir)
        assert result == 0

def test_count_valid_repos_with_git():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir)
        # Create a fake git repo
        repo1 = raw_dir / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()
        
        # Create a non-repo directory
        repo2 = raw_dir / "repo2"
        repo2.mkdir()
        
        result = count_valid_repos(raw_dir)
        assert result == 1

def test_count_valid_repos_with_bare():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir)
        # Create a fake bare repo
        repo1 = raw_dir / "repo1"
        repo1.mkdir()
        (repo1 / "HEAD").write_text("ref: refs/heads/main")
        (repo1 / "refs").mkdir()
        
        result = count_valid_repos(raw_dir)
        assert result == 1

def test_calculate_success_rate():
    assert calculate_success_rate(500, 500) == 100.0
    assert calculate_success_rate(250, 500) == 50.0
    assert calculate_success_rate(0, 500) == 0.0
    assert calculate_success_rate(500, 0) == 0.0 # Division by zero handled

def test_estimate_excluded_count():
    assert estimate_excluded_count(500, 400) == 100
    assert estimate_excluded_count(500, 500) == 0
    assert estimate_excluded_count(500, 600) == 0 # Should not be negative