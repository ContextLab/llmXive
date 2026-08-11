import os
import numpy as np

# Set random seed for reproducibility
# Note: This must be called at import time or explicitly before data generation
# to ensure deterministic behavior across the pipeline.
_RANDOM_SEED = 42
np.random.seed(_RANDOM_SEED)

# Project root directory (assumed to be the parent of code/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
DATA_LOGS_DIR = os.path.join(DATA_DIR, "logs")
DATA_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")

# Ensure directories exist
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(DATA_LOGS_DIR, exist_ok=True)
os.makedirs(DATA_ARTIFACTS_DIR, exist_ok=True)

# Hyperparameters
MIN_WORD_COUNT = 50
LANGUAGE_DETECTION_THRESHOLD = 0.8
SIMILARITY_THRESHOLD_DEFAULT = 0.30
VIF_WARNING_THRESHOLD = 5.0
BONFERRONI_ALPHA = 0.05

# Extraction parameters
PRONOUN_LIST = [
    'i', 'me', 'my', 'myself', 'we', 'us', 'our', 'ours', 'ourselves',
    'you', 'your', 'yours', 'yourself', 'yourselves',
    'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
    'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves'
]

# Output paths
OUTPUT_REGRESSION_PLOT = os.path.join(DATA_ARTIFACTS_DIR, "regression_plot.png")
OUTPUT_PERSPECTIVE_FEATURES = os.path.join(DATA_PROCESSED_DIR, "perspective_features.json")
OUTPUT_MATCHING_RESULTS = os.path.join(DATA_PROCESSED_DIR, "matching_results.json")
OUTPUT_ALIGNED_DATASET = os.path.join(DATA_PROCESSED_DIR, "aligned_dataset.csv")
OUTPUT_READER_RESPONSE = os.path.join(DATA_PROCESSED_DIR, "reader_response.csv")