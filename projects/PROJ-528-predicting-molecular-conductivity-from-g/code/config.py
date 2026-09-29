import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')
RAW_DATA_PATH = os.path.join(DATA_PATH, 'raw', 'smiles.csv')

# Constants
SEED = 42
OUTLIER_SIGMA = 3.0
VIF_THRESHOLD = 10.0
TARGET_VAR = 'conductivity'
CONFIDENCE_INTERVAL_TARGET = 0.95

# Sensitivity thresholds for outlier analysis (lower bound, standard, strict)
SENSITIVITY_THRESHOLDS = [2.5, 3.0, 3.5]