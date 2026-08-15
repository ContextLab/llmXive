"""
Logging Configuration Module.
Sets up logging infrastructure for the project.
"""
import os
import logging
from pathlib import Path

# Ensure logs directory exists
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logger
logger = logging.getLogger("llmXive")
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler(logs_dir / "pipeline.log")
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

def setup_citation_logger():
    """Setup citation validation logger."""
    citation_logger = logging.getLogger("citation_validation")
    citation_logger.setLevel(logging.INFO)
    
    fh = logging.FileHandler(logs_dir / "citation_validation.log")
    fh.setFormatter(formatter)
    citation_logger.addHandler(fh)
    return citation_logger
