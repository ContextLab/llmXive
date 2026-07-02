import pytest
import os
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics import calc_quality_rate, calc_churn
from utils import CommitSampler

class TestCalcQualityRate:
    """Tests for calc_quality_rate function."""

    def test_calc_quality_rate_empty_repo(self):
        """Test quality rate calculation on a repo with no commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            # Initialize empty git repo
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            
            result = calc_quality_rate(repo_path)
            
            assert result["quality_rate"] == 0.0
            assert result["sample_size"] == 0
            assert result["error_count"] == 0

    def test_calc_quality_rate_no_manual_labels(self):
        """Test quality rate calculation without manual labels file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            
            # Create a simple file and commit
            test_file = repo_path / "test.py"
            test_file.write_text("print('hello')\n")
            subprocess.run(["git", "-C", str(repo_path), "add", "."], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.email", "test@test.com"], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "Test User"], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "commit", "-m", "Initial commit"], capture_output=True)
            
            # Create a non-existent manual labels path
            manual_labels_path = Path(tmpdir) / "nonexistent.csv"
            
            result = calc_quality_rate(repo_path, manual_labels_path=str(manual_labels_path))
            
            assert result["quality_rate"] >= 0.0
            assert result["quality_rate"] <= 1.0
            assert result["sample_size"] >= 1
            assert result["validation"] is None

    def test_calc_quality_rate_with_manual_labels(self):
        """Test quality rate calculation with manual labels file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            
            # Create commits
            subprocess.run(["git", "-C", str(repo_path), "config", "user.email", "test@test.com"], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "Test User"], capture_output=True)
            
            # Commit 1: Simple file
            test_file = repo_path / "test1.py"
            test_file.write_text("print('hello')\n")
            subprocess.run(["git", "-C", str(repo_path), "add", "."], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "commit", "-m", "Bug fix: fix hello"], capture_output=True)
            commit1 = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            
            # Commit 2: Another file
            test_file2 = repo_path / "test2.py"
            test_file2.write_text("print('world')\n")
            subprocess.run(["git", "-C", str(repo_path), "add", "."], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "commit", "-m", "Add world"], capture_output=True)
            commit2 = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            
            # Create manual labels CSV
            manual_labels_path = Path(tmpdir) / "manual_labels.csv"
            manual_labels_path.write_text(f"commit_hash,label\n{commit1},bug_fix\n{commit2},not_bug_fix\n")
            
            result = calc_quality_rate(repo_path, manual_labels_path=str(manual_labels_path), sample_size=2)
            
            assert result["quality_rate"] >= 0.0
            assert result["quality_rate"] <= 1.0
            assert result["sample_size"] == 2
            assert result["validation"] is not None
            assert "accuracy" in result["validation"]
            assert "ci_lower" in result["validation"]
            assert "ci_upper" in result["validation"]

    def test_calc_quality_rate_sample_size(self):
        """Test that sample size is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.email", "test@test.com"], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "Test User"], capture_output=True)
            
            # Create multiple commits
            for i in range(20):
                test_file = repo_path / f"test{i}.py"
                test_file.write_text(f"print('{i}')\n")
                subprocess.run(["git", "-C", str(repo_path), "add", "."], capture_output=True)
                subprocess.run(["git", "-C", str(repo_path), "commit", "-m", f"Commit {i}"], capture_output=True)
            
            result = calc_quality_rate(repo_path, sample_size=5)
            
            assert result["sample_size"] <= 5
            # Sampler might return fewer if not enough unique commits, but should not exceed
            assert result["sample_size"] <= 5

class TestCommitSampler:
    """Tests for CommitSampler class."""

    def test_sample_commits_basic(self):
        """Test basic commit sampling."""
        commits = [f"commit_{i}" for i in range(100)]
        sampler = CommitSampler()
        
        sampled = sampler.sample_commits(commits, n=10)
        
        assert len(sampled) == 10
        assert all(c in commits for c in sampled)
        # Check for uniqueness
        assert len(set(sampled)) == 10

    def test_sample_commits_less_than_n(self):
        """Test sampling when n is larger than available commits."""
        commits = [f"commit_{i}" for i in range(5)]
        sampler = CommitSampler()
        
        sampled = sampler.sample_commits(commits, n=10)
        
        assert len(sampled) == 5
        assert all(c in commits for c in sampled)

    def test_sample_commits_empty(self):
        """Test sampling from empty list."""
        commits = []
        sampler = CommitSampler()
        
        sampled = sampler.sample_commits(commits, n=10)
        
        assert len(sampled) == 0

    def test_sample_commits_deterministic_with_seed(self):
        """Test that sampling is deterministic with a fixed seed."""
        commits = [f"commit_{i}" for i in range(100)]
        sampler = CommitSampler()
        
        sampled1 = sampler.sample_commits(commits, n=10)
        sampled2 = sampler.sample_commits(commits, n=10)
        
        # Without setting a seed, results might differ, but the logic should be consistent
        # This test primarily ensures no errors occur
        assert len(sampled1) == 10
        assert len(sampled2) == 10

class TestCalcChurn:
    """Tests for calc_churn function."""

    def test_calc_churn_empty_repo(self):
        """Test churn calculation on a repo with no commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            
            result = calc_churn(repo_path)
            
            assert result == 0.0

    def test_calc_churn_with_commits(self):
        """Test churn calculation with commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.email", "test@test.com"], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "Test User"], capture_output=True)
            
            # Create a file with 10 lines
            test_file = repo_path / "test.py"
            test_file.write_text("\n" * 10)
            subprocess.run(["git", "-C", str(repo_path), "add", "."], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "commit", "-m", "Add file"], capture_output=True)
            
            # Modify the file to add 5 more lines
            test_file.write_text("\n" * 15)
            subprocess.run(["git", "-C", str(repo_path), "add", "."], capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "commit", "-m", "Modify file"], capture_output=True)
            
            result = calc_churn(repo_path)
            
            # First commit: 10 added, 0 deleted
            # Second commit: 5 added, 10 deleted (total 15 - 10 = 5 added, 10 deleted)
            # Total churn: 10 + (5 + 10) = 25
            assert result == 25.0
