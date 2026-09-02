"""
Constants and configuration for the project.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state"
TESTS_DIR = PROJECT_ROOT / "tests"

# Data Subdirectories
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_INTERMEDIATE = DATA_DIR / "intermediate"

# Results Subdirectories
RESULTS_PLOTS = RESULTS_DIR / "plots"

# Ensure directories exist
def ensure_dirs():
    for d in [CODE_DIR, DATA_DIR, RESULTS_DIR, STATE_DIR, TESTS_DIR,
              DATA_RAW, DATA_PROCESSED, DATA_INTERMEDIATE, RESULTS_PLOTS]:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds
RANDOM_SEED = 42

# Model Hyperparameters
HOLD_OUT_FRACTION = 0.20
MAX_DEPTH_GRID = [5, 10, 15, 20, None]
N_PERMUTATIONS = 1000
N_ESTIMATORS = 500

# Hypothesis Thresholds
BALANCED_ACC_THRESHOLD = 0.75
FDR_THRESHOLD = 0.05
CORRELATION_THRESHOLD = 0.4
P_VALUE_THRESHOLD = 0.01

# File Paths (Relative to Project Root)
STUDY_MANIFEST_PATH = DATA_RAW / "study_manifest.json"
HETEROGENEITY_REPORT_PATH = DATA_PROCESSED / "heterogeneity_report.json"
HARMONIZED_LABELS_PATH = DATA_PROCESSED / "harmonized_labels.csv"
BATCH_CORRECTED_MATRIX_PATH = DATA_PROCESSED / "batch_corrected_matrix.csv"
LABELS_PATH = DATA_PROCESSED / "labels.csv"
PREPROCESS_LOG_PATH = DATA_PROCESSED / "preprocess_log.json"
MODEL_PATH = RESULTS_DIR / "model.pkl"
FEATURE_IMPORTANCE_PATH = RESULTS_DIR / "feature_importance_ranking.json"
CORRELATION_ANALYSIS_PATH = RESULTS_DIR / "correlation_analysis_raw.json"
MODEL_VALIDATION_PATH = RESULTS_DIR / "model_validation.json"
SENSITIVITY_ANALYSIS_PATH = RESULTS_DIR / "sensitivity_analysis.json"
VIF_SCORES_PATH = RESULTS_DIR / "vif_scores.json"
SHAP_ANALYSIS_PATH = RESULTS_DIR / "shap_analysis.json"
TOP_METABOLITES_PATH = RESULTS_DIR / "top_metabolites.json"
PATHWAY_MAPPINGS_PATH = RESULTS_DIR / "pathway_mappings.json"
PATHWAY_REPORT_PATH = RESULTS_DIR / "pathway_report.json"
PATHWAY_ANALYSIS_PATH = RESULTS_DIR / "pathway_analysis.json"

# Initialize directories on import
ensure_dirs()
