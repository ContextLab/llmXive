"""
Configuration management for the llmXive project: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG.

This module manages paths (raw, processed, results) and configuration parameters (thresholds, epoch length).
It implements the ratified design decision for 10-second epochs (docs/decisions/epoch_length.md).
"""
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
# Ensure these paths align with plan.md structure
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
CONFIG_DIR = PROJECT_ROOT / "data" / "config"
FIGURES_DIR = PROJECT_ROOT / "figures"
STATE_DIR = PROJECT_ROOT / "state"
SPECS_DIR = PROJECT_ROOT / "specs"

# Parameters (Ratified Decisions)
# Deviation from FR-002 (2s): 10s epochs selected for better spectral resolution in coherence estimation.
# Reference: docs/decisions/epoch_length.md
EPOCH_LENGTH_SEC = 10

# Signal Processing Parameters
BANDPASS_FREQS = (1, 40)  # Hz: Bandpass filter range
ARTIFACT_REJECTION_THRESHOLD = 0.5  # 50% of epochs allowed to be artifacts before rejection
SNR_THRESHOLD_DB = 10.0  # Minimum Signal-to-Noise Ratio in dB

# Network Analysis Parameters
CONNECTIVITY_METHOD = "coherence"  # Welch method for coherence calculation
NETWORK_THRESHOLD = 0.2  # Threshold for binarizing weighted networks (example default)

# Cognitive Data Validation (FR-007)
VALID_COGNITIVE_INSTRUMENTS = ["MMSE", "MoCA"]

# Statistical Parameters
CORRECTION_METHOD = "fdr_bh"  # Benjamini-Hochberg FDR correction
SIGNIFICANCE_LEVEL = 0.05

def ensure_dirs():
    """
    Create all required data directories if they don't exist.
    This function is critical for pipeline initialization.
    """
    directories = [
        RAW_DATA_DIR, 
        PROCESSED_DATA_DIR, 
        QUALITY_DIR, 
        RESULTS_DIR, 
        CONFIG_DIR, 
        FIGURES_DIR, 
        STATE_DIR,
        SPECS_DIR
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
    
    return directories