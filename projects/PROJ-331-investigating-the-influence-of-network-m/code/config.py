"""
Configuration module for the motif-rsfc project.
Defines paths, seeds, and constants used throughout the pipeline.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = DATA_DIR / "logs"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
FIGURES_DIR = RESULTS_DIR / "figures"

# Random seed for reproducibility
RANDOM_SEED = 42

# Performance constraints
MOTIF_TIMEOUT_SECONDS = 300  # SC-002: Max 300s per subject

# Statistical parameters
BONFERRONI_ALPHA = 0.05
PERMUTATION_COUNT = 1000
VIF_THRESHOLD = 5.0

# Cohort configuration
# Expected number of subjects in the HCP cohort for this study
EXPECTED_COHORT_SIZE = 100

# Motif analysis configuration
# Default number of nodes for motif enumeration (FR-004)
# Configurable to allow investigation of n-node subgraphs
N_MOTIF_NODES = 3

# Directory paths for specific outputs
SUBJECT_LIST_MANIFEST_PATH = PROCESSED_DIR / "subject_list_manifest.json"
WEIGHTED_ADJACENCY_DIR = PROCESSED_DIR
BINARY_ADJACENCY_PATH = PROCESSED_DIR / "canonical_binary_adj.npy"
MOTIF_PROFILES_PATH = PROCESSED_DIR / "motif_profiles.json"
GLOBAL_EFFICIENCY_PATH = PROCESSED_DIR / "global_efficiency.json"
SUBJECT_METRICS_PATH = PROCESSED_DIR / "subject_metrics.csv"
SUCCESS_RATE_PATH = PROCESSED_DIR / "success_rate.json"
QUALITY_FLAGS_PATH = PROCESSED_DIR / "quality_flags.json"
PARTIAL_CORRELATIONS_PATH = PROCESSED_DIR / "partial_correlations.json"
CORRELATION_RESULTS_PATH = RESULTS_DIR / "correlation_results.json"
PERMUTATION_RESULTS_PATH = RESULTS_DIR / "permutation_results.json"
POWER_ANALYSIS_PATH = RESULTS_DIR / "power_analysis.json"
PIPELINE_LOG_PATH = LOGS_DIR / "pipeline.log"
REPORT_PATH = RESULTS_DIR / "results.pdf"

def ensure_dirs():
    """Create all necessary directories if they don't exist."""
    dirs = [
        CODE_DIR,
        DATA_DIR,
        RESULTS_DIR,
        STATE_DIR,
        LOGS_DIR,
        PROCESSED_DIR,
        RAW_DIR,
        FIGURES_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_dirs()
    print("Directories ensured.")