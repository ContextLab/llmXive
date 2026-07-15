import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_RESULTS = PROJECT_ROOT / "output" / "results"
OUTPUT_PLOTS = PROJECT_ROOT / "output" / "plots"
OUTPUT_REPORTS = PROJECT_ROOT / "output" / "reports"
OUTPUT_EXPLORATORY = PROJECT_ROOT / "output" / "exploratory"
OUTPUT_FIGURES = PROJECT_ROOT / "output" / "figures"

# Random seeds
RANDOM_SEED = 42

# Default thresholds
DEFAULT_CORRELATION_THRESHOLD = 0.3
THRESHOLD_SWEEP_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5]

# Permutation settings
DEFAULT_N_PERMUTATIONS = 1000
N_PERMUTATIONS_LARGE = 500  # For clustering coefficient on large datasets

def get_config() -> Dict[str, Any]:
    """
    Return a dictionary of configuration values.
    """
    return {
        'data_raw': str(DATA_RAW),
        'data_processed': str(DATA_PROCESSED),
        'output_results': str(OUTPUT_RESULTS),
        'output_plots': str(OUTPUT_PLOTS),
        'output_reports': str(OUTPUT_REPORTS),
        'output_exploratory': str(OUTPUT_EXPLORATORY),
        'output_figures': str(OUTPUT_FIGURES),
        'random_seed': RANDOM_SEED,
        'default_threshold': DEFAULT_CORRELATION_THRESHOLD,
        'threshold_sweep': THRESHOLD_SWEEP_VALUES,
        'n_permutations': DEFAULT_N_PERMUTATIONS,
        'n_permutations_large': N_PERMUTATIONS_LARGE,
    }

def ensure_dirs() -> None:
    """
    Ensure all required directories exist.
    """
    for path in [DATA_RAW, DATA_PROCESSED, OUTPUT_RESULTS, OUTPUT_PLOTS, OUTPUT_REPORTS, OUTPUT_EXPLORATORY, OUTPUT_FIGURES]:
        os.makedirs(path, exist_ok=True)

# Re-exporting functions that might be needed by other modules
# Note: In a real implementation, these would be defined in stats_engine.py
# and imported here for convenience.
# For this task, we assume they exist as per the API surface.

# Placeholder for functions that should be in stats_engine.py
# These are imported from stats_engine in the main module
# def construct_graph(corr_matrix, threshold):
#     pass
# def calculate_stats(graph):
#     pass