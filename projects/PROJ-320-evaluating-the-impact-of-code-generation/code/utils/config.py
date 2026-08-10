"""
Configuration settings for the llmXive research pipeline.

This module defines all project-wide constants, thresholds, and API settings
to ensure reproducibility and centralized configuration management.
"""

import os
from typing import List, Dict, Any

# Project Root (relative to where scripts are run from, usually project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# ==============================================================================
# Repository List (Target GitHub Repositories for Data Acquisition)
# ==============================================================================
TARGET_REPOS: List[str] = [
    "psf/requests",
    "microsoft/vscode",
    "numpy/numpy"
]

# ==============================================================================
# Classification Thresholds (US1)
# ==============================================================================
# Minimum confidence score required to label a PR as 'llm' or 'human' without flagging
CONFIDENCE_THRESHOLD: float = 0.6

# Minimum number of LLM PRs required in a repo batch before switching repos
MIN_LLM_COUNT_PER_REPO: int = 10

# Maximum number of PRs to fetch per repository
MAX_PRS_PER_REPO: int = 200

# ==============================================================================
# Audit Thresholds (US1 - T019)
# ==============================================================================
# Minimum sample size for manual validation
AUDIT_MIN_THRESHOLD: int = 10

# Proportion of LLM population to sample for audit
AUDIT_PROPORTION: float = 0.10

# Maximum acceptable error rate for automated classification (SC-004)
MAX_ACCEPTABLE_ERROR_RATE: float = 0.05

# ==============================================================================
# Statistical Analysis Settings (US2)
# ==============================================================================
# Significance level (alpha) for hypothesis testing
SIGNIFICANCE_LEVEL: float = 0.05

# Memory threshold (in GB) for falling back to standard metrics in complexity calculation
COMPLEXITY_MEMORY_THRESHOLD_GB: float = 6.0

# ==============================================================================
# GitHub API Settings (US1 - T007, T013)
# ==============================================================================
# GitHub API Base URL
GITHUB_API_BASE_URL: str = "https://api.github.com"

# Maximum number of retries for API requests with exponential backoff
MAX_API_RETRIES: int = 5

# Initial backoff duration in seconds
INITIAL_BACKOFF_SECONDS: float = 1.0

# Maximum backoff duration in seconds
MAX_BACKOFF_SECONDS: float = 60.0

# Global watchdog timer in seconds to prevent CI timeouts
API_WATCHDOG_TIMEOUT_SECONDS: int = 300

# ==============================================================================
# Path Constants
# ==============================================================================
DATA_RAW_DIR: str = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR: str = os.path.join(PROJECT_ROOT, "data", "processed")
REPORTS_FIGURES_DIR: str = os.path.join(PROJECT_ROOT, "reports", "figures")
DATA_AUDIT_DIR: str = os.path.join(PROJECT_ROOT, "data", "audit")

# ==============================================================================
# Random Seed (for reproducibility)
# ==============================================================================
# Default seed value; can be overridden by environment variable or seeds.py
DEFAULT_RANDOM_SEED: int = 42

# ==============================================================================
# Logging Configuration
# ==============================================================================
LOG_FILE_PATH: str = os.path.join(PROJECT_ROOT, "data", "pipeline.log")
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: int = 5

# ==============================================================================
# Feature Flags / Experiment Settings
# ==============================================================================
ENABLE_SECONDARY_DETECTOR: bool = True
ENABLE_COMPLEXITY_ANALYSIS: bool = True
ENABLE_MANUAL_AUDIT: bool = True

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration for logging."""
    return {
        "target_repos": TARGET_REPOS,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "max_prs_per_repo": MAX_PRS_PER_REPO,
        "audit_min_threshold": AUDIT_MIN_THRESHOLD,
        "max_acceptable_error_rate": MAX_ACCEPTABLE_ERROR_RATE,
        "significance_level": SIGNIFICANCE_LEVEL,
        "complexity_memory_threshold_gb": COMPLEXITY_MEMORY_THRESHOLD_GB,
        "default_random_seed": DEFAULT_RANDOM_SEED
    }