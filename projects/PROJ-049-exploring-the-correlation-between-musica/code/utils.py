"""
Utility functions for logging, configuration, and HTTP requests.
"""

import logging
import os
import time
import requests
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

# Configuration
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def setup_logging(name: str = __name__) -> logging.Logger:
    """
    Setup logging configuration with file rotation.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logger instance.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    if logger.handlers:
        return logger
    
    # File handler with rotation
    fh = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary of configuration values.
    """
    return {
        "RANDOM_SEED": os.getenv("RANDOM_SEED", "42"),
        "DATA_PATH": os.getenv("DATA_PATH", "data"),
        "BFI_URL": os.getenv("BFI_URL", ""),
        "LASTFM_URL": os.getenv("LASTFM_URL", ""),
    }

def safe_http_request(url: str, timeout: int = 30) -> Optional[requests.Response]:
    """
    Perform a safe HTTP request with timeout and error handling.
    
    Args:
        url: Target URL.
        timeout: Request timeout in seconds.
        
    Returns:
        Response object or None if failed.
    """
    logger = setup_logging(__name__)
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        logger.error(f"Request to {url} timed out.")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Request failed for {url}: {e}")
        return None

def download_file(url: str, dest_path: Path, timeout: int = 30) -> bool:
    """
    Download a file from a URL.
    
    Args:
        url: Source URL.
        dest_path: Destination path.
        timeout: Request timeout.
        
    Returns:
        True if successful, False otherwise.
    """
    logger = setup_logging(__name__)
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded {url} to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
