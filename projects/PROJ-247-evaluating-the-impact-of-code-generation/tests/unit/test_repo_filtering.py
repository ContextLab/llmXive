"""
Unit tests for T016 repository filtering logic.

Tests:
- Counting blocks by repo and label
- Identifying excluded repos
- Filtering matched pairs
- Saving exclusions log and filtered pairs
"""
import pytest
import csv
import json
from pathlib import Path
import tempfile
import shutil

from utils.repo_filter import (
    load_matched_pairs,
    count_blocks_by_repo_and_label,
    identify_excluded_repos,
    filter_matched_pairs,
    save_exclusions_log,
    save_filtered_pairs,
    run_repo_filtering_pipeline
)
from utils.models import MatchedPair


class TestCountBlocksByRepoAndLabel:
    """Tests for count_blocks_by_repo_and_label function."""
    
    def test_count_blocks_single_repo(self):
        """Test counting blocks for a single repository."""
        pairs = [
            MatchedPair(llm_block_id="llm1", human_block_id="human1", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m1"),
            MatchedPair(llm_block_id="llm2", human_block_id="human2", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m2"),
        ]
        
        counts = count_blocks_by_repo_and_label(pairs)
        
        assert "repo1" in counts
        assert counts["repo1"]["llm"] == 2
        assert counts["repo1"]["human"] == 2
    
    def test_count_blocks_multiple_repos(self):
        """Test counting blocks for multiple repositories."""
        pairs = [
            MatchedPair(llm_block_id="llm1", human_block_id="human1", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m1"),
            MatchedPair(llm_block_id="llm2", human_block_id="human2", repo_name="repo2", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m2"),
            MatchedPair(llm_block_id="llm3", human_block_id="human3", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m3"),
        ]
        
        counts = count_blocks_by_repo_and_label(pairs)
        
        assert "repo1" in counts
        assert "repo2" in counts
        assert counts["repo1"]["llm"] == 2
        assert counts["repo1"]["human"] == 2
        assert counts["repo2"]["llm"] == 1
        assert counts["repo2"]["human"] == 1
    
    def test_count_blocks_empty_list(self):
        """Test counting blocks for an empty list."""
        pairs = []
        counts = count_blocks_by_repo_and_label(pairs)
        assert counts == {}

class TestIdentifyExcludedRepos:
    """Tests for identify_excluded_repos function."""
    
    def test_identify_excluded_repos_below_threshold(self):
        """Test identifying repos below threshold."""
        repo_counts = {
            "repo1": {"llm": 3, "human": 5},  # <5 LLM
            "repo2": {"llm": 5, "human": 3},  # <5 Human
            "repo3": {"llm": 5, "human": 5},  # Meets criteria
            "repo4": {"llm": 2, "human": 2},  # Both below
        }
        
        excluded = identify_excluded_repos(repo_counts, min_llm_blocks=5, min_human_blocks=5)
        
        assert "repo1" in excluded
        assert "repo2" in excluded
        assert "repo4" in excluded
        assert "repo3" not in excluded
    
    def test_identify_excluded_repos_empty(self):
        """Test with no excluded repos."""
        repo_counts = {
            "repo1": {"llm": 10, "human": 10},
            "repo2": {"llm": 8, "human": 7},
        }
        
        excluded = identify_excluded_repos(repo_counts, min_llm_blocks=5, min_human_blocks=5)
        assert excluded == set()
    
    def test_identify_excluded_repos_all_excluded(self):
        """Test when all repos are excluded."""
        repo_counts = {
            "repo1": {"llm": 2, "human": 2},
            "repo2": {"llm": 1, "human": 1},
        }
        
        excluded = identify_excluded_repos(repo_counts, min_llm_blocks=5, min_human_blocks=5)
        assert excluded == {"repo1", "repo2"}

class TestFilterMatchedPairs:
    """Tests for filter_matched_pairs function."""
    
    def test_filter_matched_pairs(self):
        """Test filtering out excluded repos."""
        pairs = [
            MatchedPair(llm_block_id="llm1", human_block_id="human1", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m1"),
            MatchedPair(llm_block_id="llm2", human_block_id="human2", repo_name="repo2", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m2"),
            MatchedPair(llm_block_id="llm3", human_block_id="human3", repo_name="repo3", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m3"),
        ]
        
        excluded_repos = {"repo2"}
        filtered = filter_matched_pairs(pairs, excluded_repos)
        
        assert len(filtered) == 2
        assert all(p.repo_name != "repo2" for p in filtered)
    
    def test_filter_matched_pairs_all_excluded(self):
        """Test when all repos are excluded."""
        pairs = [
            MatchedPair(llm_block_id="llm1", human_block_id="human1", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m1"),
        ]
        
        excluded_repos = {"repo1"}
        filtered = filter_matched_pairs(pairs, excluded_repos)
        
        assert len(filtered) == 0
    
    def test_filter_matched_pairs_none_excluded(self):
        """Test when no repos are excluded."""
        pairs = [
            MatchedPair(llm_block_id="llm1", human_block_id="human1", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m1"),
        ]
        
        excluded_repos = set()
        filtered = filter_matched_pairs(pairs, excluded_repos)
        
        assert len(filtered) == 1

class TestSaveExclusionsLog:
    """Tests for save_exclusions_log function."""
    
    def test_save_exclusions_log(self):
        """Test saving exclusions log."""
        excluded_repos = {"repo1", "repo2"}
        repo_counts = {
            "repo1": {"llm": 3, "human": 5},
            "repo2": {"llm": 5, "human": 2},
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exclusions.csv"
            save_exclusions_log(excluded_repos, repo_counts, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert {"repo_name", "llm_block_count", "human_block_count", "exclusion_reason"}.issubset(rows[0].keys())

class TestSaveFilteredPairs:
    """Tests for save_filtered_pairs function."""
    
    def test_save_filtered_pairs(self):
        """Test saving filtered pairs."""
        pairs = [
            MatchedPair(llm_block_id="llm1", human_block_id="human1", repo_name="repo1", propensity_score_llm=0.5, propensity_score_human=0.5, match_id="m1"),
            MatchedPair(llm_block_id="llm2", human_block_id="human2", repo_name="repo2", propensity_score_llm=0.6, propensity_score_human=0.6, match_id="m2"),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "filtered.csv"
            save_filtered_pairs(pairs, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['llm_block_id'] == 'llm1'
                assert rows[1]['repo_name'] == 'repo2'

class TestRunRepoFilteringPipeline:
    """Tests for the complete pipeline."""
    
    def test_run_repo_filtering_pipeline(self):
        """Test the complete filtering pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "matched_pairs.csv"
            output_path = Path(tmpdir) / "filtered.csv"
            exclusions_path = Path(tmpdir) / "exclusions.csv"
            
            # Create input file
            with open(input_path, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['llm_block_id', 'human_block_id', 'repo_name', 'propensity_score_llm', 'propensity_score_human', 'match_id'])
                # repo1: 5 LLM, 5 Human (keep)
                for i in range(5):
                    writer.writerow([f'llm{i}', f'human{i}', 'repo1', 0.5, 0.5, f'm{i}'])
                # repo2: 3 LLM, 5 Human (exclude)
                for i in range(3):
                    writer.writerow([f'llm{i}', f'human{i}', 'repo2', 0.5, 0.5, f'm{i+5}'])
                # repo3: 5 LLM, 2 Human (exclude)
                for i in range(5):
                    writer.writerow([f'llm{i}', f'human{i}', 'repo3', 0.5, 0.5, f'm{i+8}'])
            
            filtered_pairs, excluded_repos = run_repo_filtering_pipeline(
                input_path=input_path,
                output_path=output_path,
                exclusions_log_path=exclusions_path,
                min_llm_blocks=5,
                min_human_blocks=5
            )
            
            # Check results
            assert len(filtered_pairs) == 5  # Only repo1
            assert all(p.repo_name == 'repo1' for p in filtered_pairs)
            assert excluded_repos == {'repo2', 'repo3'}
            
            # Check output files
            assert output_path.exists()
            assert exclusions_path.exists()
            
            # Verify filtered CSV
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 5
            
            # Verify exclusions CSV
            with open(exclusions_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                excluded_repos_from_log = {r['repo_name'] for r in rows}
                assert excluded_repos_from_log == {'repo2', 'repo3'}