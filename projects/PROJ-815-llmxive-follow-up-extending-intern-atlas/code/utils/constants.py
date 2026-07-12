"""
Constants for the llmXive follow-up: extending Intern-Atlas project.

This module defines core configuration values used across the pipeline,
including date ranges, edge types, and retraction label mappings.
"""

# Date range for analysis (inclusive)
MIN_YEAR = 2010
MAX_YEAR = 2018
ANALYSIS_YEAR_RANGE = (MIN_YEAR, MAX_YEAR)

# Edge types representing relationships between methods
EDGE_TYPE_IMPROVES = "improves"
EDGE_TYPE_REPLACES = "replaces"
EDGE_TYPE_EXTENDS = "extends"
VALID_EDGE_TYPES = {EDGE_TYPE_IMPROVES, EDGE_TYPE_REPLACES, EDGE_TYPE_EXTENDS}

# Retraction label mappings
# 0 = Robust (no retraction or non-methodological retraction)
# 1 = Fragile (methodological error or irreproducibility)
# 2 = Retraction-Only (fraud or misconduct)
LABEL_ROBUST = 0
LABEL_FRAGILE = 1
LABEL_RETRACTION_ONLY = 2

RETRACTION_LABEL_MAPPING = {
    LABEL_ROBUST: "Robust",
    LABEL_FRAGILE: "Fragile",
    LABEL_RETRACTION_ONLY: "Retraction-Only",
}

# Reason to label mapping logic (used in merge_retractions.py)
# These are the canonical reason categories that map to labels
REASON_METHODOLOGICAL_ERROR = "methodological error"
REASON_IRREPRODUCIBILITY = "irreproducibility"
REASON_FRAUD = "fraud"
REASON_OTHER = "other"

# Mapping from reason strings to numeric labels
REASON_TO_LABEL = {
    REASON_METHODOLOGICAL_ERROR: LABEL_FRAGILE,
    REASON_IRREPRODUCIBILITY: LABEL_FRAGILE,
    REASON_FRAUD: LABEL_RETRACTION_ONLY,
    REASON_OTHER: LABEL_ROBUST,
}

# File paths and output names
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
FEATURES_OUTPUT_FILE = "features_2010_2018.csv"
FEATURES_FULL_PATH = f"{DATA_PROCESSED_DIR}/{FEATURES_OUTPUT_FILE}"

# Model results
MODEL_RESULTS_FILE = "model_results.json"
MODEL_RESULTS_FULL_PATH = f"{DATA_PROCESSED_DIR}/{MODEL_RESULTS_FILE}"

# Sensitivity analysis outputs
SENSITIVITY_FLAGS_FILE = "sensitivity_flags.json"
SENSITIVITY_FLAGS_FULL_PATH = f"{DATA_PROCESSED_DIR}/{SENSITIVITY_FLAGS_FILE}"
THRESHOLD_METRICS_FILE = "threshold_sweep_metrics.json"
THRESHOLD_METRICS_FULL_PATH = f"{DATA_PROCESSED_DIR}/{THRESHOLD_METRICS_FILE}"
STRUCTURAL_COUPING_REPORT_FILE = "structural_coupling_report.json"
STRUCTURAL_COUPING_REPORT_FULL_PATH = f"{DATA_PROCESSED_DIR}/{STRUCTURAL_COUPING_REPORT_FILE}"

# Plot outputs
PLOTS_DIR = f"{DATA_PROCESSED_DIR}/plots"
PR_CURVE_FILE = "pr_curve.png"
PERMUTATION_DIST_FILE = "permutation_dist.png"
THRESHOLD_SWEEP_FILE = "threshold_sweep.png"

# Threshold values for sensitivity analysis
THRESHOLD_VALUES = [0.3, 0.5, 0.7]

# Fuzzy matching threshold
FUZZY_MATCH_RATIO_THRESHOLD = 0.85

# Permutation test iterations
PERMUTATION_ITERATIONS = 100

# VIF and MI thresholds for instability detection
VIF_THRESHOLD = 5.0
MI_THRESHOLD = 0.1

# Random seed for reproducibility
DEFAULT_SEED = 42