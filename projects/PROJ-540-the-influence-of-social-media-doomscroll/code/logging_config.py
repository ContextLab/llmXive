import logging
import sys
from pathlib import Path
from config import ensure_directories, load_config

def setup_logging(log_file: str = "outputs/analysis.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configure the logging infrastructure to write to a specific file and stdout.
    
    Args:
        log_file: Relative path to the log file from project root.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        The root logger instance configured with the file and console handlers.
    """
    # Load config to ensure directories exist before logging starts
    try:
        config = load_config()
        ensure_directories(config)
    except Exception as e:
        # Fallback if config loading fails, try to ensure basic structure
        Path("outputs").mkdir(parents=True, exist_ok=True)
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in interactive sessions
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    try:
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler for {log_path}: {e}", file=sys.stderr)

    # Console Handler (always output to stdout for visibility)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Output file: {log_path.absolute()}")
    return logger