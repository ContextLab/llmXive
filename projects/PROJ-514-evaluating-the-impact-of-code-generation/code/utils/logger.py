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

# Global logger instance to prevent multiple file handlers
_logger_instance: Optional[logging.Logger] = None

def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logging.Logger instance
    """
    global _logger_instance
    
    # If this is the default name, use the singleton instance
    if name == "research_pipeline":
        if _logger_instance is None:
            _logger_instance = _create_logger("research_pipeline")
        return _logger_instance
    
    # For named sub-loggers, use standard hierarchy but ensure file handler exists
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Inherit level from root or default
        logger.setLevel(logging.INFO)
        
        # Add file handler to sub-loggers as well for comprehensive tracking
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

def _create_logger(name: str) -> logging.Logger:
    """Internal helper to create a fully configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
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
    Used to track provenance of code samples (Constitution Principle II).
    
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
    Used to track LLM generation parameters and GitHub API usage (Constitution Principle VI).
    
    Args:
        endpoint: API endpoint called
        status_code: HTTP status code
        data: Response data (will be truncated for logging)
    """
    logger = get_logger("api_tracking")
    
    # Truncate large data objects to prevent log flooding
    data_preview = None
    if data is not None:
        data_str = str(data)
        data_preview = data_str[:200] if len(data_str) > 200 else data_str
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "status_code": status_code,
        "data_preview": data_preview
    }
    
    logger.info(json.dumps(log_entry))