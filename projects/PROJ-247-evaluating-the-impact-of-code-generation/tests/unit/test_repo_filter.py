"""
Unit tests for repository filtering logic (T016).

Tests the exclusion of repositories with <5 LLM and <5 Human blocks.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.repo_filter import (
    load_matched_pairs,
    count_blocks_by_repo_and_label,
    identify_excluded_repos,
    filter_matched_pairs,
    save_exclusions_log,
    save_filtered_pairs,
    run_repo_filtering_pipeline,
    MIN_LLM_BLOCKS,
    MIN_HUMAN_BLOCKS
)


class TestCountBlocksByRepoAndLabel:
    """Tests for block counting logic."""

    def test_count_basic(self):
        """Test basic counting of LLM and Human blocks."""
        pairs = [
            {"repo_id": "repo1", "label": "LLM", "block_id": "1"},
            {"repo_id": "repo1", "label": "LLM", "block_id": "2"},
            {"repo_id": "repo1", "label": "HUMAN", "block_id": "3"},
            {"repo_id": "repo2", "label": "HUMAN", "block_id": "4"},
        ]
        
        counts = count_blocks_by_repo_and_label(pairs)
        
        assert counts["repo1"]["LLM"] == 2
        assert counts["repo1"]["HUMAN"] == 1
        assert counts["repo2"]["LLM"] == 0
        assert counts["repo2"]["HUMAN"] == 1

    def test_count_empty(self):
        """Test counting with empty list."""
        counts = count_blocks_by_repo_and_label([])
        assert len(counts) == 0

    def test_count_missing_fields(self):
        """Test handling of missing repo_id or label."""
        pairs = [
            {"label": "LLM", "block_id": "1"},  # Missing repo_id
            {"repo_id": "repo1", "block_id": "2"},  # Missing label
            {"repo_id": "repo1", "label": "INVALID", "block_id": "3"},
            {"repo_id": "repo1", "label": "LLM", "block_id": "4"},
        ]
        
        counts = count_blocks_by_repo_and_label(pairs)
        
        # Only the valid pair should be counted
        assert counts["repo1"]["LLM"] == 1
        assert counts["repo1"]["HUMAN"] == 0


class TestIdentifyExcludedRepos:
    """Tests for repository exclusion logic."""

    def test_exclude_low_llm(self):
        """Test exclusion of repos with too few LLM blocks."""
        repo_counts = {
            "repo1": {"LLM": 3, "HUMAN": 10},  # Too few LLM
            "repo2": {"LLM": 10, "HUMAN": 10},  # OK
            "repo3": {"LLM": 5, "HUMAN": 10},   # Exactly at threshold
        }
        
        excluded = identify_excluded_repos(repo_counts)
        
        assert "repo1" in excluded
        assert "repo2" not in excluded
        assert "repo3" not in excluded

    def test_exclude_low_human(self):
        """Test exclusion of repos with too few Human blocks."""
        repo_counts = {
            "repo1": {"LLM": 10, "HUMAN": 3},  # Too few Human
            "repo2": {"LLM": 10, "HUMAN": 10},  # OK
            "repo3": {"LLM": 10, "HUMAN": 5},   # Exactly at threshold
        }
        
        excluded = identify_excluded_repos(repo_counts)
        
        assert "repo1" in excluded
        assert "repo2" not in excluded
        assert "repo3" not in excluded

    def test_exclude_both_low(self):
        """Test exclusion of repos with both low counts."""
        repo_counts = {
            "repo1": {"LLM": 2, "HUMAN": 2},  # Both too low
            "repo2": {"LLM": 10, "HUMAN": 10},  # OK
        }
        
        excluded = identify_excluded_repos(repo_counts)
        
        assert "repo1" in excluded
        assert "repo2" not in excluded

    def test_exclude_empty_counts(self):
        """Test exclusion of repos with zero counts."""
        repo_counts = {
            "repo1": {"LLM": 0, "HUMAN": 0},
        }
        
        excluded = identify_excluded_repos(repo_counts)
        
        assert "repo1" in excluded


class TestFilterMatchedPairs:
    """Tests for filtering matched pairs."""

    def test_filter_basic(self):
        """Test basic filtering of pairs."""
        pairs = [
            {"repo_id": "repo1", "label": "LLM", "block_id": "1"},
            {"repo_id": "repo1", "label": "HUMAN", "block_id": "2"},
            {"repo_id": "repo2", "label": "LLM", "block_id": "3"},
        ]
        excluded_repos = {"repo1"}
        
        filtered, excluded = filter_matched_pairs(pairs, excluded_repos)
        
        assert len(filtered) == 1
        assert filtered[0]["repo_id"] == "repo2"
        assert len(excluded) == 2
        assert all(p["repo_id"] == "repo1" for p in excluded)

    def test_filter_empty(self):
        """Test filtering with empty excluded set."""
        pairs = [{"repo_id": "repo1", "label": "LLM", "block_id": "1"}]
        
        filtered, excluded = filter_matched_pairs(pairs, set())
        
        assert len(filtered) == 1
        assert len(excluded) == 0

    def test_filter_all_excluded(self):
        """Test filtering where all repos are excluded."""
        pairs = [
            {"repo_id": "repo1", "label": "LLM", "block_id": "1"},
            {"repo_id": "repo2", "label": "HUMAN", "block_id": "2"},
        ]
        excluded_repos = {"repo1", "repo2"}
        
        filtered, excluded = filter_matched_pairs(pairs, excluded_repos)
        
        assert len(filtered) == 0
        assert len(excluded) == 2


class TestSaveAndLoad:
    """Tests for save/load functionality."""

    def test_save_exclusions_log(self):
        """Test saving exclusions log to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exclusions.csv"
            excluded_repos = {"repo1", "repo2"}
            repo_counts = {
                "repo1": {"LLM": 2, "HUMAN": 10},
                "repo2": {"LLM": 10, "HUMAN": 3},
            }
            
            save_exclusions_log(excluded_repos, repo_counts, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            repo_ids = {row["repo_id"] for row in rows}
            assert repo_ids == {"repo1", "repo2"}

    def test_save_filtered_pairs(self):
        """Test saving filtered pairs to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "filtered.csv"
            pairs = [
                {"repo_id": "repo1", "label": "LLM", "block_id": "1"},
                {"repo_id": "repo2", "label": "HUMAN", "block_id": "2"},
            ]
            
            save_filtered_pairs(pairs, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2

    def test_save_empty_pairs(self):
        """Test saving empty pairs list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "filtered.csv"
            
            save_filtered_pairs([], str(output_path))
            
            assert output_path.exists()


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    def test_pipeline_success(self):
        """Test successful pipeline execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "matched_pairs.csv"
            output_path = Path(tmpdir) / "filtered.csv"
            exclusions_path = Path(tmpdir) / "exclusions.csv"
            
            # Create input data
            pairs = [
                # repo1: 6 LLM, 6 HUMAN -> KEEP
                {"repo_id": "repo1", "label": "LLM", "block_id": f"1_{i}"} for i in range(6)
            ] + [
                {"repo_id": "repo1", "label": "HUMAN", "block_id": f"2_{i}"} for i in range(6)
            ] + [
                # repo2: 3 LLM, 10 HUMAN -> EXCLUDE (low LLM)
                {"repo_id": "repo2", "label": "LLM", "block_id": f"3_{i}"} for i in range(3)
            ] + [
                {"repo_id": "repo2", "label": "HUMAN", "block_id": f"4_{i}"} for i in range(10)
            ]
            
            # Write input file
            with open(input_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["repo_id", "label", "block_id"])
                writer.writeheader()
                writer.writerows(pairs)
            
            # Run pipeline
            stats = run_repo_filtering_pipeline(
                str(input_path),
                str(output_path),
                str(exclusions_path)
            )
            
            assert stats["status"] == "success"
            assert stats["total_pairs"] == 25
            assert stats["filtered_pairs"] == 12  # repo1's 12 pairs
            assert stats["excluded_pairs"] == 13  # repo2's 13 pairs
            assert stats["excluded_repos"] == 1
            
            # Verify output file
            assert output_path.exists()
            assert exclusions_path.exists()

    def test_pipeline_empty_input(self):
        """Test pipeline with empty input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "matched_pairs.csv"
            output_path = Path(tmpdir) / "filtered.csv"
            exclusions_path = Path(tmpdir) / "exclusions.csv"
            
            # Create empty input file with headers
            with open(input_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["repo_id", "label", "block_id"])
                writer.writeheader()
            
            stats = run_repo_filtering_pipeline(
                str(input_path),
                str(output_path),
                str(exclusions_path)
            )
            
            assert stats["status"] == "empty_input"
            assert stats["total_pairs"] == 0


class TestConstants:
    """Tests for threshold constants."""

    def test_threshold_values(self):
        """Verify threshold constants are set correctly."""
        assert MIN_LLM_BLOCKS == 5
        assert MIN_HUMAN_BLOCKS == 5