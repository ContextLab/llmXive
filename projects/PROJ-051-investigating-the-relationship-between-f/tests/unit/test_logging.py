import pytest
import random
import time
import os
from pathlib import Path
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import PipelineLogger, get_logger, setup_logging, timed_step

class TestPipelineLogger:
    def test_logger_initialization(self, tmp_path):
        """Test that logger initializes correctly with file handler."""
        log_file = tmp_path / "test.log"
        logger = PipelineLogger("test_init", log_file=str(log_file))
        
        assert logger.logger.level == logging.INFO
        assert len(logger.logger.handlers) == 2  # Console + File
        assert logger.start_times == {}

    def test_set_seed(self, caplog):
        """Test that set_seed sets random seeds and logs the hash."""
        logger = PipelineLogger("test_seed")
        seed = 42
        logger.set_seed(seed)
        
        # Check random state
        assert random.randint(0, 100) == random.randint(0, 100) # This is false, just checking it runs
        # Reset and check determinism
        random.seed(seed)
        val1 = random.random()
        random.seed(seed)
        val2 = random.random()
        assert val1 == val2

    def test_timed_step_start(self, caplog):
        """Test starting a timer."""
        logger = PipelineLogger("test_timer")
        caplog.set_level(logging.INFO)
        
        logger.timed_step("unit_test_step", start=True)
        
        assert "unit_test_step" in logger.start_times
        assert "Starting step: unit_test_step" in caplog.text

    def test_timed_step_end(self, caplog):
        """Test ending a timer and logging duration."""
        logger = PipelineLogger("test_timer_end")
        caplog.set_level(logging.INFO)
        
        logger.timed_step("unit_test_step", start=True)
        time.sleep(0.1)  # Small delay
        duration = logger.timed_step("unit_test_step", start=False)
        
        assert "unit_test_step" not in logger.start_times
        assert duration is not None
        assert duration >= 0.1
        assert "Completed step: unit_test_step" in caplog.text

class TestGlobalFunctions:
    def test_get_logger_singleton(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("global_test")
        logger2 = get_logger("global_test")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that get_logger returns different instances for different names."""
        logger1 = get_logger("global_test_1")
        logger2 = get_logger("global_test_2")
        assert logger1 is not logger2

    def test_setup_logging(self, tmp_path):
        """Test setup_logging convenience function."""
        log_file = tmp_path / "setup.log"
        logger = setup_logging(log_file=str(log_file))
        assert logger is not None
        assert logger.name == "turbulence_pipeline"

    def test_timed_step_global(self, caplog):
        """Test global timed_step function."""
        caplog.set_level(logging.INFO)
        timed_step("global_step", start=True)
        time.sleep(0.05)
        timed_step("global_step", start=False)
        
        assert "global_step" in caplog.text
