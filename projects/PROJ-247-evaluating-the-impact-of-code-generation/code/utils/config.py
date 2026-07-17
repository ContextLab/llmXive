"""
Configuration constants for the project.
"""
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Classifier Threshold
CLASSIFIER_THRESHOLD = 0.8

# GitHub API
GITHUB_API_TIMEOUT = 30
GITHUB_CLONE_DEPTH = 100

# Metrics
MIN_STARS = 5
MIN_COMMITS_90_DAYS = 1

# Logging
LOG_MAX_BYTES = 1024 * 1024  # 1MB
LOG_BACKUP_COUNT = 5