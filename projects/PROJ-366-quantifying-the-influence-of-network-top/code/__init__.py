"""
Thermal conductivity pipeline package.
"""
import logging
import sys
from pathlib import Path

# Configure logging
def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging infrastructure.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create log directory
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add file handler for pipeline stages
    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)

# Initialize logging on import
setup_logging()
