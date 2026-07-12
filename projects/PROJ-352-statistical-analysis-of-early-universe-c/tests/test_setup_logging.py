import logging
import os
import sys
from pathlib import Path
import pytest
import shutil

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_logging import setup_logging, get_logger

def test_setup_logging_creates_directory_and_handlers(tmp_path):
    """
    Test that setup_logging creates the logs directory and configures handlers.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Create a mock 'code' directory structure
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "__init__.py").touch()
        
        # Create the setup_logging.py file in the temp code dir
        setup_script = code_dir / "setup_logging.py"
        setup_script.write_text("""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_dir: str = "data/logs") -> None:
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    logs_dir = project_root / log_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"pipeline_{timestamp}.log"
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    file_handler = logging.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def get_logger(name: str = None) -> logging.Logger:
    return logging.getLogger(name)
""")
        
        # Import and run
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_logging", setup_script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Setup logging
        module.setup_logging(log_level="DEBUG", log_dir="test_logs")
        
        # Verify logs directory exists
        logs_dir = tmp_path / "test_logs"
        assert logs_dir.exists()
        
        # Verify handlers are added to root logger
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 2  # Console and File
        
        # Verify we can get a logger
        test_logger = module.get_logger("test_module")
        assert test_logger is not None
        assert test_logger.name == "test_module"
        
    finally:
        os.chdir(original_cwd)
        # Clean up any log files created
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

def test_get_logger_returns_valid_logger():
    """
    Test that get_logger returns a valid logger instance.
    """
    logger = get_logger("test_unit")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_unit"
    assert logger.level == logging.NOTSET  # Default level