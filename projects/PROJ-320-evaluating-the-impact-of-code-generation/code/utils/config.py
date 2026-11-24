"""
Configuration management for the project.
"""
import os
from typing import List, Dict, Any
from pathlib import Path

# ----------------------------------------------------------------------
# Core configuration constants required by task T005
# ----------------------------------------------------------------------

# Prioritized list of repositories to fetch PRs from.
# This list is used throughout the pipeline (e.g., fetch_github.py)
# and must be importable as `REPOS`.
REPOS: List[str] = [
    "psf/requests",
    "microsoft/vscode",
    "numpy/numpy"
]

# API limits configuration – can be extended in the future.
# For now we expose the most common limits needed by the fetcher.
API_LIMITS: Dict[str, Any] = {
    # GitHub API rate limit (requests per hour).  The actual limit
    # depends on authentication; this is a sensible default for
    # unauthenticated requests.
    "rate_limit_per_hour": 60,
    # Maximum number of PRs to fetch per repository in a single batch.
    "batch_size": 200,
    # Maximum number of retries on rate‑limit or transient errors.
    "max_retries": 3,
}

# Classification thresholds used by the LLM detection logic.
# LLM_CONFIDENCE is the confidence score below which a PR is
# considered ambiguous and flagged for manual audit.
LLM_CONFIDENCE: float = 0.6

# ----------------------------------------------------------------------
# Existing configuration handling (preserved from original file)
# ----------------------------------------------------------------------

# Default configuration
_CONFIG = {
    "repos": REPOS,
    "api": {
        "token": os.getenv("GITHUB_TOKEN", ""),
        "base_url": "https://api.github.com"
    },
    "thresholds": {
        "min_llm_count": 10,
        "confidence_threshold": LLM_CONFIDENCE,
        "error_rate_threshold": 0.05
    },
    "audit": {
        "min_sample_size": 10,
        "scaling_factor": 0.1
    },
    "complexity": {
        "memory_threshold_gb": 6,
        "chunk_size_lines": 1000
    }
}

def get_path(key: str) -> Path:
    """Get a path from config (placeholder for future path config)."""
    return Path(".")

def get_repo_list() -> List[str]:
    """Returns the list of prioritized repositories."""
    return _CONFIG.get("repos", [])

def get_api_settings() -> Dict[str, Any]:
    """Returns API settings."""
    return _CONFIG.get("api", {})

def get_classification_thresholds() -> Dict[str, float]:
    """Returns classification thresholds."""
    return _CONFIG.get("thresholds", {})

def get_audit_settings() -> Dict[str, Any]:
    """Returns audit settings."""
    return _CONFIG.get("audit", {})

def get_complexity_settings() -> Dict[str, Any]:
    """Returns complexity settings."""
    return _CONFIG.get("complexity", {})

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration."""
    return {
        "repos": len(get_repo_list()),
        "api_configured": bool(get_api_settings().get("token")),
        "thresholds": get_classification_thresholds()
    }

def main():
    print(f"Repos: {get_repo_list()}")
    print(f"API Settings: {get_api_settings()}")

if __name__ == "__main__":
    main()