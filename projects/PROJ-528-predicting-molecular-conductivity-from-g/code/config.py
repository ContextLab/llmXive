import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')

# Constants
SEED = 42
OUTLIER_SIGMA = 3.0
VIF_THRESHOLD = 10.0
TARGET_VAR = 'conductivity'
