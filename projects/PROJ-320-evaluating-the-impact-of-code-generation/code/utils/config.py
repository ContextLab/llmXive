"""
Configuration management for the research pipeline.
"""
import os
from typing import List, Dict, Any

# Default repository list for data acquisition
DEFAULT_REPOS = [
    'psf/requests',
    'microsoft/vscode',
    'numpy/numpy'
]

# Thresholds and settings
CONFIG = {
    'github_api': {
        'max_retries': 5,
        'backoff_factor': 2.0,
        'rate_limit_threshold': 10,
    },
    'classification': {
        'confidence_threshold': 0.6,
        'min_llm_count_per_repo': 10,
    },
    'audit': {
        'min_threshold': 30,
        'proportion': 0.10,
        'error_rate_threshold': 0.05,
    },
    'complexity': {
        'memory_limit_gb': 6,
    }
}

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration.
    
    Returns:
        Dictionary containing key configuration values
    """
    return {
        'repos': DEFAULT_REPOS,
        'github_api': CONFIG['github_api'],
        'classification': CONFIG['classification'],
        'audit': CONFIG['audit'],
        'complexity': CONFIG['complexity']
    }
