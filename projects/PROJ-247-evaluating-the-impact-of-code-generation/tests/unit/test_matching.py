"""
Unit tests for the matching module (T015).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from utils.matching import (
    load_block_metrics,
    load_repo_metadata,
    calculate_propensity_scores,
    perform_nearest_neighbor_matching,
    run_matching_pipeline,
    MatchingError
)

@pytest.fixture
def sample_block_metrics():
    """Create a temporary CSV with sample block metrics."""
    data = {
        'repo_id': ['repo_A', 'repo_A', 'repo_A', 'repo_B', 'repo_B'],
        'block_id': ['b1', 'b2', 'b3', 'b4', 'b5'],
        'label': ['LLM', 'Human', 'LLM', 'Human', 'Human'],
        'cyclomatic_complexity': [5, 6, 4, 7, 3],
        'max_nesting_depth': [2, 3, 1, 4, 2],
        'loc': [50, 60, 40, 80, 30],
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def sample_repo_metadata():
    """Create a temporary CSV with sample repo metadata."""
    data = {
        'repo_id': ['repo_A', 'repo_B'],
        'stars': [100, 50],
        'created_at': ['2020-01-01', '2021-01-01'],
        'updated_at': ['2023-01-01', '2023-01-01'],
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

def test_load_block_metrics(sample_block_metrics):
    df = load_block_metrics(sample_block_metrics)
    assert 'repo_id' in df.columns
    assert 'block_id' in df.columns
    assert 'label' in df.columns
    assert len(df) == 5
    # Check label uppercasing
    assert all(df['label'].isin(['LLM', 'Human']))
    os.unlink(sample_block_metrics)

def test_load_repo_metadata(sample_repo_metadata):
    df = load_repo_metadata(sample_repo_metadata)
    assert 'repo_id' in df.columns
    assert 'stars' in df.columns
    assert len(df) == 2
    os.unlink(sample_repo_metadata)

def test_calculate_propensity_scores(sample_block_metrics, sample_repo_metadata):
    # Load and merge manually for this test
    block_df = load_block_metrics(sample_block_metrics)
    repo_df = load_repo_metadata(sample_repo_metadata)
    merged = pd.merge(block_df, repo_df, on='repo_id', how='inner')
    merged['repo_age_days'] = 0 # Dummy age
    
    scored = calculate_propensity_scores(merged)
    assert 'propensity' in scored.columns
    assert all((scored['propensity'] >= 0) & (scored['propensity'] <= 1))
    
    os.unlink(sample_block_metrics)
    os.unlink(sample_repo_metadata)

def test_perform_nearest_neighbor_matching():
    # Create a simple dataset where matching is deterministic
    data = {
        'repo_id': ['repo_A', 'repo_A', 'repo_A', 'repo_A'],
        'block_id': ['llm1', 'llm2', 'h1', 'h2'],
        'label': ['LLM', 'LLM', 'Human', 'Human'],
        'propensity': [0.5, 0.6, 0.51, 0.59]
    }
    df = pd.DataFrame(data)
    
    matched = perform_nearest_neighbor_matching(df, ratio=1, caliper=0.1)
    
    assert len(matched) == 2 # 2 LLMs matched
    assert 'llm_block_id' in matched.columns
    assert 'human_block_id' in matched.columns
    assert 'match_id' in matched.columns

def test_run_matching_pipeline(sample_block_metrics, sample_repo_metadata):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'matched_pairs.csv')
        
        result = run_matching_pipeline(
            block_metrics_path=sample_block_metrics,
            repo_metadata_path=sample_repo_metadata,
            output_path=output_path
        )
        
        assert Path(output_path).exists()
        assert len(result) > 0
        assert 'match_id' in result.columns
        
        # Verify file content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(result)

def test_missing_columns_raises_error():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("repo_id,block_id\n1,2\n") # Missing 'label'
        fname = f.name
    
    with pytest.raises(ValueError):
        load_block_metrics(fname)
    
    os.unlink(fname)