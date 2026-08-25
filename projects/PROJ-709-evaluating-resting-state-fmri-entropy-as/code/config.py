"""
Configuration file for hyperparameters and constants.

This module centralizes all tunable parameters for the fMRI entropy analysis pipeline.
"""
import os
from pathlib import Path

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"

# Entropy Parameters
M = 2  # Embedding dimension
R_FACTOR = 0.2  # Tolerance factor as fraction of standard deviation

# Preprocessing Parameters
FD_THRESHOLD = 0.2  # Framewise Displacement threshold for scrubbing (mm)
TARGET_LENGTH = 120  # Target number of time points after truncation

# Atlas Parameters
ATLAS_N = 200  # Number of parcels in the atlas

# Dataset Parameters
DATASET_ID = "ds000305"  # OpenNeuro dataset ID for ADHD

# Modeling Parameters
N_FOLDS = 5  # Number of folds for cross-validation
RIDGE_ALPHA = 1.0  # Regularization strength for Ridge regression
LOGISTIC_ALPHA = 1.0  # Regularization strength for Logistic Ridge

# Validation Parameters
N_PERMUTATIONS = 1000  # Number of permutations for significance testing
FDR_ALPHA = 0.05  # Significance level for FDR correction

# Motion Analysis
MOTION_CORRELATION_THRESHOLD = 0.3  # Threshold for flagging motion-entropy correlation

# Feature Selection
FEATURE_SELECTION_TARGET = 30  # Target number of features after RFE/Lasso (range 20-50)
