"""
Configuration module defining paths, thresholds, and memory limits.

This module centralizes all project-wide constants and configuration
values to ensure consistency across the pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root
# Assumes the script is run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

# --- Paths ---
# Raw data directory (downloaded datasets)
RAW_DIR = DATA_ROOT / "raw"

# Stratified data directory (split subsets)
STRATIFIED_DIR = DATA_ROOT / "stratified"

# Extracted features directory
FEATURES_DIR = DATA_ROOT / "features"

# Results directory (metrics, reports, aggregated outputs)
RESULTS_DIR = DATA_ROOT / "results"

# Processed data (intermediate)
PROCESSED_DIR = DATA_ROOT / "processed"

# --- Memory Limits ---
# Maximum RAM usage in GB before triggering batch processing
MEMORY_LIMIT_GB = 6.0

# --- RANSAC Thresholds ---
# RANSAC thresholds for Fundamental Matrix estimation
RANSAC_REPROJECTION_THRESHOLD = 1.0  # pixels
RANSAC_CONFIDENCE = 0.99             # Probability that RANSAC finds the best model
RANSAC_MAX_ITERATIONS = 2000         # Maximum iterations for RANSAC

# --- Feature Extraction Thresholds ---
# SIFT specific thresholds
SIFT_MIN_CONTRAST = 0.04             # Minimum contrast for SIFT keypoints
SIFT_EDGE_THRESHOLD = 10.0           # Edge threshold for SIFT
# ORB specific thresholds
ORB_MAX_KEYPOINTS = 500              # Maximum number of keypoints for ORB

# --- Stratification Thresholds ---
# Texture and Motion thresholds for stratification
MOTION_SLOW_THRESHOLD = 5.0          # Optical flow magnitude threshold for "Slow"
MOTION_FAST_THRESHOLD = 20.0         # Optical flow magnitude threshold for "Fast"
TEXTURE_LOW_THRESHOLD = 0.5          # Entropy threshold for "Low" texture
TEXTURE_HIGH_THRESHOLD = 1.5         # Entropy threshold for "High" texture

# Minimum sequences per stratum
MIN_STRATUM_SIZE = 50                # Abort if any stratum has < 50 sequences

# --- Helper Functions ---

def get_data_dir() -> Path:
    """Return the root data directory."""
    return DATA_ROOT

def get_raw_dir() -> Path:
    """Return the raw data directory."""
    return RAW_DIR

def get_stratified_dir() -> Path:
    """Return the stratified data directory."""
    return STRATIFIED_DIR

def get_features_dir() -> Path:
    """Return the features directory."""
    return FEATURES_DIR

def get_results_dir() -> Path:
    """Return the results directory."""
    return RESULTS_DIR

def get_processed_dir() -> Path:
    """Return the processed data directory."""
    return PROCESSED_DIR

def get_memory_limit_gb() -> float:
    """Return the memory limit in GB."""
    return MEMORY_LIMIT_GB

def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    dirs = [
        RAW_DIR,
        STRATIFIED_DIR,
        FEATURES_DIR,
        RESULTS_DIR,
        PROCESSED_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "paths": {
            "raw": str(RAW_DIR),
            "stratified": str(STRATIFIED_DIR),
            "features": str(FEATURES_DIR),
            "results": str(RESULTS_DIR),
            "processed": str(PROCESSED_DIR)
        },
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "thresholds": {
            "ransac_reprojection": RANSAC_REPROJECTION_THRESHOLD,
            "ransac_confidence": RANSAC_CONFIDENCE,
            "ransac_max_iter": RANSAC_MAX_ITERATIONS,
            "sift_min_contrast": SIFT_MIN_CONTRAST,
            "sift_edge_threshold": SIFT_EDGE_THRESHOLD,
            "orb_max_keypoints": ORB_MAX_KEYPOINTS,
            "motion_slow": MOTION_SLOW_THRESHOLD,
            "motion_fast": MOTION_FAST_THRESHOLD,
            "texture_low": TEXTURE_LOW_THRESHOLD,
            "texture_high": TEXTURE_HIGH_THRESHOLD,
            "min_stratum_size": MIN_STRATUM_SIZE
        }
    }