import json
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock
import pytest

# Mock config to use temporary directories for testing
@pytest.fixture
def mock_config(tmp_path):
    """Mock config functions to use temporary directories."""
    with patch('code.utils.runtime_verifier.get_results_dir', return_value=str(tmp_path / 'results')):
        with patch('code.utils.runtime_verifier.get_logs_dir', return_value=str(tmp_path / 'logs')):
            with patch('code.utils.runtime_verifier.get_time_limit_seconds', return_value=100): # 100s limit for test
                with patch('code.utils.runtime_verifier.ensure_directories'):
                    # Create the directories
                    (tmp_path / 'results').mkdir(parents=True)
                    (tmp_path / 'logs').mkdir(parents=True)
                    yield tmp_path

def test_verify_runtime_pass(mock_config):
    """Test that PASS is logged when runtime is under limit."""
    # Setup metrics file
    metrics_path = os.path.join(str(mock_config / 'results'), 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump({'total_runtime_seconds': 50}, f)
    
    # Capture log output
    with patch('code.utils.runtime_verifier.setup_verifier_logger') as mock_logger_setup:
        mock_logger = MagicMock()
        mock_logger_setup.return_value = mock_logger
        
        from code.utils.runtime_verifier import verify_runtime_limit
        result = verify_runtime_limit()
        
        assert result is True
        # Verify the info log was called with PASS message
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("PASS" in c for c in calls)

def test_verify_runtime_fail(mock_config):
    """Test that FAIL is logged when runtime exceeds limit."""
    # Setup metrics file with runtime > limit (100)
    metrics_path = os.path.join(str(mock_config / 'results'), 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump({'total_runtime_seconds': 150}, f)
    
    with patch('code.utils.runtime_verifier.setup_verifier_logger') as mock_logger_setup:
        mock_logger = MagicMock()
        mock_logger_setup.return_value = mock_logger
        
        from code.utils.runtime_verifier import verify_runtime_limit
        result = verify_runtime_limit()
        
        assert result is False
        # Verify the warning log was called with FAIL message
        calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("FAIL" in c for c in calls)

def test_verify_runtime_missing_metrics(mock_config):
    """Test handling when metrics.json is missing."""
    # Don't create metrics.json
    
    with patch('code.utils.runtime_verifier.setup_verifier_logger') as mock_logger_setup:
        mock_logger = MagicMock()
        mock_logger_setup.return_value = mock_logger
        
        from code.utils.runtime_verifier import verify_runtime_limit
        result = verify_runtime_limit()
        
        assert result is False
        mock_logger.error.assert_called()

def test_verify_runtime_missing_field(mock_config):
    """Test handling when total_runtime_seconds is missing in metrics."""
    metrics_path = os.path.join(str(mock_config / 'results'), 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump({'other_field': 123}, f)
    
    with patch('code.utils.runtime_verifier.setup_verifier_logger') as mock_logger_setup:
        mock_logger = MagicMock()
        mock_logger_setup.return_value = mock_logger
        
        from code.utils.runtime_verifier import verify_runtime_limit
        result = verify_runtime_limit()
        
        assert result is False
        mock_logger.error.assert_called()