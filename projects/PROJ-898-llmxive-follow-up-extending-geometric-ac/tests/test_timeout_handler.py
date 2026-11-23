"""
Unit tests for the timeout handler module (T017).

Tests verify:
1. Timeout enforcement works correctly
2. Trial log entries are recorded with correct flags
3. Timeout reason is set to 'step_limit'
4. Configuration is read correctly from config.yaml
"""
import os
import sys
import time
import tempfile
import shutil
import csv
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from timeout_handler import TimeoutHandler, TimeoutResult, TimeoutError
from config import load_config, ExperimentConfig
from trial_log_schema import TrialLogger


class TestTimeoutHandler:
    """Test suite for TimeoutHandler class."""
    
    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary directory for test results."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock experiment configuration."""
        config = Mock(spec=ExperimentConfig)
        config.timeout_limits.solver_step_seconds = 2
        config.paths.results = "data/results"
        return config
    
    @pytest.fixture
    def timeout_handler(self, mock_config):
        """Create a TimeoutHandler instance with mock config."""
        return TimeoutHandler(mock_config)
    
    def test_timeout_result_dataclass(self):
        """Test TimeoutResult dataclass creation."""
        result = TimeoutResult(
            success=True,
            result={"data": "test"},
            timeout_triggered=False,
            elapsed_seconds=1.5,
            error_message=None
        )
        
        assert result.success is True
        assert result.result == {"data": "test"}
        assert result.timeout_triggered is False
        assert result.elapsed_seconds == 1.5
        assert result.error_message is None
    
    def test_execute_step_success(self, timeout_handler, temp_results_dir):
        """Test successful execution without timeout."""
        # Create a quick solver function
        def quick_solver():
            time.sleep(0.1)
            return {"status": "success"}
        
        # Create trial logger
        log_path = os.path.join(temp_results_dir, "trial_log.csv")
        trial_logger = TrialLogger(log_file=log_path)
        
        result = timeout_handler.execute_step(
            quick_solver,
            trial_id=1,
            step=1,
            logger=trial_logger
        )
        
        assert result.success is True
        assert result.timeout_triggered is False
        assert result.result == {"status": "success"}
        assert result.elapsed_seconds < 1.0
    
    def test_execute_step_timeout(self, timeout_handler, temp_results_dir):
        """Test execution that triggers timeout."""
        # Create a slow solver function
        def slow_solver():
            time.sleep(10)  # Much longer than timeout
            return {"status": "should_not_reach"}
        
        # Create trial logger
        log_path = os.path.join(temp_results_dir, "trial_log.csv")
        trial_logger = TrialLogger(log_file=log_path)
        
        result = timeout_handler.execute_step(
            slow_solver,
            trial_id=2,
            step=1,
            logger=trial_logger
        )
        
        assert result.success is False
        assert result.timeout_triggered is True
        assert result.error_message is not None
        assert "timeout" in result.error_message.lower()
    
    def test_timeout_logged_with_correct_flags(self, timeout_handler, temp_results_dir):
        """Verify timeout events are logged with correct flags."""
        def slow_solver():
            time.sleep(10)
            return {}
        
        log_path = os.path.join(temp_results_dir, "trial_log.csv")
        trial_logger = TrialLogger(log_file=log_path)
        
        timeout_handler.execute_step(
            slow_solver,
            trial_id=3,
            step=1,
            logger=trial_logger
        )
        
        # Verify log file contents
        assert os.path.exists(log_path)
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        entry = rows[0]
        
        assert entry['trial_id'] == '3'
        assert entry['step'] == '1'
        assert entry['success'] == 'False'
        assert entry['timeout'] == 'True'
        assert entry['timeout_reason'] == 'step_limit'
        assert entry['infeasible'] == 'False'
    
    def test_timeout_from_config(self):
        """Test that timeout limit is read from config."""
        # This test assumes config.yaml has timeout_limits.solver_step_seconds
        # In a real scenario, we'd load the actual config
        config = Mock(spec=ExperimentConfig)
        config.timeout_limits.solver_step_seconds = 5
        
        handler = TimeoutHandler(config)
        assert handler.get_timeout_limit() == 5
    
    def test_exception_handling(self, timeout_handler, temp_results_dir):
        """Test handling of non-timeout exceptions."""
        def failing_solver():
            raise ValueError("Solver failed")
        
        log_path = os.path.join(temp_results_dir, "trial_log.csv")
        trial_logger = TrialLogger(log_file=log_path)
        
        result = timeout_handler.execute_step(
            failing_solver,
            trial_id=4,
            step=1,
            logger=trial_logger
        )
        
        assert result.success is False
        assert result.timeout_triggered is False
        assert "Solver failed" in result.error_message
    
    def test_get_timeout_limit(self, timeout_handler):
        """Test get_timeout_limit method."""
        expected_timeout = timeout_handler.config.timeout_limits.solver_step_seconds
        assert timeout_handler.get_timeout_limit() == expected_timeout


class TestTimeoutIntegration:
    """Integration tests for timeout functionality."""
    
    def test_full_timeout_workflow(self):
        """Test complete workflow with timeout enforcement."""
        # Create a temporary directory for test results
        temp_dir = tempfile.mkdtemp()
        try:
            # Setup config mock
            config = Mock(spec=ExperimentConfig)
            config.timeout_limits.solver_step_seconds = 1
            config.paths.results = temp_dir
            
            handler = TimeoutHandler(config)
            log_path = os.path.join(temp_dir, "trial_log.csv")
            trial_logger = TrialLogger(log_file=log_path)
            
            # Run a timeout scenario
            def slow_task():
                time.sleep(5)
                return {}
            
            result = handler.execute_step(
                slow_task,
                trial_id=100,
                step=5,
                logger=trial_logger
            )
            
            # Verify results
            assert not result.success
            assert result.timeout_triggered
            
            # Verify log file
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) >= 1
            last_entry = rows[-1]
            assert last_entry['trial_id'] == '100'
            assert last_entry['step'] == '5'
            assert last_entry['timeout'] == 'True'
            assert last_entry['timeout_reason'] == 'step_limit'
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
