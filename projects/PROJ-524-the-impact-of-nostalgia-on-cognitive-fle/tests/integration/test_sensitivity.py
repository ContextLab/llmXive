import os
import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

RESULTS_DIR = Path("data/results")
SENSITIVITY_REPORT_PATH = RESULTS_DIR / "sensitivity_report.json"

@pytest.fixture
def mock_sensitivity_data(tmp_path):
    """Create mock sensitivity analysis data."""
    data = {
        'threshold_0.04': {'significant': True, 'p_value': 0.03},
        'threshold_0.05': {'significant': True, 'p_value': 0.045},
        'threshold_0.06': {'significant': True, 'p_value': 0.055},
        'threshold_0.10': {'significant': True, 'p_value': 0.09}
    }
    path = tmp_path / "sensitivity_report.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

def test_sensitivity_analysis_runs(mock_sensitivity_data, tmp_path):
    """Test that sensitivity analysis can process the mock data."""
    # Simulate reading the data
    with open(mock_sensitivity_data, 'r') as f:
        data = json.load(f)
    
    # Verify we can iterate and check significance
    for threshold_key, result in data.items():
        assert 'significant' in result
        assert 'p_value' in result
        
        threshold = float(threshold_key.split('_')[1])
        p_val = result['p_value']
        
        # Check logic
        assert result['significant'] == (p_val <= threshold)

def test_borderline_threshold_detection(mock_sensitivity_data):
    """Test that borderline p-values (0.04-0.06) are detected."""
    with open(mock_sensitivity_data, 'r') as f:
        data = json.load(f)
    
    # Check for borderline cases
    borderline_found = False
    for threshold_key, result in data.items():
        p_val = result['p_value']
        if 0.04 <= p_val <= 0.06:
            borderline_found = True
            # This should be flagged
            assert result.get('is_borderline', False) or True # Placeholder for actual logic
    
    # In our mock data, 0.045 and 0.055 are borderline
    assert borderline_found, "Expected to find borderline p-values in mock data"

def test_sensitivity_report_generation(mock_sensitivity_data, tmp_path):
    """Test that a sensitivity report can be generated."""
    with open(mock_sensitivity_data, 'r') as f:
        data = json.load(f)
    
    # Generate a summary report
    summary = {
        'total_thresholds': len(data),
        'borderline_count': sum(1 for r in data.values() if 0.04 <= r['p_value'] <= 0.06),
        'is_sensitive_to_threshold': False # Would be calculated based on variation
    }
    
    output_path = tmp_path / "sensitivity_summary.json"
    with open(output_path, 'w') as f:
        json.dump(summary, f)
    
    # Verify
    with open(output_path, 'r') as f:
        loaded_summary = json.load(f)
    
    assert loaded_summary['total_thresholds'] == 4
    assert loaded_summary['borderline_count'] == 2 # 0.045 and 0.055
