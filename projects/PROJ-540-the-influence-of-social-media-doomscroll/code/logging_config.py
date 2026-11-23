import logging
import sys
from pathlib import Path
from config import ensure_directories, load_config

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"LOGCFG: {message}")

def setup_logging(log_file: str = "outputs/analysis.log") -> None:
    """
    Configure logging to both console and file.
    """
    _log_step(f"Setting up logging to {log_file}")
    
    ensure_directories()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    _log_step("Logging configured successfully")

def main() -> None:
    """Main entry point for logging config script."""
    setup_logging()
    logger.info("Logging setup completed")

if __name__ == "__main__":
    main()
