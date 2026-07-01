import logging
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from pathlib import Path

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Configures and returns a standard logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def log_commit_info(logger: logging.Logger, repo_id: str, sha: str, issue_id: str):
    """Logs commit metadata."""
    logger.info(f"Processing {repo_id}: SHA={sha}, Issue={issue_id}")

def log_api_response(logger: logging.Logger, endpoint: str, status_code: int, duration: float):
    """Logs API interaction details."""
    logger.info(f"API Call: {endpoint} -> Status: {status_code}, Duration: {duration:.2f}s")
