"""
Unit tests for the stats data loader (T027a).
Verifies loading of baseline and flow metrics.
"""
import json
import os
import pytest
from pathlib import Path
import tempfile

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stats import load_json_metrics, load_baseline_and_flow_metrics

@pytest.fixture
def temp_metric_files():
    """Create temporary metric files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = os.path.join(tmpdir, "baseline_results.json")
        flow_path = os.path.join(tmpdir, "flow_results.json")

        baseline_data = [
            {"clip_id": "clip_001", "peak_memory": 1024, "consecutive_ssim": 0.95},
            {"clip_id": "clip_002", "peak_memory": 1100, "consecutive_ssim": 0.92}
        ]
        flow_data = [
            {"clip_id": "clip_001", "peak_memory": 800, "consecutive_ssim": 0.94, "flow_magnitude": 2.5},
            {"clip_id": "clip_002", "peak_memory": 850, "consecutive_ssim": 0.91, "flow_magnitude": 3.1}
        ]

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        with open(flow_path, 'w') as f:
            json.dump(flow_data, f)

        yield baseline_path, flow_path

def test_load_json_metrics_valid_file(temp_metric_files):
    """Test loading a valid JSON metrics file."""
    baseline_path, _ = temp_metric_files
    data = load_json_metrics(baseline_path)
    
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['clip_id'] == 'clip_001'

def test_load_baseline_flow_metrics_missing_file():
    """Test that missing files raise FileNotFoundError."""
    # We rely on the actual paths in the module, which should not exist in test env
    # unless created. This test verifies the error handling.
    with pytest.raises(FileNotFoundError):
        # This will attempt to load from the default paths defined in stats.py
        # which likely don't exist in the test environment
        load_baseline_and_flow_metrics()

def test_load_json_metrics_invalid_json():
    """Test handling of invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("not valid json")
        temp_path = f.name

    try:
        with pytest.raises(json.JSONDecodeError):
            load_json_metrics(temp_path)
    finally:
        os.unlink(temp_path)

def test_load_json_metrics_empty_list():
    """Test loading an empty list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_path = f.name

    try:
        data = load_json_metrics(temp_path)
        assert data == []
    finally:
        os.unlink(temp_path)
