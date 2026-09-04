"""
Integration test for Task T032: Merge and Save final analysis dataset.

This test verifies that:
1. The merge logic correctly combines scoring_results.csv and proxy_results.csv
2. The final_analysis.csv is created with the expected columns
3. The merge is an inner join (only posts with both scores and proxies are included)
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the functions we're testing
from code.services.merge_and_save import (
    load_scoring_results,
    load_proxy_results,
    merge_datasets,
    save_final_analysis,
    run_merge_and_save_pipeline
)
from code.config import CONFIG


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_scoring_data(temp_test_dir):
    """Create a sample scoring_results.csv file."""
    data = {
        "post_id": ["1", "2", "3", "4", "5"],
        "text": ["test1", "test2", "test3", "test4", "test5"],
        "anxiety_score": [0.1, 0.5, 0.8, 0.2, 0.9],
        "confidence_score": [0.9, 0.7, 0.65, 0.8, 0.95]
    }
    df = pd.DataFrame(data)
    output_path = temp_test_dir / "scoring_results.csv"
    df.to_csv(output_path, index=False)
    return output_path


@pytest.fixture
def sample_proxy_data(temp_test_dir):
    """Create a sample proxy_results.csv file."""
    data = {
        "post_id": ["1", "2", "3", "6", "7"],  # Note: 4 and 5 are missing, 6 and 7 are new
        "user_id": ["u1", "u2", "u3", "u4", "u5"],
        "control_proxy": [0.2, 0.5, 0.8, 0.3, 0.7],
        "timestamp_regularity": [0.1, 0.4, 0.9, 0.2, 0.6]
    }
    df = pd.DataFrame(data)
    output_path = temp_test_dir / "proxy_results.csv"
    df.to_csv(output_path, index=False)
    return output_path


def test_load_scoring_results(sample_scoring_data):
    """Test loading of scoring results."""
    df = load_scoring_results(sample_scoring_data)
    
    assert len(df) == 5
    assert "post_id" in df.columns
    assert "text" in df.columns
    assert "anxiety_score" in df.columns
    assert "confidence_score" in df.columns
    assert df["anxiety_score"].min() >= 0
    assert df["anxiety_score"].max() <= 1


def test_load_proxy_results(sample_proxy_data):
    """Test loading of proxy results."""
    df = load_proxy_results(sample_proxy_data)
    
    assert len(df) == 5
    assert "post_id" in df.columns
    assert "user_id" in df.columns
    assert "control_proxy" in df.columns
    assert "timestamp_regularity" in df.columns


def test_merge_datasets_inner_join(sample_scoring_data, sample_proxy_data):
    """Test that merge_datasets performs an inner join correctly."""
    scores_df = load_scoring_results(sample_scoring_data)
    proxies_df = load_proxy_results(sample_proxy_data)
    
    merged = merge_datasets(scores_df, proxies_df)
    
    # Expected: post_ids 1, 2, 3 (intersection of scoring and proxy data)
    # post_ids 4, 5 are in scoring but not proxy
    # post_ids 6, 7 are in proxy but not scoring
    expected_post_ids = {"1", "2", "3"}
    actual_post_ids = set(merged["post_id"].astype(str))
    
    assert actual_post_ids == expected_post_ids
    assert len(merged) == 3  # Only 3 posts in both datasets


def test_merge_preserves_all_columns(sample_scoring_data, sample_proxy_data):
    """Test that all required columns are present after merge."""
    scores_df = load_scoring_results(sample_scoring_data)
    proxies_df = load_proxy_results(sample_proxy_data)
    
    merged = merge_datasets(scores_df, proxies_df)
    
    expected_columns = {
        "post_id", "text", "anxiety_score", "confidence_score",
        "user_id", "control_proxy", "timestamp_regularity"
    }
    
    assert set(merged.columns) == expected_columns


def test_run_merge_and_save_pipeline(temp_test_dir, sample_scoring_data, sample_proxy_data):
    """Test the full merge and save pipeline."""
    output_path = temp_test_dir / "final_analysis.csv"
    
    result_path = run_merge_and_save_pipeline(
        scoring_input=sample_scoring_data,
        proxy_input=sample_proxy_data,
        output_path=output_path
    )
    
    # Verify file was created
    assert result_path.exists()
    assert result_path == output_path
    
    # Verify content
    df = pd.read_csv(result_path)
    assert len(df) == 3  # Inner join result
    assert "post_id" in df.columns
    assert "anxiety_score" in df.columns
    assert "control_proxy" in df.columns


def test_missing_scoring_file(temp_test_dir):
    """Test error handling when scoring file is missing."""
    with pytest.raises(FileNotFoundError):
        load_scoring_results(temp_test_dir / "nonexistent.csv")


def test_missing_proxy_file(temp_test_dir):
    """Test error handling when proxy file is missing."""
    with pytest.raises(FileNotFoundError):
        load_proxy_results(temp_test_dir / "nonexistent.csv")


def test_missing_post_id_column(temp_test_dir):
    """Test error handling when post_id is missing."""
    # Create scoring data without post_id
    data = {
        "text": ["test1"],
        "anxiety_score": [0.5],
        "confidence_score": [0.8]
    }
    df = pd.DataFrame(data)
    scoring_path = temp_test_dir / "scoring_no_id.csv"
    df.to_csv(scoring_path, index=False)
    
    with pytest.raises(ValueError, match="post_id"):
        load_scoring_results(scoring_path)
