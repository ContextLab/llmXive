"""
Environment configuration for 1000 Genomes FTP URLs and local paths.

This module centralizes all paths and URLs used throughout the pipeline
to ensure consistency and easy configuration updates.
"""
import os
from pathlib import Path

# Base project directory (assumes code/ is at root or relative to this file)
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
CODE_DIR = _BASE_DIR / "code"
DATA_DIR = _BASE_DIR / "code" / "data"
LOGS_DIR = _BASE_DIR / "code" / "logs"
PAPER_DIR = _BASE_DIR / "paper"

# Data subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FIGURES_DIR = PAPER_DIR / "figures"

# 1000 Genomes FTP Configuration
# Source: https://www.internationalgenome.org/data-portal/data/dataset/1000-genomes-phase-3-vcf
FTP_HOST = "ftp.1000genomes.ebi.ac.uk"
FTP_BASE_URL = "ftp://ftp.1000genomes.ebi.us/vol1/ftp/release/20130502"

# Specific file paths on FTP
MITO_VCF_NAME = "ALL.chrM.phase3_integrated.vcf.gz"
METADATA_PANEL_NAME = "integrated_call_samples_3.20130502.panel"

# Full FTP URLs
MITO_VCF_URL = f"{FTP_BASE_URL}/{MITO_VCF_NAME}"
METADATA_URL = f"{FTP_BASE_URL}/{METADATA_PANEL_NAME}"

# Local file paths for downloaded data
LOCAL_RAW_DIR = RAW_DATA_DIR / "1000_genomes"
LOCAL_MITO_VCF_PATH = LOCAL_RAW_DIR / MITO_VCF_NAME
LOCAL_METADATA_PATH = LOCAL_RAW_DIR / METADATA_PANEL_NAME

# Processed output paths
PROCESSED_DATASET_PATH = PROCESSED_DATA_DIR / "mito_aging_dataset.csv"
MODEL_RESULTS_PATH = PROCESSED_DATA_DIR / "model_results.csv"
ANALYSIS_RESULTS_PATH = PROCESSED_DATA_DIR / "analysis_results.csv"
SENSITIVITY_RESULTS_PATH = PROCESSED_DATA_DIR / "sensitivity_analysis.csv"

# Log file paths
MAIN_LOG_PATH = LOGS_DIR / "pipeline.log"
MODEL_COMPARISON_LOG_PATH = LOGS_DIR / "model_comparison.log"

# Checksum file path
CHECKSUM_PATH = PROCESSED_DATA_DIR / "dataset_checksum.txt"

def ensure_directories():
    """Create all required directories if they do not exist."""
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        LOCAL_RAW_DIR,
        LOGS_DIR,
        FIGURES_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories

# Validation constants
REQUIRED_COLUMNS = {
    "burden": "heteroplasmy_burden",
    "age": "age",
    "sex": "sex",
    "population": "super_population",
    "haplogroup": "haplogroup",
}

# Heteroplasmy threshold (default 1%)
DEFAULT_VAF_THRESHOLD = 0.01

# Depth stratification bins
DEPTH_BINS = {
    "low": (0, 30),
    "medium": (30, 100),
    "high": (100, float("inf")),
}

if __name__ == "__main__":
    # Simple test to verify configuration loading
    print("Environment Configuration Loaded:")
    print(f"  Base Directory: {_BASE_DIR}")
    print(f"  FTP Base URL: {FTP_BASE_URL}")
    print(f"  Mito VCF URL: {MITO_VCF_URL}")
    print(f"  Metadata URL: {METADATA_URL}")
    print(f"  Local Raw Dir: {LOCAL_RAW_DIR}")
    print(f"  Processed Dataset Path: {PROCESSED_DATASET_PATH}")
    
    # Ensure directories exist
    ensure_directories()
    print("  All directories created/verified.")