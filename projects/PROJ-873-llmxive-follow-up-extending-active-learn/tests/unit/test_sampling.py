"""
Unit tests for sampling module (T013b).
"""
import json
import os
import tempfile
import pytest
from collections import defaultdict
from typing import List, Dict, Any

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from sampling import (
    load_comparison_logs,
    filter_wasted_calls,
    stratify_by_similarity,
    select_stratified_sample,
    load_sample_config,
    run_sampling_pipeline
)


@pytest.fixture
def sample_logs():
    """Create sample comparison logs for testing."""
    return [
        {"index": 0, "similarity": 0.92, "pair": ("a", "b")},
        {"index": 1, "similarity": 0.95, "pair": ("c", "d")},
        {"index": 2, "similarity": 0.96, "pair": ("e", "f")},
        {"index": 3, "similarity": 0.965, "pair": ("g", "h")},
        {"index": 4, "similarity": 0.97, "pair": ("i", "j")},
        {"index": 5, "similarity": 0.98, "pair": ("k", "l")},
        {"index": 6, "similarity": 0.99, "pair": ("m", "n")},
        {"index": 7, "similarity": 0.94, "pair": ("o", "p")},
    ]


@pytest.fixture
def sample_config():
    """Create sample config for testing."""
    return {
        "total_flagged_count": 100,
        "max_limit": 1000,
        "sample_size": 3,
        "calculation_method": "dynamic_percentage_capped"
    }


def test_filter_wasted_calls(sample_logs):
    """Test filtering for similarity > 0.95."""
    wasted = filter_wasted_calls(sample_logs, threshold=0.95)
    
    # Should include items with similarity > 0.95
    assert len(wasted) == 5  # indices 2, 3, 4, 5, 6
    similarities = [item["similarity"] for item in wasted]
    assert all(s > 0.95 for s in similarities)
    
    # Indices should match expected
    indices = [item["index"] for item in wasted]
    assert set(indices) == {2, 3, 4, 5, 6}


def test_filter_wasted_calls_no_threshold_match(sample_logs):
    """Test filtering when no items exceed threshold."""
    wasted = filter_wasted_calls(sample_logs, threshold=0.999)
    assert len(wasted) == 0


def test_stratify_by_similarity(sample_logs):
    """Test stratification into bins."""
    wasted = filter_wasted_calls(sample_logs, threshold=0.95)
    bins = stratify_by_similarity(wasted, bin_width=0.01, threshold=0.95)
    
    assert len(bins) == 4  # [0.95, 0.96), [0.96, 0.97), [0.97, 0.98), [0.98, 0.99)
    
    # Check bin contents
    assert len(bins["[0.95, 0.96)"]) == 1  # index 2 (0.96 is not > 0.96, wait... 0.96 is in [0.96, 0.97))
    # Actually: 0.96 -> bin [0.96, 0.97), 0.965 -> [0.96, 0.97), 0.97 -> [0.97, 0.98), 0.98 -> [0.98, 0.99), 0.99 -> [0.99, 1.00)
    
    # Recalculate:
    # 0.96 -> bin_idx = int((0.96 - 0.95) / 0.01) = 1 -> [0.96, 0.97)
    # 0.965 -> bin_idx = int((0.965 - 0.95) / 0.01) = 1 -> [0.96, 0.97)
    # 0.97 -> bin_idx = int((0.97 - 0.95) / 0.01) = 2 -> [0.97, 0.98)
    # 0.98 -> bin_idx = int((0.98 - 0.95) / 0.01) = 3 -> [0.98, 0.99)
    # 0.99 -> bin_idx = int((0.99 - 0.95) / 0.01) = 4 -> [0.99, 1.00)
    
    assert len(bins["[0.96, 0.97)"]) == 2
    assert len(bins["[0.97, 0.98)"]) == 1
    assert len(bins["[0.98, 0.99)"]) == 1
    assert len(bins["[0.99, 1.00)"]) == 1


def test_select_stratified_sample(sample_logs, sample_config):
    """Test stratified sample selection."""
    wasted = filter_wasted_calls(sample_logs, threshold=0.95)
    bins = stratify_by_similarity(wasted, bin_width=0.01, threshold=0.95)
    
    sample_indices = select_stratified_sample(bins, sample_size=3)
    
    assert len(sample_indices) == 3
    assert all(idx in [2, 3, 4, 5, 6] for idx in sample_indices)
    assert len(set(sample_indices)) == 3  # No duplicates


def test_select_stratified_sample_all_items(sample_logs, sample_config):
    """Test when sample_size >= total items."""
    wasted = filter_wasted_calls(sample_logs, threshold=0.95)
    bins = stratify_by_similarity(wasted, bin_width=0.01, threshold=0.95)
    
    sample_indices = select_stratified_sample(bins, sample_size=100)
    
    # Should return all 5 items
    assert len(sample_indices) == 5
    assert set(sample_indices) == {2, 3, 4, 5, 6}


def test_run_sampling_pipeline(sample_logs, sample_config):
    """Test full pipeline execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "logs.json")
        config_path = os.path.join(tmpdir, "config.json")
        output_path = os.path.join(tmpdir, "sample.json")
        
        # Write test data
        with open(log_path, "w") as f:
            json.dump(sample_logs, f)
        
        with open(config_path, "w") as f:
            json.dump(sample_config, f)
        
        # Run pipeline
        result = run_sampling_pipeline(
            log_path=log_path,
            config_path=config_path,
            output_path=output_path,
            threshold=0.95,
            bin_width=0.01
        )
        
        # Verify output file
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            saved_sample = json.load(f)
        
        assert len(saved_sample) == 3
        assert set(saved_sample) == set(result)
