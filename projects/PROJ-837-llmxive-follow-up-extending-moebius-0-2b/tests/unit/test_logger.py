import pytest
import logging
import sys
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logger import (
    get_logger, setup_project_logger, 
    get_console_only_logger, log_error, log_fatal
)

class TestLogger:
    def test_get_logger_creation(self):
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_setup_project_logger(self):
        logger = setup_project_logger("project_test")
        assert logger is not None
        assert logger.handlers is not None
        assert len(logger.handlers) > 0

    def test_console_only_logger(self):
        logger = get_console_only_logger("console_test")
        assert logger is not None
        
        # Verify it has a console handler
        has_console = any(
            isinstance(h, logging.StreamHandler) and 
            isinstance(h.stream, sys.stdout.__class__)
            for h in logger.handlers
        )
        assert has_console

    def test_log_error(self):
        logger = get_console_only_logger("error_test")
        
        # Capture log output
        import io
        from contextlib import redirect_stderr
        
        f = io.StringIO()
        with redirect_stderr(f):
            log_error(logger, "Test error message")
        
        output = f.getvalue()
        assert "Test error message" in output

    def test_log_fatal(self):
        logger = get_console_only_logger("fatal_test")
        
        import io
        from contextlib import redirect_stderr
        
        f = io.StringIO()
        with redirect_stderr(f):
            log_fatal(logger, "Test fatal message")
        
        output = f.getvalue()
        assert "Test fatal message" in output
        assert "FATAL" in output.upper() or "CRITICAL" in output.upper()

    def test_logger_levels(self):
        logger = get_logger("level_test")
        
        assert logger.level == logging.INFO
        assert logger.isEnabledFor(logging.DEBUG) is False
        assert logger.isEnabledFor(logging.INFO) is True
        assert logger.isEnabledFor(logging.ERROR) is True
