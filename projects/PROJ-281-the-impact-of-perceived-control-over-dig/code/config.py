"""
Global configuration, random seeds, and path constants.

This module defines all configuration parameters used throughout the project,
including file paths, model settings, and processing thresholds.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Output files
RAW_DATA_PATH = RAW_DATA_DIR / "social_media.csv"
PREPROCESSED_TEXT_PATH = PROCESSED_DATA_DIR / "preprocessed_text.csv"
SCORING_RESULTS_PATH = PROCESSED_DATA_DIR / "scoring_results.csv"
PROXY_RESULTS_PATH = PROCESSED_DATA_DIR / "proxy_results.csv"  # T026 output
FINAL_ANALYSIS_PATH = PROCESSED_DATA_DIR / "final_analysis.csv"
ANALYSIS_RESULTS_PATH = PROCESSED_DATA_DIR / "analysis_results.json"
NORMALITY_CHECK_PATH = PROCESSED_DATA_DIR / "normality_check.json"
COVERAGE_REPORT_PATH = PROCESSED_DATA_DIR / "coverage_report.json"
CORRELATION_PLOT_PATH = PROCESSED_DATA_DIR / "correlation_plot.png"

# Model configuration
ANXIETY_MODEL_NAME = "cardiffnlp/twitter-roberta-base-emotion"
CONFIDENCE_THRESHOLD = 0.6
LANGUAGE_CONFIDENCE_THRESHOLD = 0.8

# Processing thresholds
TEXT_MIN_LENGTH = 10
TEXT_MAX_LENGTH = 280
POSTS_PER_USER_MIN = 1

# Random seed for reproducibility
RANDOM_SEED = 42

# Performance constraints
MAX_RUNTIME_HOURS = 6
MAX_MEMORY_GB = 7

# Configuration dictionary
CONFIG: Dict[str, Any] = {
    'paths': {
        'project_root': PROJECT_ROOT,
        'data_dir': DATA_DIR,
        'raw_data_dir': RAW_DATA_DIR,
        'processed_data_dir': PROCESSED_DATA_DIR,
        'raw_data_path': RAW_DATA_PATH,
        'preprocessed_text_path': PREPROCESSED_TEXT_PATH,
        'scoring_results_path': SCORING_RESULTS_PATH,
        'proxy_results_path': PROXY_RESULTS_PATH,
        'final_analysis_path': FINAL_ANALYSIS_PATH,
        'analysis_results_path': ANALYSIS_RESULTS_PATH,
        'normality_check_path': NORMALITY_CHECK_PATH,
        'coverage_report_path': COVERAGE_REPORT_PATH,
        'correlation_plot_path': CORRELATION_PLOT_PATH,
    },
    'models': {
        'anxiety_model_name': ANXIETY_MODEL_NAME,
    },
    'thresholds': {
        'confidence_threshold': CONFIDENCE_THRESHOLD,
        'language_confidence_threshold': LANGUAGE_CONFIDENCE_THRESHOLD,
        'text_min_length': TEXT_MIN_LENGTH,
        'text_max_length': TEXT_MAX_LENGTH,
        'posts_per_user_min': POSTS_PER_USER_MIN,
    },
    'performance': {
        'random_seed': RANDOM_SEED,
        'max_runtime_hours': MAX_RUNTIME_HOURS,
        'max_memory_gb': MAX_MEMORY_GB,
    }
}

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

__all__ = [
    'PROJECT_ROOT',
    'DATA_DIR',
    'RAW_DATA_DIR',
    'PROCESSED_DATA_DIR',
    'RAW_DATA_PATH',
    'PREPROCESSED_TEXT_PATH',
    'SCORING_RESULTS_PATH',
    'PROXY_RESULTS_PATH',
    'FINAL_ANALYSIS_PATH',
    'ANALYSIS_RESULTS_PATH',
    'NORMALITY_CHECK_PATH',
    'COVERAGE_REPORT_PATH',
    'CORRELATION_PLOT_PATH',
    'ANXIETY_MODEL_NAME',
    'CONFIDENCE_THRESHOLD',
    'LANGUAGE_CONFIDENCE_THRESHOLD',
    'TEXT_MIN_LENGTH',
    'TEXT_MAX_LENGTH',
    'POSTS_PER_USER_MIN',
    'RANDOM_SEED',
    'MAX_RUNTIME_HOURS',
    'MAX_MEMORY_GB',
    'CONFIG'
]
