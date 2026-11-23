import pytest
import os
import json
import tempfile
from sampling import run_sampling_pipeline, stratify_by_query, select_stratified_sample
from metrics import calculate_dynamic_sample_size

def test_stratify_by_query():
    data = [
        {'query_id': 'q1', 'similarity': 0.96},
        {'query_id': 'q1', 'similarity': 0.97},
        {'query_id': 'q2', 'similarity': 0.98}
    ]
    result = stratify_by_query(data)
    assert 'q1' in result
    assert 'q2' in result
    assert len(result['q1']) == 2
    assert len(result['q2']) == 1

def test_select_stratified_sample():
    data = [
        {'query_id': 'q1', 'similarity': 0.96},
        {'query_id': 'q1', 'similarity': 0.97},
        {'query_id': 'q2', 'similarity': 0.98}
    ]
    stratified = stratify_by_query(data)
    indices = select_stratified_sample(stratified, 2)
    assert len(indices) == 2
    assert all(0 <= i < 3 for i in indices)

def test_run_sampling_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        flagged_path = os.path.join(tmpdir, 'flagged.json')
        config_path = os.path.join(tmpdir, 'config.json')
        output_path = os.path.join(tmpdir, 'sample.json')
        
        data = [
            {'query_id': 'q1', 'similarity': 0.96},
            {'query_id': 'q1', 'similarity': 0.97},
            {'query_id': 'q2', 'similarity': 0.98},
            {'query_id': 'q2', 'similarity': 0.99}
        ]
        with open(flagged_path, 'w') as f:
            json.dump(data, f)
        
        config = {'sample_size': 3}
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        run_sampling_pipeline(flagged_path, config_path, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert 'selected_indices' in result
        assert len(result['selected_indices']) == 3
        assert result['total_flagged'] == 4

def test_calculate_dynamic_sample_size_integration():
    # Test the function used by the pipeline
    assert calculate_dynamic_sample_size(100, 50) == 50  # Cap applied
    assert calculate_dynamic_sample_size(100, 200) == 20  # 20% of 100
