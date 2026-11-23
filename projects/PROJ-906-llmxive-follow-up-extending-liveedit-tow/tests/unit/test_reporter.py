import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Adjust imports based on project structure
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.reporter import (
    generate_baseline_report,
    generate_flow_report,
    _load_json_file,
    BASELINE_RESULTS_PATH,
    FLOW_RESULTS_PATH
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_json_file_existing():
    data = {"test": "value"}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        result = _load_json_file(temp_path)
        # _load_json_file returns a list if the top level is a list, or wraps dict
        # But our implementation returns the list if it's a list, or handles dict keys.
        # If the file is a simple dict without 'baseline_metrics', it returns [data] if 'clip_id' in data else []
        # Let's test with a list
    finally:
        os.unlink(temp_path)

def test_load_json_file_missing():
    result = _load_json_file("non_existent_path_12345.json")
    assert result == []

def test_generate_baseline_report_merge():
    """
    Test that generate_baseline_report correctly merges baseline metrics with resource metrics.
    """
    baseline_data = [
        {"clip_id": "clip_001", "ssim": 0.9, "consecutive_ssim": 0.85, "temporal_gradient_variance": 0.02},
        {"clip_id": "clip_002", "ssim": 0.8, "consecutive_ssim": 0.75, "temporal_gradient_variance": 0.03}
    ]
    resource_data = [
        {"clip_id": "clip_001", "peak_memory": 2.5, "inference_time": 10.2},
        {"clip_id": "clip_002", "peak_memory": 2.8, "inference_time": 11.5}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the path constants to use temp dir
        original_path = BASELINE_RESULTS_PATH
        temp_path = os.path.join(tmpdir, "baseline_results.json")
        
        # We need to patch the module's global variable or the function's internal logic
        # Since the function uses the global constant, we can't easily patch it without reloading.
        # Instead, we test the logic by mocking the file write.
        
        with patch('code.analysis.reporter.ensure_directories'), \
             patch('code.analysis.reporter.BASELINE_RESULTS_PATH', temp_path), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = generate_baseline_report(baseline_data, resource_data)
            
            # Verify the structure
            assert 'baseline_metrics' in result
            assert len(result['baseline_metrics']) == 2
            
            # Check merge logic
            m0 = result['baseline_metrics'][0]
            assert m0['clip_id'] == 'clip_001'
            assert m0['peak_memory'] == 2.5
            assert m0['inference_time'] == 10.2
            assert m0['consecutive_ssim'] == 0.85
            
            m1 = result['baseline_metrics'][1]
            assert m1['clip_id'] == 'clip_002'
            assert m1['peak_memory'] == 2.8
            assert m1['inference_time'] == 11.5
            assert m1['consecutive_ssim'] == 0.75

def test_generate_baseline_report_missing_resource():
    """
    Test that generate_baseline_report handles missing resource data gracefully.
    """
    baseline_data = [
        {"clip_id": "clip_001", "ssim": 0.9, "consecutive_ssim": 0.85}
    ]
    
    with patch('code.analysis.reporter.ensure_directories'), \
         patch('builtins.open', mock_open()):
        
        result = generate_baseline_report(baseline_data, None)
        
        assert len(result['baseline_metrics']) == 1
        # Should default to 0.0 for missing resource fields
        assert result['baseline_metrics'][0]['peak_memory'] == 0.0
        assert result['baseline_metrics'][0]['inference_time'] == 0.0

def test_generate_flow_report():
    """
    Test flow report generation.
    """
    flow_data = [
        {"clip_id": "clip_001", "ssim": 0.88, "consecutive_ssim": 0.82, "invalid_flow_count": 1}
    ]
    
    with patch('code.analysis.reporter.ensure_directories'), \
         patch('builtins.open', mock_open()):
        
        result = generate_flow_report(flow_data)
        
        assert 'flow_metrics' in result
        assert len(result['flow_metrics']) == 1
        assert result['flow_metrics'][0]['clip_id'] == 'clip_001'
        assert result['flow_metrics'][0]['invalid_flow_count'] == 1

def test_baseline_report_generation():
    """
    Full integration test for T017: Generate baseline report.
    """
    # Simulate data that would come from T016a and T008
    baseline_metrics = [
        {"clip_id": "davis_001", "ssim": 0.92, "consecutive_ssim": 0.88, "temporal_gradient_variance": 0.015},
        {"clip_id": "davis_002", "ssim": 0.85, "consecutive_ssim": 0.80, "temporal_gradient_variance": 0.025}
    ]
    resource_metrics = [
        {"clip_id": "davis_001", "peak_memory": 3.2, "inference_time": 12.5},
        {"clip_id": "davis_002", "peak_memory": 3.5, "inference_time": 13.1}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake intermediate file to simulate T016a output
        intermediate_path = os.path.join(tmpdir, "baseline_ssim.json")
        with open(intermediate_path, 'w') as f:
            json.dump(baseline_metrics, f)
        
        # We can't easily patch the global path constant in the module without reloading,
        # so we test the function logic directly with the data passed in.
        # The task requires the function to write to `data/metrics/baseline_results.json`.
        # In a real run, the main pipeline would ensure the directory exists.
        
        # Mock the file write to avoid needing real paths
        with patch('code.analysis.reporter.ensure_directories'), \
             patch('builtins.open', mock_open()) as mock_file:
            
                report = generate_baseline_report(baseline_metrics, resource_metrics)
                
                # Verify the call to open was made
                assert mock_file.called
                # Verify the content written
                handle = mock_file()
                written_content = ''.join([call[0][0] for call in handle.write.call_args_list])
                written_data = json.loads(written_content)
                
                assert 'baseline_metrics' in written_data
                assert len(written_data['baseline_metrics']) == 2
                assert written_data['baseline_metrics'][0]['peak_memory'] == 3.2
                assert written_data['baseline_metrics'][0]['consecutive_ssim'] == 0.88