"""
Unit tests for data/utils.py functionality.
"""
import os
import logging
import tempfile
import pytest
from unittest.mock import patch

# Import the module under test
# Assuming the project root is in the PYTHONPATH
from code.data.utils import (
    set_seed, 
    get_seed, 
    get_seed_hash, 
    setup_logging, 
    ensure_seed_initialized,
    _get_log_level_from_env,
    DEFAULT_SEED,
    LOG_LEVEL_ENV_VAR
)


class TestSeedManagement:
    def test_set_seed_default(self):
        """Test that set_seed uses DEFAULT_SEED when no argument provided."""
        # Reset global state first
        import code.data.utils as utils
        utils._global_seed = None
        utils._seed_hash = None

        seed = set_seed()
        assert seed == DEFAULT_SEED
        assert get_seed() == DEFAULT_SEED
        assert get_seed_hash() is not None
        assert len(get_seed_hash()) == 16

    def test_set_seed_explicit(self):
        """Test setting an explicit seed."""
        import code.data.utils as utils
        utils._global_seed = None
        utils._seed_hash = None

        test_seed = 12345
        seed = set_seed(test_seed)
        assert seed == test_seed
        assert get_seed() == test_seed

    def test_seed_hash_consistency(self):
        """Test that the same seed always produces the same hash."""
        import code.data.utils as utils
        utils._global_seed = None
        utils._seed_hash = None

        seed1 = set_seed(999)
        hash1 = get_seed_hash()

        utils._global_seed = None
        utils._seed_hash = None

        seed2 = set_seed(999)
        hash2 = get_seed_hash()

        assert hash1 == hash2


class TestLoggingInfrastructure:
    def test_setup_logging_console_only(self):
        """Test setup_logging with no file argument."""
        logger = setup_logging(level=logging.DEBUG, name="test_console")
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_with_file(self):
        """Test setup_logging creates a file handler."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            log_path = tmp.name

        try:
            logger = setup_logging(level=logging.INFO, log_file=log_path, name="test_file")
            assert len(logger.handlers) == 2
            
            # Check that one handler is a FileHandler
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
            assert file_handlers[0].baseFilename == log_path
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_setup_logging_env_level(self):
        """Test that logging level is read from environment variable."""
        with patch.dict(os.environ, {LOG_LEVEL_ENV_VAR: "WARNING"}):
            level = _get_log_level_from_env()
            assert level == logging.WARNING

    def test_setup_logging_env_default(self):
        """Test that default logging level is INFO if env var is missing/invalid."""
        with patch.dict(os.environ, {}, clear=True):
            level = _get_log_level_from_env()
            assert level == logging.INFO

        with patch.dict(os.environ, {LOG_LEVEL_ENV_VAR: "INVALID_LEVEL"}):
            level = _get_log_level_from_env()
            assert level == logging.INFO

    def test_setup_logging_duplicate_call(self):
        """Test that calling setup_logging multiple times doesn't duplicate handlers."""
        logger = setup_logging(level=logging.INFO, name="test_dup")
        initial_count = len(logger.handlers)
        
        # Call again with different level
        logger2 = setup_logging(level=logging.DEBUG, name="test_dup")
        
        assert logger is logger2
        assert len(logger2.handlers) == initial_count

class TestEnsureSeed:
    def test_ensure_seed_initialized_already_set(self):
        """Test ensure_seed_initialized when seed is already set."""
        import code.data.utils as utils
        utils._global_seed = 555
        
        seed = ensure_seed_initialized()
        assert seed == 555

    def test_ensure_seed_initialized_not_set(self):
        """Test ensure_seed_initialized when seed is not set."""
        import code.data.utils as utils
        utils._global_seed = None
        utils._seed_hash = None
        
        seed = ensure_seed_initialized()
        assert seed == DEFAULT_SEED
        assert get_seed() == DEFAULT_SEED