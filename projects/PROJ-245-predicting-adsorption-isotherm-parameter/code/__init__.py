"""
llmXive Adsorption Isotherm Pipeline - Root Package
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logging.info(f"Loaded environment variables from {env_path}")
else:
    logging.debug("No .env file found, proceeding with system environment.")

# Configure root logger
def setup_logging(log_level: str = "INFO", log_file: str = "logs/pipeline.log"):
    """
    Configure the root logger with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file relative to project root
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_level_enum = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level_enum)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level_enum)
    console_handler.setFormatter(simple_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_enum)
    
    # Avoid adding handlers multiple times if this is called repeatedly
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

# Initialize logging with default settings
setup_logging()

__version__ = "0.1.0"
