"""
Unit tests for ground truth validation logic.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the config module to avoid dependency on full project setup
class MockConfig:
    def __getitem__(self, key):
        if key == 'paths':
            return {
                'raw_data': '/tmp/mock_raw',
                'results': '/tmp/mock_results'
            }
        return {}

# Patch get_config before importing the module
import sys
from unittest.mock import patch

@pytest.fixture
def mock_records():
    return [
        {'id': 1, 'label': 'success', 'data': 'log1'},
        {'id': 2, 'label': 'failure', 'data': 'log2'},
        {'id': 3, 'label': 'success', 'data': 'log3'},
        {'id': 4, 'status': 'failure', 'data': 'log4'}, # Different field
        {'id': 5, 'data': 'log5'}, # Missing label
    ]

@pytest.fixture
def temp_csv_file(mock_records):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Write header
        if mock_records:
            headers = list(mock_records[0].keys())
            f.write(','.join(headers) + '\n')
            for record in mock_records:
                values = [str(record.get(h, '')) for h in headers]
                f.write(','.join(values) + '\n')
        return f.name

def test_identify_label_field_success(mock_records):
    from src.utils.validate_ground_truth import identify_label_field
    
    # Test with 'label' field present
    label = identify_label_field(mock_records)
    assert label == 'label', "Should identify 'label' field"

def test_identify_label_field_status_fallback(mock_records):
    # Modify records to not have 'label' but have 'status'
    modified_records = [
        {'id': 1, 'status': 'success'},
        {'id': 2, 'status': 'failure'},
    ]
    from src.utils.validate_ground_truth import identify_label_field
    
    label = identify_label_field(modified_records)
    assert label == 'status', "Should identify 'status' field"

def test_identify_label_field_no_label():
    from src.utils.validate_ground_truth import identify_label_field
    
    records = [{'id': 1, 'data': 'test'}]
    label = identify_label_field(records)
    assert label is None, "Should return None if no label field found"

def test_validate_labels_valid_values():
    from src.utils.validate_ground_truth import validate_labels
    
    records = [
        {'label': 'success'},
        {'label': 'failure'},
        {'label': 'passed'},
        {'label': 'failed'},
        {'label': '1'},
        {'label': '0'},
    ]
    
    result = validate_labels(records, 'label')
    assert result['valid_count'] == 6
    assert len(result['issues']) == 0

def test_validate_labels_invalid_values():
    from src.utils.validate_ground_truth import validate_labels
    
    records = [
        {'label': 'success'},
        {'label': 'unknown'},
        {'label': 'maybe'},
    ]
    
    result = validate_labels(records, 'label')
    assert result['valid_count'] == 1
    assert len(result['issues']) == 2

def test_validate_labels_missing_field():
    from src.utils.validate_ground_truth import validate_labels
    
    records = [
        {'label': 'success'},
        {'other': 'failure'},
    ]
    
    result = validate_labels(records, 'label')
    assert result['valid_count'] == 1
    assert len(result['issues']) == 1
    assert 'missing label field' in result['issues'][0]

def test_main_integration(temp_csv_file):
    from src.utils.validate_ground_truth import main
    from pathlib import Path
    import json
    
    # Create temp directories
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / 'raw'
        res_dir = Path(tmpdir) / 'results'
        raw_dir.mkdir()
        res_dir.mkdir()
        
        # Move csv to raw dir
        csv_path = raw_dir / 'data.csv'
        with open(temp_csv_file, 'r') as src:
            with open(csv_path, 'w') as dst:
                dst.write(src.read())
        
        # Mock config
        with patch('src.utils.validate_ground_truth.get_config') as mock_config:
            mock_config.return_value = {
                'paths': {
                    'raw_data': str(raw_dir),
                    'results': str(res_dir)
                }
            }
            
            # Run main
            main()
            
            # Check output
            output_file = res_dir / 'ground_truth_validation.json'
            assert output_file.exists(), "Output file should be created"
            
            with open(output_file, 'r') as f:
                report = json.load(f)
            
            assert 'status' in report
            assert 'sample_size' in report
            assert 'issues' in report
            assert report['sample_size'] > 0