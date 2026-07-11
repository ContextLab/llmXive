import os

# Project Root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Directories
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
DATA_RESULTS_DIR = os.path.join(PROJECT_ROOT, 'data', 'results')
FIGURES_DIR = os.path.join(PROJECT_ROOT, 'figures')

# Random Seed
RANDOM_SEED = 42

# Thresholds
THRESHOLDS = {
    'low': 0.01,
    'medium': 0.05,
    'high': 0.10
}

# Resource Limits
MAX_RUNTIME_HOURS = 4
MAX_RAM_GB = 6
