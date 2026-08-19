"""
Configuration management for the cross-modal neural prediction error pipeline.

This module defines global constants, paths, and helper functions for the project.
It strictly enforces real data sources (OpenNeuro) and prohibits synthetic data generation.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
STATE_DIR = PROJECT_ROOT / "state"
PROJECTS_DIR = STATE_DIR / "projects"
DOCS_DIR = PROJECT_ROOT / "docs"
FIGURES_DIR = DATA_DIR / "figures"

# OpenNeuro Dataset IDs (Real Data Only)
# Auditory Oddball: ds000246
# Visual Oddball: ds000117
DATASET_IDS = {
    "auditory": "ds000246",
    "visual": "ds000117"
}

# Validation Thresholds
MIN_SAMPLING_RATE_HZ = 500
MIN_ODDBALL_TRIALS = 100
MIN_STANDARD_TRIALS = 300

# Time Windows (ms)
AUDITORY_TIME_WINDOW = (0.050, 0.250)  # 50-250ms for MMN
VISUAL_TIME_WINDOW = (0.150, 0.350)    # 150-350ms for VMM

# Filter Parameters
BANDPASS_FILTER_PARAMS = {
    "low_cut": 0.1,
    "high_cut": 40.0,
    "filt_type": "fir",
    "order": "auto"
}

# ICA Parameters
ICA_REJECTION_CRITERIA = {
    "method": "correlation",
    "eog_channels": ["EOG061", "EOG062"],
    "threshold": 0.95
}

# Random Seed for reproducibility
RANDOM_SEED = 42

# Output Paths
CLEANED_DATA_PATH = DATA_PROCESSED_DIR / "cleaned_data.fif"
METRICS_SUMMARY_PATH = DATA_RESULTS_DIR / "metrics_summary.json"
SENSITIVITY_ANALYSIS_PATH = DATA_RESULTS_DIR / "sensitivity_analysis.csv"
BH_CORRECTED_PVALUES_PATH = DATA_RESULTS_DIR / "bh_corrected_pvalues.json"
RELIABILITY_PATH = DATA_RESULTS_DIR / "reliability.json"
SC002_COMPLIANCE_PATH = DATA_RESULTS_DIR / "sc002_compliance.json"
FINAL_REPORT_PATH = DATA_RESULTS_DIR / "final_report.md"
STATE_PROJECT_FILE = PROJECTS_DIR / "PROJ-779-cross-modal-comparison-of-neural-predict.yaml"

def ensure_directories() -> None:
    """
    Create all necessary project directories if they do not exist.
    """
    dirs = [
        CODE_DIR,
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        FIGURES_DIR,
        STATE_DIR,
        PROJECTS_DIR,
        DOCS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config() -> Dict[str, Any]:
    """
    Return a dictionary containing all current configuration constants.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "dataset_ids": DATASET_IDS,
        "min_sampling_rate_hz": MIN_SAMPLING_RATE_HZ,
        "min_oddball_trials": MIN_ODDBALL_TRIALS,
        "min_standard_trials": MIN_STANDARD_TRIALS,
        "auditory_time_window": AUDITORY_TIME_WINDOW,
        "visual_time_window": VISUAL_TIME_WINDOW,
        "bandpass_filter_params": BANDPASS_FILTER_PARAMS,
        "ica_rejection_criteria": ICA_REJECTION_CRITERIA,
        "random_seed": RANDOM_SEED,
        "output_paths": {
            "cleaned_data": str(CLEANED_DATA_PATH),
            "metrics_summary": str(METRICS_SUMMARY_PATH),
            "sensitivity_analysis": str(SENSITIVITY_ANALYSIS_PATH),
            "bh_corrected_pvalues": str(BH_CORRECTED_PVALUES_PATH),
            "reliability": str(RELIABILITY_PATH),
            "sc002_compliance": str(SC002_COMPLIANCE_PATH),
            "final_report": str(FINAL_REPORT_PATH),
            "state_project": str(STATE_PROJECT_FILE)
        }
    }