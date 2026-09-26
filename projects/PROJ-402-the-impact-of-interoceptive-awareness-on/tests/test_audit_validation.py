import pytest
import os
import sys
import json
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.schema_validator import load_schema_from_file, validate_data_against_schema
from utils.bids_scanner import find_events_files
from code_02_audit_metadata import validate_events_tsv, local_bids_scan, generate_audit_report

# Note: The module is named 02_audit_metadata.py but we import it as code_02_audit_metadata
# This is a workaround for Python's import restrictions on leading digits

@pytest.fixture
def temp_schema_dir():
    """Create a temporary directory with a valid schema file."""
    temp_dir = tempfile.mkdtemp()
    schema_path = Path(temp_dir) / "test_schema.yaml"
    
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "enum": ["Schandry", "heartbeat", "TSST", "rest", "baseline"]
            },
            "onset": {"type": "number"},
            "duration": {"type": "number"},
            "value": {"type": "number"},
            "trial_type": {"type": "string"}
        },
        "required": ["task"]
    }
    
    import yaml
    with open(schema_path, 'w') as f:
        yaml.dump(schema_content, f)
        
    yield schema_path
    shutil.rmtree(temp_dir)

@pytest.fixture
def valid_events_tsv(temp_dir):
    """Create a valid events.tsv file."""
    temp_dir = tempfile.mkdtemp()
    events_path = Path(temp_dir) / "sub-01_task-schandry_events.tsv"
    
    data = {
        'task': ['Schandry', 'Schandry', 'Schandry'],
        'onset': [0.0, 10.0, 20.0],
        'duration': [5.0, 5.0, 5.0],
        'value': [1, 2, 3]
    }
    df = pd.DataFrame(data)
    df.to_csv(events_path, sep='\t', index=False)
    
    yield events_path
    shutil.rmtree(temp_dir)

@pytest.fixture
def invalid_events_tsv(temp_dir):
    """Create an invalid events.tsv file (missing required 'task' column)."""
    temp_dir = tempfile.mkdtemp()
    events_path = Path(temp_dir) / "sub-01_task-invalid_events.tsv"
    
    data = {
        'onset': [0.0, 10.0, 20.0],
        'duration': [5.0, 5.0, 5.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(events_path, sep='\t', index=False)
    
    yield events_path
    shutil.rmtree(temp_dir)

def test_validate_events_tsv_valid_file(valid_events_tsv, temp_schema_dir):
    """Test validation of a valid events.tsv file."""
    # Load schema
    schema = load_schema_from_file(temp_schema_dir)
    
    # Validate
    result = validate_events_tsv(valid_events_tsv, schema)
    
    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert str(valid_events_tsv) in result['file']

def test_validate_events_tsv_invalid_file(invalid_events_tsv, temp_schema_dir):
    """Test validation of an invalid events.tsv file."""
    schema = load_schema_from_file(temp_schema_dir)
    
    result = validate_events_tsv(invalid_events_tsv, schema)
    
    assert result['valid'] is False
    assert len(result['errors']) > 0
    assert "task" in str(result['errors']).lower() or "required" in str(result['errors']).lower()

def test_validate_events_tsv_missing_file(temp_schema_dir):
    """Test validation of a non-existent file."""
    schema = load_schema_from_file(temp_schema_dir)
    fake_path = Path("/nonexistent/path/events.tsv")
    
    result = validate_events_tsv(fake_path, schema)
    
    assert result['valid'] is False
    assert "not found" in result['errors'][0].lower()

def test_local_bids_scan_integration(temp_schema_dir):
    """Test the full local BIDS scan with validation."""
    # Create a temporary data directory structure
    temp_data = tempfile.mkdtemp()
    data_dir = Path(temp_data)
    
    # Create valid events file
    valid_events = data_dir / "sub-01" / "sub-01_task-schandry_events.tsv"
    valid_events.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'task': ['Schandry', 'Schandry'],
        'onset': [0.0, 10.0],
        'duration': [5.0, 5.0]
    }
    pd.DataFrame(data).to_csv(valid_events, sep='\t', index=False)
    
    # Create invalid events file
    invalid_events = data_dir / "sub-02" / "sub-02_task-bad_events.tsv"
    invalid_events.parent.mkdir(parents=True, exist_ok=True)
    
    data_bad = {
        'onset': [0.0],
        'duration': [5.0]
    }
    pd.DataFrame(data_bad).to_csv(invalid_events, sep='\t', index=False)
    
    try:
        schema = load_schema_from_file(temp_schema_dir)
        
        # Run scan
        result = local_bids_scan(schema)
        
        # Verify results
        assert len(result['events_files']) == 2
        assert result['has_schandry_or_heartbeat'] is True
        assert 'schandry' in result['found_tasks']
        assert result['feasibility_status'] == "Success"
        
        # Check validation results
        valid_count = sum(1 for v in result['validations'] if v['valid'])
        invalid_count = sum(1 for v in result['validations'] if not v['valid'])
        
        assert valid_count == 1
        assert invalid_count == 1
        
    finally:
        shutil.rmtree(temp_data)

def test_generate_audit_report_creates_file(temp_schema_dir):
    """Test that generate_audit_report creates the markdown file."""
    temp_results = tempfile.mkdtemp()
    results_dir = Path(temp_results)
    
    # Mock data
    remote_check = {
        'checked': True,
        'count': 1,
        'relevant_studies': [{'id': 'ds001', 'name': 'Test Study', 'keywords': ['tsst', 'heartbeat']}]
    }
    
    local_scan = {
        'events_files': ['/fake/path.tsv'],
        'validations': [{'file': '/fake/path.tsv', 'valid': True, 'errors': []}],
        'found_tasks': ['schandry'],
        'has_schandry_or_heartbeat': True,
        'has_tsst': False,
        'feasibility_status': 'Success'
    }
    
    try:
        # Temporarily override RESULTS_DIR
        import code_02_audit_metadata as audit_module
        original_dir = audit_module.RESULTS_DIR
        audit_module.RESULTS_DIR = results_dir
        
        report_path = generate_audit_report(remote_check, local_scan)
        
        assert report_path.exists()
        assert report_path.name == "data_audit.md"
        
        content = report_path.read_text()
        assert "Feasibility Success" in content
        assert "Schandry" in content
        
    finally:
        # Restore original
        import code_02_audit_metadata as audit_module
        audit_module.RESULTS_DIR = original_dir
        shutil.rmtree(temp_results)
