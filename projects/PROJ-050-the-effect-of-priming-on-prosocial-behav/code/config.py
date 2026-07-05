"""
Configuration module for PROJ-050.
Handles environment variable management and project paths.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Source Paths
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
VALIDATION_DATA_DIR = PROJECT_ROOT / "data" / "validation"
RESULTS_DIR = PROJECT_ROOT / "results"

# Environment Variable Defaults
# TARGET_N: Number of comments to fetch per group (Prime/Control)
TARGET_N = int(os.getenv("TARGET_N", "10000"))

# Minimum required per group to proceed with analysis
MIN_GROUP_SIZE = 4000

# Statistical Parameters
ALPHA = float(os.getenv("ALPHA", "0.05"))
EFFECT_SIZE_D = float(os.getenv("EFFECT_SIZE_D", "0.15"))

# Data Source Configuration
REDDIT_API_BASE = os.getenv("REDDIT_API_BASE", "https://api.pushshift.io/reddit/search/comment/")
TARGET_SUBREDDITS = os.getenv("TARGET_SUBREDDITS", "AskReddit,relationships,socialscience,psychology,dataisbeautiful").split(",")

# Validation Thresholds
KAPPA_THRESHOLD = 0.7
MIN_RATERS = 3

# Performance Constraints
MAX_RUNTIME_HOURS = 4