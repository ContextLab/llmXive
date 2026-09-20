"""
Logging configuration for the project.
"""
import logging
import sys
from pathlib import Path

from config import ensure_directories, load_config

def setup_logging(log_file: str = 'outputs/analysis.log') -> None:
    """
    Configures logging to file and console.

    Args:
        log_file: Path to the log file.
    """
    ensure_directories()
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout)
    ]
    
    logging.basicConfig(
        level=logging.INFO,
        format=format_str,
        handlers=handlers
    )

def main():
    """Main entry point."""
    setup_logging()
    logging.info("Logging configured successfully.")

if __name__ == '__main__':
    main()
