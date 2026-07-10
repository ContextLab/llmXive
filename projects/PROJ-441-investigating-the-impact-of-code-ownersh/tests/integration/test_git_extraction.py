"""
Integration test for git metrics extraction.

Verifies that the git_metrics module correctly calculates
LOC-weighted Gini coefficient and developer count.
"""

import os
import json
import tempfile
import subprocess
import pytest
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.extractors.git_metrics import (
    extract_repo_metrics,
    calculate_gini_coefficient,
    get_blame_authorship,
    checkout_commit
)
from code.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_repo():
    """Create a temporary git repository with multiple authors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test_repo"
        repo_path.mkdir()
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "alice@example.com"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Alice"], cwd=repo_path, check=True, capture_output=True)
        
        # Create a file
        test_file = repo_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")
        
        # Commit as Alice
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
        
        # Add more lines
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")
        
        # Switch user to Bob
        subprocess.run(["git", "config", "user.email", "bob@example.com"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Bob"], cwd=repo_path, check=True, capture_output=True)
        
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add lines"], cwd=repo_path, check=True, capture_output=True)
        
        # Add more lines
        test_file.write_text("line1\nline2\nline3\nline4\nline5\nline6\nline7\n")
        
        # Switch user to Charlie
        subprocess.run(["git", "config", "user.email", "charlie@example.com"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Charlie"], cwd=repo_path, check=True, capture_output=True)
        
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add more lines"], cwd=repo_path, check=True, capture_output=True)
        
        yield str(repo_path)

def test_gini_coefficient_perfect_equality():
    """Test Gini coefficient with perfect equality (all authors have same lines)."""
    values = [10, 10, 10, 10]
    gini = calculate_gini_coefficient(values)
    # Gini for equal distribution should be 0
    assert abs(gini) < 0.01, f"Expected Gini ~0 for equal distribution, got {gini}"

def test_gini_coefficient_perfect_inequality():
    """Test Gini coefficient with perfect inequality (one author has all lines)."""
    values = [40, 0, 0, 0]
    gini = calculate_gini_coefficient(values)
    # Gini for perfect inequality should be close to 1
    assert gini > 0.9, f"Expected Gini ~1 for perfect inequality, got {gini}"

def test_git_blame_extraction(sample_repo):
    """Test that git blame correctly attributes lines to authors."""
    metrics = extract_repo_metrics(sample_repo)
    
    assert "error" not in metrics, f"Extraction failed: {metrics.get('error')}"
    assert metrics["developer_count"] == 3, f"Expected 3 developers, got {metrics['developer_count']}"
    assert metrics["gini_coefficient"] is not None
    assert 0 <= metrics["gini_coefficient"] <= 1

def test_commit_checkout(sample_repo):
    """Test checking out a specific commit."""
    # Get the first commit
    result = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=sample_repo,
        capture_output=True,
        text=True,
        check=True
    )
    first_commit = result.stdout.strip()
    
    success = checkout_commit(sample_repo, first_commit)
    assert success, "Failed to checkout commit"
    
    # Verify we are on the correct commit
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=sample_repo,
        capture_output=True,
        text=True,
        check=True
    )
    assert result.stdout.strip() == first_commit, "Commit did not match"

def test_output_json_structure(sample_repo):
    """Test that output JSON contains required fields."""
    metrics = extract_repo_metrics(sample_repo)
    
    required_fields = [
        "repository",
        "target_commit",
        "files_analyzed",
        "total_lines",
        "gini_coefficient",
        "developer_count",
        "author_distribution"
    ]
    
    for field in required_fields:
        assert field in metrics, f"Missing required field: {field}"
    
    # Verify types
    assert isinstance(metrics["gini_coefficient"], (int, float))
    assert isinstance(metrics["developer_count"], int)
    assert isinstance(metrics["author_distribution"], dict)

def test_empty_repository(tmp_path):
    """Test handling of a repository with no commits."""
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    subprocess.run(["git", "init"], cwd=empty_repo, check=True, capture_output=True)
    
    metrics = extract_repo_metrics(str(empty_repo))
    
    assert "error" in metrics or metrics["developer_count"] is None

def test_nonexistent_file(sample_repo):
    """Test handling of a non-existent file."""
    # This should be handled gracefully in extract_file_metrics
    # but extract_repo_metrics filters by file patterns
    metrics = extract_repo_metrics(sample_repo, file_patterns=["*.nonexistent"])
    
    assert "error" in metrics or metrics["files_analyzed"] == 0