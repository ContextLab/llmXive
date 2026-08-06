import os
import json
import tempfile
import shutil
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# We need to mock the config to avoid dependency on full project setup for unit tests
# But since T009 is about the infrastructure, we test the logic directly.

# Import the module under test
# We will patch the config to return a temporary directory for testing
import code.utils.logging_utils as logging_utils
from code.config import get_config

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def mock_config(temp_dir):
    """Mock the config to use temporary directories."""
    original_get_config = get_config
    
    def mock_config():
        return {
            'paths': {
                'artifacts': temp_dir,
                'data': os.path.join(temp_dir, 'data'),
                'code': os.path.join(temp_dir, 'code'),
                'tests': os.path.join(temp_dir, 'tests')
            }
        }
    
    with patch('code.utils.logging_utils.get_config', mock_config):
        with patch('code.utils.logging_utils.ensure_directories'):
            yield mock_config

def test_setup_logging_creates_files(mock_config, temp_dir):
    """Test that setup_logging creates the log directory and initializes state."""
    # Reset global state
    logging_utils._metrics_buffer.clear()
    logging_utils._metrics_file_path = None
    logging_utils._logger_instance = None

    logger = logging_utils.setup_logging()
    
    assert logger is not None
    assert logging_utils._logger_instance is not None
    assert logging_utils._metrics_file_path is not None
    
    # Check log directory exists
    log_dir = os.path.join(temp_dir, 'logs')
    assert os.path.exists(log_dir)

def test_log_metric_appends_to_buffer(mock_config, temp_dir):
    """Test that log_metric adds entries to the buffer."""
    logging_utils._metrics_buffer.clear()
    logging_utils._logger_instance = None
    
    # Force setup to set the file path
    with patch('code.utils.logging_utils.ensure_directories'):
        logging_utils.setup_logging()
    
    logging_utils.log_metric("test_key", 123)
    logging_utils.log_metric("test_key_2", 456, step=1)
    
    assert len(logging_utils._metrics_buffer) == 2
    assert logging_utils._metrics_buffer[0]['key'] == 'test_key'
    assert logging_utils._metrics_buffer[0]['value'] == 123
    assert logging_utils._metrics_buffer[1]['step'] == 1

def test_flush_metrics_writes_file(mock_config, temp_dir):
    """Test that flush_metrics writes the JSON file."""
    logging_utils._metrics_buffer.clear()
    logging_utils._logger_instance = None
    logging_utils._metrics_file_path = os.path.join(temp_dir, 'metrics.json')
    
    with patch('code.utils.logging_utils.ensure_directories'):
        logging_utils.setup_logging()
    
    logging_utils.log_metric("flush_test", 999)
    logging_utils.flush_metrics()
    
    assert os.path.exists(logging_utils._metrics_file_path)
    
    with open(logging_utils._metrics_file_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) >= 1
    assert any(item['key'] == 'flush_test' for item in data)

def test_get_metrics_returns_copy(mock_config, temp_dir):
    """Test that get_metrics returns a copy, not the reference."""
    logging_utils._metrics_buffer.clear()
    logging_utils._logger_instance = None
    
    with patch('code.utils.logging_utils.ensure_directories'):
        logging_utils.setup_logging()
    
    logging_utils.log_metric("ref_test", 1)
    retrieved = logging_utils.get_metrics()
    
    # Modify retrieved list
    retrieved.append({"fake": True})
    
    # Original buffer should be unchanged
    assert len(logging_utils._metrics_buffer) == 1
    assert len(retrieved) == 2