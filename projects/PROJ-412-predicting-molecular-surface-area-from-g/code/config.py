"""
Configuration parameters for the molecular surface area prediction pipeline.
"""
import os
from typing import List

# Time budget for the entire pipeline (hours)
# Placeholder value; to be updated based on CI runner profile or final plan
TIME_BUDGET: float = 6.0

# Maximum RAM usage in GB before triggering early exit
MAX_RAM_GB: float = 7.0

# Sensitivity thresholds for MAE analysis (in Angstroms squared)
# As mandated by FR-006
SENSITIVITY_THRESHOLDS: List[float] = [0.01, 0.05, 0.1]

# Random seed for reproducibility
RANDOM_SEED: int = 42

# Paths
PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR: str = os.path.join(PROJECT_ROOT, 'data')
LOGS_DIR: str = os.path.join(PROJECT_ROOT, 'logs')
RESULTS_DIR: str = os.path.join(PROJECT_ROOT, 'results')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
