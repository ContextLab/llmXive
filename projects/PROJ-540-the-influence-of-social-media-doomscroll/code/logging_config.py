import logging
import sys
from pathlib import Path
from config import ensure_directories, load_config

def setup_logging(log_file: str = 'outputs/analysis.log') -> None:
    """Configure logging to file and console."""
    log_path = Path(log_file)
    ensure_directories(log_path)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)

if __name__ == "__main__":
    setup_logging()
