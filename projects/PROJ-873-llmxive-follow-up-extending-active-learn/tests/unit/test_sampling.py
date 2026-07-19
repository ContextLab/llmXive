import json
import os
import tempfile
import pytest
from typing import List, Dict, Any

from sampling import (
    load_comparison_logs,
    filter_wasted_calls,
    stratify_by_query,
    select_stratified_sample,
    run_sampling_pipeline
)

@pytest.fixture
def sample_comparisons():
    """Create sample comparison data for testing."""
    return [
        {"id": 0, "similarity": 0.96, "query_id": "q1", "doc_id": "d1"},
        {"id": 1, "similarity": 0.97, "query_id": "q1", "doc_id": "d2"},
        {"id": 2, "similarity": 0.98, "query_id": "q2", "doc_id": "d3"},
        {"id": 3, "similarity": 0.99, "query_id": "q2", "doc_id": "d4"},
        {"id": 4, "similarity": 1.00, "query_id": "q3", "doc_id": "d5"},
        {"id": 5, "similarity": 0.94, "query_id": "q3", "doc_id": "d6"},  # Below threshold
        {"id": 6, "similarity": 0.955, "query_id": "q1", "doc_id": "d7"},
        {"id": 7, "similarity": 0.965, "query_id": "q2", "doc_id": "d8"},
    ]

def test_load_comparison_logs_from_list(sample_comparisons):
    """Test loading comparisons from a list structure."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_comparisons, f)
        temp_path = f.name
    
    try:
        result = load_comparison_logs(temp_path)
        assert len(result) == len(sample_comparisons)
        assert result[0]['id'] == 0
    finally:
        os.unlink(temp_path)

def test_filter_wasted_calls(sample_comparisons):
    """Test filtering for wasted calls (similarity > 0.95)."""
    wasted = filter_wasted_calls(sample_comparisons, threshold=0.95)
    
    # Should exclude id 5 (similarity 0.94)
    assert len(wasted) == 7
    
    # Verify all are above threshold
    for comp in wasted:
        assert comp['similarity'] > 0.95

def test_stratify_by_query(sample_comparisons):
    """Test stratification by similarity bins."""
    wasted = filter_wasted_calls(sample_comparisons, threshold=0.95)
    bins = stratify_by_query(wasted, n_bins=5)
    
    assert len(bins) > 0
    
    # Check that all items in bins are above threshold
    for bin_items in bins.values():
        for item in bin_items:
            assert item['similarity'] > 0.95

def test_select_stratified_sample(sample_comparisons):
    """Test stratified sample selection."""
    wasted = filter_wasted_calls(sample_comparisons, threshold=0.95)
    bins = stratify_by_query(wasted, n_bins=3)
    
    # Select 3 samples
    selected = select_stratified_sample(bins, sample_size=3)
    
    assert len(selected) <= 3
    assert all(isinstance(idx, int) for idx in selected)

def test_run_sampling_pipeline(sample_comparisons):
    """Test the full sampling pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create input files
        log_path = os.path.join(tmpdir, 'comparisons.json')
        config_path = os.path.join(tmpdir, 'config.json')
        output_path = os.path.join(tmpdir, 'sample.json')
        
        with open(log_path, 'w') as f:
            json.dump(sample_comparisons, f)
        
        config = {"sample_size": 3, "max_limit": 100}
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Run pipeline
        result = run_sampling_pipeline(
            log_path=log_path,
            sample_config_path=config_path,
            output_path=output_path,
            similarity_threshold=0.95
        )
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Verify output content
        with open(output_path, 'r') as f:
            sample = json.load(f)
        
        assert len(sample) <= 3
        assert all(isinstance(idx, int) for idx in sample)

def test_run_sampling_pipeline_empty_wasted(sample_comparisons):
    """Test pipeline when no wasted calls are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, 'comparisons.json')
        config_path = os.path.join(tmpdir, 'config.json')
        output_path = os.path.join(tmpdir, 'sample.json')
        
        # All similarities below threshold
        low_sim_comparisons = [
            {"id": 0, "similarity": 0.80},
            {"id": 1, "similarity": 0.85},
        ]
        
        with open(log_path, 'w') as f:
            json.dump(low_sim_comparisons, f)
        
        config = {"sample_size": 3}
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        result = run_sampling_pipeline(
            log_path=log_path,
            sample_config_path=config_path,
            output_path=output_path,
            similarity_threshold=0.95
        )
        
        assert result == []
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            sample = json.load(f)
        
        assert sample == []