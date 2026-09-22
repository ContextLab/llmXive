"""
config.py

Centralized configuration management for the project.
Defines paths, thresholds, and API settings.
"""
import os
from typing import List, Dict, Any
from pathlib import Path

# Project root is assumed to be the parent of the 'code' directory
# If running as a script, we try to infer it, otherwise we use a default
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if not (_PROJECT_ROOT / "code").exists():
    # Fallback if structure is different or running in a test environment
    _PROJECT_ROOT = Path.cwd()

def get_path(relative_path: str) -> Path:
    """
    Resolve a relative path from the project root.
    
    Args:
        relative_path: Path relative to the project root.
        
    Returns:
        Absolute Path object.
    """
    return _PROJECT_ROOT / relative_path

def get_repo_list() -> List[str]:
    """
    Get the list of prioritized repositories to analyze.
    
    Returns:
        List of "owner/repo" strings.
    """
    return [
        "psf/requests",
        "microsoft/vscode",
        "numpy/numpy",
        "pandas-dev/pandas",
        "scikit-learn/scikit-learn"
    ]

def get_api_settings() -> Dict[str, Any]:
    """
    Get GitHub API settings including rate limit handling.
    
    Returns:
        Dictionary with API configuration.
    """
    return {
        "base_url": "https://api.github.com",
        "timeout": 30,
        "max_retries": 5,
        "backoff_factor": 2,
        "rate_limit_buffer": 10, # Leave this many requests in the buffer
    }

def get_classification_thresholds() -> Dict[str, float]:
    """
    Get thresholds for classification logic.
    
    Returns:
        Dictionary with confidence thresholds.
    """
    return {
        "min_confidence_llm": 0.8,
        "min_confidence_human": 0.6,
        "ambiguous_threshold": 0.6, # Below this is flagged
        "detector_score_threshold": 0.5,
    }

def get_audit_settings() -> Dict[str, Any]:
    """
    Get settings for manual validation and audit.
    
    Returns:
        Dictionary with audit configuration.
    """
    return {
        "min_sample_size": 30,
        "percentage_sample": 0.10, # 10% of LLM dataset
        "error_rate_threshold": 0.05, # 5% max error rate
    }

def get_complexity_settings() -> Dict[str, Any]:
    """
    Get settings for complexity analysis.
    
    Returns:
        Dictionary with complexity configuration.
    """
    return {
        "memory_threshold_mb": 6000, # 6GB threshold for fallback
        "chunk_size": 100, # PRs to process in a batch
    }

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of all configuration settings for logging/reporting.
    
    Returns:
        Dictionary containing all config sections.
    """
    return {
        "repos": get_repo_list(),
        "api": get_api_settings(),
        "classification": get_classification_thresholds(),
        "audit": get_audit_settings(),
        "complexity": get_complexity_settings(),
    }

def main():
    """Print current configuration summary."""
    import json
    print(json.dumps(get_config_summary(), indent=2))

if __name__ == "__main__":
    main()
