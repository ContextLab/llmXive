import os
import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logger
logger = logging.getLogger(__name__)

def setup_logger(name: str = "error_handler") -> logging.Logger:
    """Setup a dedicated logger for error handling."""
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_formatter)
    
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    if not log.handlers:
        log.addHandler(handler)
    return log

def log_error(error_message: str, error_type: str, details: Optional[Dict] = None):
    """Log an error with type and details."""
    logger.error(f"[{error_type}] {error_message}")
    if details:
        logger.debug(f"Details: {json.dumps(details, indent=2)}")

def handle_api_rate_limit(task_id: str, retry_count: int, max_retries: int):
    """Handle API rate limit errors."""
    logger.warning(f"Rate limit hit for task {task_id}. Retry {retry_count}/{max_retries}")

def handle_syntax_error(task_id: str, error: SyntaxError):
    """Handle syntax errors in generated code."""
    logger.error(f"Syntax error for task {task_id}: {error}")

def handle_generation_failure(task_id: str, error: Exception):
    """Handle general generation failures."""
    logger.error(f"Generation failed for task {task_id}: {error}")

def safe_execute_task(func, *args, **kwargs):
    """Execute a function with safe error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in safe_execute_task: {e}")
        traceback.print_exc()
        return None
