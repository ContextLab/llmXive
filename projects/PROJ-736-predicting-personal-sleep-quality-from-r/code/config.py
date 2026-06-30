"""
Configuration module for the Sleep Quality Prediction pipeline.

Contains all project-wide constants including random seeds, file paths,
and model hyperparameters.
"""
import os
from pathlib import Path

# ============================================================================
# Random Seeds
# ============================================================================
# Fixed seeds for reproducibility across numpy, python random, and sklearn
RANDOM_SEED = 42
NP_SEED = 42
SKLEARN_SEED = 42

# ============================================================================
# Project Paths
# ============================================================================
# Root directory is assumed to be the parent of this config file's directory
# i.e., if code/config.py is at repo/code/config.py, root is repo/
_CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = _CURRENT_DIR.parent

# Directory structure definitions (relative to ROOT_DIR)
DIR_DATA_RAW = ROOT_DIR / "data" / "raw"
DIR_DATA_PROCESSED = ROOT_DIR / "data" / "processed"
DIR_DATA_RESULTS = ROOT_DIR / "data" / "results"
DIR_DATA_BEHAVIORAL = DIR_DATA_RAW / "behavioral"
DIR_DATA_FMRI = DIR_DATA_RAW / "fmri"
DIR_LOGS = ROOT_DIR / "data" / "logs"
DIR_FIGURES = DIR_DATA_RESULTS / "figures"

# Ensure these paths exist conceptually; actual creation is handled by T001a
# but we define them here for reference.

# Specific file paths
PATH_BEHAVIORAL_CSV = DIR_DATA_BEHAVIORAL / "hcp1200_behavioral_data.csv"
PATH_FEATURES_NPY = DIR_DATA_PROCESSED / "features.npy"
PATH_PREDICTIONS_NPY = DIR_DATA_PROCESSED / "predictions.npy"
PATH_RESULT_REPORT_JSON = DIR_DATA_RESULTS / "ResultReport.json"
PATH_LOG_FILE = DIR_LOGS / "pipeline_run.json"
PATH_VIZ_OUTPUT = DIR_FIGURES / "connectome_top_edges.png"

# ============================================================================
# Data Processing Hyperparameters
# ============================================================================

# Subject Filtering
# Maximum allowed Framewise Displacement (mm) for inclusion
MAX_FRAMWISE_DISPLACEMENT = 0.3

# ============================================================================
# Feature Engineering & Model Hyperparameters
# ============================================================================

# Variance Thresholding
# Set to a low default to allow most features through initially, 
# as per task requirement to test sensitivity later.
VARIANCE_THRESHOLD = 1e-5

# PCA Configuration
# Default variance retention for PCA dimensionality reduction
PCA_VARIANCE_RETENTION = 0.95
# Maximum number of components if variance retention doesn't limit it (optional safety)
PCA_MAX_COMPONENTS = None

# Elastic Net Hyperparameters
# Grid for L1 ratio (alpha in ElasticNetCV context often refers to regularization strength, 
# but L1_ratio is the mixing parameter)
ELASTIC_NET_L1_RATIOS = [0.1, 0.5, 0.7, 0.9, 1.0]
# Alpha (regularization strength) will be tuned via CV, but we define the search space here
# or let the CV estimator handle it. For config clarity:
ELASTIC_NET_ALPHAS = None  # Let ElasticNetCV generate default log-spaced alphas

# Cross-Validation
N_FOLDS = 5
N_ITERATIONS_INNER = 10  # For inner CV loop if nested

# ============================================================================
# Statistical Validation Parameters
# ============================================================================

# Permutation Test
N_PERMUTATIONS = 1000
# Subset size for permutation test (Plan Override: 100 subjects to save time)
PERMUTATION_SUBSET_SIZE = 100

# Bootstrap
N_BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_CONFIDENCE_LEVEL = 0.95

# ============================================================================
# Sensitivity Analysis Grid
# ============================================================================
# Variance thresholds to test
SENSITIVITY_VARIANCE_THRESHOLDS = [1e-5, 1e-4, 1e-3, 1e-2, 0.01]
# PCA retention ratios to test
SENSITIVITY_PCA_RETENTIONS = [0.95, 0.90, 0.85]

# ============================================================================
# Resource Constraints
# ============================================================================
MAX_RAM_GB = 6
MAX_WALL_CLOCK_HOURS = 5
SENSITIVITY_SUB_BUDGET_HOURS = 3

# ============================================================================
# Visualization
# ============================================================================
# Number of top edges to plot
N_TOP_EDGES_VIZ = 50
# Minimum edges required to plot (SC-004)
MIN_EDGES_VIZ = 1

# ============================================================================
# Atlas Configuration
# ============================================================================
# Schaefer Atlas parameters
SCHAEFER_N_ROIS = 400
SCHAEFER_N_COMMUNITIES = 7
SCHAEFER_RESOLUTION = "2mm"

# ============================================================================
# Helper Functions
# ============================================================================
def get_paths():
    """Return a dictionary of all defined path constants."""
    return {
        "root": ROOT_DIR,
        "raw": DIR_DATA_RAW,
        "processed": DIR_DATA_PROCESSED,
        "results": DIR_DATA_RESULTS,
        "behavioral": DIR_DATA_BEHAVIORAL,
        "logs": DIR_LOGS,
        "figures": DIR_FIGURES,
        "behavioral_csv": PATH_BEHAVIORAL_CSV,
        "features_npy": PATH_FEATURES_NPY,
        "predictions_npy": PATH_PREDICTIONS_NPY,
        "result_report": PATH_RESULT_REPORT_JSON,
        "log_file": PATH_LOG_FILE,
        "viz_output": PATH_VIZ_OUTPUT,
    }

def ensure_dirs():
    """Create all necessary directories if they do not exist."""
    dirs = [
        DIR_DATA_RAW,
        DIR_DATA_PROCESSED,
        DIR_DATA_RESULTS,
        DIR_DATA_BEHAVIORAL,
        DIR_DATA_FMRI,
        DIR_LOGS,
        DIR_FIGURES,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)