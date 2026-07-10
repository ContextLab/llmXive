"""
Configuration hyperparameters for the project.
"""

# Sample Entropy parameters
M = 2  # Embedding dimension
R_FACTOR = 0.2  # Tolerance factor (multiplied by SD)

# Preprocessing parameters
FD_THRESHOLD = 0.2  # Framewise Displacement threshold in mm
TARGET_LENGTH = 120  # Target number of time points after scrubbing
ATLAS_N = 200  # Number of parcels in the atlas

# Dataset parameters
DATASET_ID = "ds000305"
OPENNEURO_URL = "https://openneuro.org/datasets/ds000305"

# Modeling parameters
N_FOLDS = 5
RIDGE_ALPHA = 1.0
LOGISTIC_ALPHA = 1.0

# Paths
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
DATA_DERIVED_DIR = "data/derived"
CODE_DIR = "code"
