"""
Configuration settings for the Chemo Biomarker Discovery project.

This module defines paths, random seeds, thresholds, and system limits.
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Results directories
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_META_ANALYSIS_DIR = RESULTS_DIR / "meta_analysis"

# State and specs
STATE_DIR = PROJECT_ROOT / "state"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-chemo-biomarker-discovery"

# Random seed for reproducibility
RANDOM_SEED = 42

# Statistical thresholds
FDR_THRESHOLD = 0.05
LOG2FC_THRESHOLD = 1.0
MAX_VARIANCE_GENES = 1000  # Maximum genes to consider based on variance

# System limits
TIMEOUT_HOURS = 5
MAX_MEMORY_GB = 16
CPU_CORES = os.cpu_count() or 4

# TCGA configuration
TCGA_HUGGINGFACE_ORG = "tcga-data"
MIN_TCGA_TUMOR_TYPES = 3

# GEO configuration
GEO_DATASETS = ["GSE25055", "GSE42752"]
MIN_GEO_DATASETS = 2

# Preprocessing thresholds
MIN_CPM = 1.0
MIN_SAMPLE_PERCENT = 0.20  # Keep genes with CPM >= MIN_CPM in at least 20% of samples
MIN_HGNC_COVERAGE = 0.95  # Minimum gene symbol coverage required

# Model configuration
CV_FOLDS = 5
INNER_CV_FOLDS = 3
TEST_SIZE = 0.2
STRATIFY = True

# Validation thresholds
MIN_AUC = 0.75
CALIBRATION_DECILES = 10
MIN_DECILE_SIZE = 20

# Ensure directories exist
def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        RESULTS_META_ANALYSIS_DIR,
        STATE_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()
