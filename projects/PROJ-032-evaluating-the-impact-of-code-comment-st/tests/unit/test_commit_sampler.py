import pytest
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils import CommitSampler

class TestCommitSampler:
    def test_sample_commits_correct_count(self):
        """Test that sample_commits returns the correct number of commits."""
        commits = [{"hash": f"commit_{i}"} for i in range(50)]
        sampler = CommitSampler(seed=123)
        result = sampler.sample_commits(commits, n=10)
        assert len(result) == 10

    def test_sample_commits_reproducibility(self):
        """Test that sampling with the same seed yields the same results."""
        commits = [{"hash": f"commit_{i}"} for i in range(50)]
        sampler1 = CommitSampler(seed=42)
        sampler2 = CommitSampler(seed=42)
        
        result1 = sampler1.sample_commits(commits, n=5)
        result2 = sampler2.sample_commits(commits, n=5)
        
        assert result1 == result2

    def test_sample_commits_empty_list(self):
        """Test sampling from an empty list returns empty list."""
        commits = []
        sampler = CommitSampler()
        result = sampler.sample_commits(commits, n=5)
        assert result == []

    def test_sample_commits_n_greater_than_total(self):
        """Test sampling when n > total commits returns all commits."""
        commits = [{"hash": f"commit_{i}"} for i in range(5)]
        sampler = CommitSampler()
        result = sampler.sample_commits(commits, n=10)
        assert len(result) == 5

    def test_sample_commits_n_zero(self):
        """Test sampling with n=0 returns empty list."""
        commits = [{"hash": f"commit_{i}"} for i in range(10)]
        sampler = CommitSampler()
        result = sampler.sample_commits(commits, n=0)
        assert result == []

    def test_sample_commits_unique_items(self):
        """Test that sampled items are unique (no duplicates)."""
        commits = [{"hash": f"commit_{i}"} for i in range(100)]
        sampler = CommitSampler(seed=999)
        result = sampler.sample_commits(commits, n=20)
        hashes = [c["hash"] for c in result]
        assert len(hashes) == len(set(hashes)), "Sampled commits contain duplicates"