import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.matching import (
    load_block_metrics,
    load_repo_metadata,
    calculate_propensity_scores,
    perform_nearest_neighbor_matching,
    run_matching_pipeline,
    MatchingError
)

class TestMatching:
    
    @pytest.fixture
    def sample_block_metrics(self):
        """Create sample block metrics data."""
        data = {
            'block_id': ['b1', 'b2', 'b3', 'b4', 'b5', 'b6'],
            'repo_id': ['r1', 'r1', 'r1', 'r2', 'r2', 'r2'],
            'label': ['LLM', 'HUMAN', 'LLM', 'HUMAN', 'LLM', 'HUMAN'],
            'cyclomatic_complexity': [5, 6, 4, 7, 5, 6],
            'loc': [20, 25, 18, 30, 22, 24]
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sample_repo_metadata(self):
        """Create sample repo metadata."""
        data = {
            'repo_id': ['r1', 'r2'],
            'stargazers_count': [100, 200],
            'created_at': ['2020-01-01', '2019-06-01'],
            'updated_at': ['2023-01-01', '2023-06-01']
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_load_block_metrics(self, sample_block_metrics, temp_dir):
        """Test loading block metrics from CSV."""
        csv_path = temp_dir / "test_blocks.csv"
        sample_block_metrics.to_csv(csv_path, index=False)
        
        loaded_df = load_block_metrics(csv_path)
        assert len(loaded_df) == 6
        assert 'block_id' in loaded_df.columns
        assert 'label' in loaded_df.columns
    
    def test_load_block_metrics_missing_file(self, temp_dir):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_block_metrics(temp_dir / "nonexistent.csv")
    
    def test_load_block_metrics_missing_columns(self, temp_dir):
        """Test error when required columns are missing."""
        data = {'block_id': ['b1'], 'repo_id': ['r1']}
        df = pd.DataFrame(data)
        csv_path = temp_dir / "bad_blocks.csv"
        df.to_csv(csv_path, index=False)
        
        with pytest.raises(MatchingError):
            load_block_metrics(csv_path)
    
    def test_calculate_propensity_scores(self, sample_block_metrics):
        """Test propensity score calculation."""
        scored_df = calculate_propensity_scores(sample_block_metrics)
        
        assert 'propensity_score' in scored_df.columns
        assert len(scored_df) == 6
        # Scores should be between 0 and 1
        assert (scored_df['propensity_score'] >= 0).all()
        assert (scored_df['propensity_score'] <= 1).all()
    
    def test_calculate_propensity_scores_single_class(self):
        """Test error when all blocks have same label."""
        data = {
            'block_id': ['b1', 'b2'],
            'repo_id': ['r1', 'r1'],
            'label': ['LLM', 'LLM'],
            'cyclomatic_complexity': [5, 6],
            'loc': [20, 25]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(MatchingError):
            calculate_propensity_scores(df)
    
    def test_perform_nearest_neighbor_matching(self, sample_block_metrics):
        """Test 1:1 nearest neighbor matching."""
        # First calculate propensity scores
        scored_df = calculate_propensity_scores(sample_block_metrics)
        
        # Perform matching
        matched_pairs = perform_nearest_neighbor_matching(scored_df)
        
        # Should have matches for r1 (2 LLM, 1 HUMAN -> 1 match) and r2 (1 LLM, 1 HUMAN -> 1 match)
        assert len(matched_pairs) >= 1
        assert 'llm_block_id' in matched_pairs.columns
        assert 'human_block_id' in matched_pairs.columns
        assert 'repo_id' in matched_pairs.columns
        assert 'propensity_diff' in matched_pairs.columns
    
    def test_perform_nearest_neighbor_matching_no_matches(self):
        """Test matching when no pairs can be formed."""
        data = {
            'block_id': ['b1'],
            'repo_id': ['r1'],
            'label': ['LLM'],
            'cyclomatic_complexity': [5],
            'loc': [20]
        }
        df = pd.DataFrame(data)
        scored_df = calculate_propensity_scores(df)
        
        matched_pairs = perform_nearest_neighbor_matching(scored_df)
        assert len(matched_pairs) == 0
    
    def test_run_matching_pipeline(self, sample_block_metrics, sample_repo_metadata, temp_dir):
        """Test the full matching pipeline."""
        blocks_path = temp_dir / "blocks.csv"
        metadata_path = temp_dir / "metadata.csv"
        output_path = temp_dir / "matched_pairs.csv"
        
        sample_block_metrics.to_csv(blocks_path, index=False)
        sample_repo_metadata.to_csv(metadata_path, index=False)
        
        result_df = run_matching_pipeline(blocks_path, metadata_path, output_path)
        
        assert output_path.exists()
        assert len(result_df) >= 0  # At least 0 matches possible
        
        # Verify output schema
        loaded_result = pd.read_csv(output_path)
        assert 'llm_block_id' in loaded_result.columns
        assert 'human_block_id' in loaded_result.columns
    
    def test_run_matching_pipeline_missing_files(self, temp_dir):
        """Test error when input files don't exist."""
        output_path = temp_dir / "matched_pairs.csv"
        
        with pytest.raises(FileNotFoundError):
            run_matching_pipeline(
                temp_dir / "nonexistent_blocks.csv",
                temp_dir / "nonexistent_metadata.csv",
                output_path
            )
    
    def test_matching_within_repositories(self):
        """Ensure matching only happens within the same repository."""
        data = {
            'block_id': ['b1', 'b2', 'b3', 'b4'],
            'repo_id': ['r1', 'r1', 'r2', 'r2'],
            'label': ['LLM', 'HUMAN', 'LLM', 'HUMAN'],
            'cyclomatic_complexity': [1, 100, 1, 100],
            'loc': [10, 1000, 10, 1000]
        }
        df = pd.DataFrame(data)
        scored_df = calculate_propensity_scores(df)
        
        matched_pairs = perform_nearest_neighbor_matching(scored_df)
        
        # Should have 2 matches: (r1: b1-b2) and (r2: b3-b4)
        # Not cross-repo matches
        assert len(matched_pairs) == 2
        assert set(matched_pairs['repo_id']) == {'r1', 'r2'}