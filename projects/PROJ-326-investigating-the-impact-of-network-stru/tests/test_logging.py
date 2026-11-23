"""
Unit tests for the logging infrastructure (T005).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# We will temporarily override the LOG_FILE_PATH constant
import code.src.utils.logging as logging_module

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path for testing."""
    log_file = tmp_path / "run_log.json"
    # Create empty array
    with open(log_file, 'w') as f:
        json.dump([], f)
    return str(log_file)

@pytest.fixture
def setup_logging_env(tmp_path, temp_log_file):
    """Setup environment for logging tests."""
    # Patch the constant to use temp file
    original_path = logging_module.LOG_FILE_PATH
    logging_module.LOG_FILE_PATH = temp_log_file
    yield
    # Restore original
    logging_module.LOG_FILE_PATH = original_path

def test_init_logging_creates_file(setup_logging_env, tmp_path):
    """Test that init_logging creates the log file if it doesn't exist."""
    # Remove file if it exists
    log_path = Path(tmp_path) / "run_log.json"
    if log_path.exists():
        log_path.unlink()
    
    # Re-patch for this specific test
    import code.src.utils.logging as lm
    lm.LOG_FILE_PATH = str(log_path)
    
    # Call init
    lm.init_logging()
    
    # Verify file exists and is empty array
    assert log_path.exists(), "Log file should be created"
    with open(log_path, 'r') as f:
        content = json.load(f)
    assert content == [], "Log file should be an empty array"

def test_log_metric_adds_entry(setup_logging_env):
    """Test that log_metric appends a valid entry."""
    event = {
        'timestamp': '2025-01-15T10:00:00Z',
        'event_type': 'graph_generated',
        'run_id': 'test-run-1',
        'seed': 42,
        'status': 'success',
        'duration_seconds': 1.5
    }
    
    logging_module.log_metric(event)
    
    # Read back
    log_entries = logging_module.get_run_log()
    assert len(log_entries) == 1
    assert log_entries[0]['run_id'] == 'test-run-1'
    assert set(log_entries[0].keys()) == {'timestamp', 'event_type', 'run_id', 'seed', 'status', 'duration_seconds'}

def test_log_metric_missing_fields_raises(setup_logging_env):
    """Test that log_metric raises ValueError for missing fields."""
    event = {
        'timestamp': '2025-01-15T10:00:00Z',
        'event_type': 'graph_generated',
        # Missing run_id, seed, status, duration_seconds
    }
    
    with pytest.raises(ValueError, match="Missing required fields"):
        logging_module.log_metric(event)

def test_log_run_convenience(setup_logging_env):
    """Test the log_run convenience wrapper."""
    logging_module.log_run(
        event_type='simulation_start',
        run_id='sim-run-99',
        seed=123,
        status='started',
        duration_seconds=0.01,
        extra_param='value'
    )
    
    log_entries = logging_module.get_run_log()
    assert len(log_entries) == 1
    assert log_entries[0]['run_id'] == 'sim-run-99'
    assert log_entries[0]['extra_param'] == 'value'

def test_load_existing_log_empty(setup_logging_env, tmp_path):
    """Test loading an empty log."""
    log_path = Path(tmp_path) / "empty_log.json"
    with open(log_path, 'w') as f:
        json.dump([], f)
    
    import code.src.utils.logging as lm
    original = lm.LOG_FILE_PATH
    lm.LOG_FILE_PATH = str(log_path)
    
    result = lm.load_existing_log()
    assert result == []
    lm.LOG_FILE_PATH = original

def test_schema_check(setup_logging_env):
    """Verify the schema check requirement: set(entry.keys()) == required."""
    required = {'timestamp', 'event_type', 'run_id', 'seed', 'status', 'duration_seconds'}
    
    event = {
        'timestamp': '2025-01-15T10:00:00Z',
        'event_type': 'divergence_detected',
        'run_id': 'div-test',
        'seed': 0,
        'status': 'aborted',
        'duration_seconds': 10.0
    }
    
    logging_module.log_metric(event)
    entry = logging_module.get_run_log()[-1]
    assert set(entry.keys()) == required

def test_event_types_valid(setup_logging_env):
    """Test that valid event types are accepted."""
    valid_types = ['graph_generated', 'simulation_start', 'simulation_end', 'divergence_detected', 'timeout_reached']
    for et in valid_types:
        event = {
            'timestamp': '2025-01-15T10:00:00Z',
            'event_type': et,
            'run_id': f'test-{et}',
            'seed': 1,
            'status': 'ok',
            'duration_seconds': 0.1
        }
        logging_module.log_metric(event)
    
    entries = logging_module.get_run_log()
    assert len(entries) == len(valid_types)