"""
code/utils/config.py

Configuration definitions including repo lists and thresholds.
"""
import os
from typing import List, Dict, Any

# Prioritized repositories for data acquisition
REPO_LIST: List[str] = [
    "psf/requests",
    "microsoft/vscode",
    "numpy/numpy"
]

# Thresholds and limits
MAX_PRS_PER_REPO: int = 200
MIN_LLM_COUNT_THRESHOLD: int = 10
CONFIDENCE_THRESHOLD: float = 0.6
ERROR_RATE_LIMIT: float = 0.05

# API settings
API_TIMEOUT: int = 30
MAX_RETRIES: int = 5

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration.
    """
    return {
        "repos": REPO_LIST,
        "max_prs_per_repo": MAX_PRS_PER_REPO,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "error_rate_limit": ERROR_RATE_LIMIT
    }
