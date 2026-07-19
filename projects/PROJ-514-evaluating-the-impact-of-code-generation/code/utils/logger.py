"""
Logging infrastructure for the research pipeline.
Tracks commit SHAs, Issue URLs, and API responses.
"""

import logging
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_commit_info(commit_sha: str, repo_url: str, issue_url: Optional[str] = None):
    """
    Log commit information to a structured log file.
    
    Args:
        commit_sha: Full commit SHA
        repo_url: Repository URL
        issue_url: Optional issue/PR URL
    """
    logger = get_logger("commit_tracking")
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha,
        "repo_url": repo_url,
        "issue_url": issue_url
    }
    
    logger.info(json.dumps(log_entry))

def log_api_response(endpoint: str, status_code: int, data: Any = None):
    """
    Log API interactions for audit trail.
    
    Args:
        endpoint: API endpoint called
        status_code: HTTP status code
        data: Response data (will be truncated for logging)
    """
    logger = get_logger("api_tracking")
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "status_code": status_code,
        "data_preview": str(data)[:200] if data else None
    }
    
    logger.info(json.dumps(log_entry))
