"""
Unit tests for src/brainnet/utils.py
"""
import logging
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.brainnet.utils import set_seed, setup_logging, profile_memory


class TestSetSeed:
    def test_set_seed_deterministic(self):
        """Test that set_seed produces deterministic results."""
        set_seed(42)
        val1 = np.random.rand()
        
        set_seed(42)
        val2 = np.random.rand()
        
        assert val1 == val2, "Seed reset should produce same random values"

    def test_set_seed_different_values(self):
        """Test that different seeds produce different results."""
        set_seed(42)
        val1 = np.random.rand()
        
        set_seed(123)
        val2 = np.random.rand()
        
        assert val1 != val2, "Different seeds should produce different values"


class TestSetupLogging:
    def test_console_handler_exists(self):
        """Test that console handler is added."""
        logger = setup_logging(level=logging.INFO, name="test_console")
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_file_handler_exists(self):
        """Test that file handler is added when log_file is provided."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            log_path = tmp.name
        
        try:
            logger = setup_logging(level=logging.INFO, log_file=log_path, name="test_file")
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_logger_name(self):
        """Test that logger has the correct name."""
        logger = setup_logging(name="custom_name")
        assert logger.name == "custom_name"

    def test_duplicate_handlers_prevention(self):
        """Test that calling setup_logging twice doesn't duplicate handlers."""
        logger = setup_logging(level=logging.INFO, name="test_dup")
        initial_count = len(logger.handlers)
        
        setup_logging(level=logging.INFO, name="test_dup")
        
        assert len(logger.handlers) == initial_count, "Handlers should not duplicate"


class TestProfileMemory:
    def test_profile_memory_returns_result(self):
        """Test that decorated function returns the correct result."""
        @profile_memory()
        def add_numbers(a, b):
            return a + b
        
        result = add_numbers(2, 3)
        assert result == 5

    def test_profile_memory_logs_info(self):
        """Test that memory profiling logs output."""
        import io
        from contextlib import redirect_stderr
        
        log_stream = io.StringIO()
        test_logger = logging.getLogger("test_mem")
        test_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter('%(message)s'))
        test_logger.addHandler(handler)
        
        @profile_memory(log=test_logger)
        def dummy_func():
            x = np.random.rand(1000, 1000)
            return x.sum()
        
        dummy_func()
        
        log_contents = log_stream.getvalue()
        assert "Starting memory profile" in log_contents
        assert "Peak memory" in log_contents
        assert "Finished dummy_func" in log_contents

    def test_profile_memory_no_func_arg(self):
        """Test decorator usage with parentheses but no arguments."""
        @profile_memory()
        def simple_func():
            return 42
        
        assert simple_func() == 42