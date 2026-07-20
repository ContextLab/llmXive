"""
Global configuration constants for the CMB Gap Bias Analysis project.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_DERIVED_DIR = DATA_DIR / "derived"
DATA_METADATA_DIR = DATA_DIR / "metadata"
DATA_RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
TESTS_DIR = PROJECT_ROOT / "tests"

# Simulation Constants
N_SIDE = 512
BASE_SEED = 42
MAX_L = 2 * N_SIDE  # Default max multipole

# Cosmological Parameters (Ground Truth for Simulation)
# These match the simple setup in generate_maps.py
COSMO_PARAMS = {
    "H0": 67.4,
    "ombh2": 0.022,
    "omch2": 0.12,
    "n_s": 0.965,
    "tau": 0.054,
    "As": 2.1e-9,
    "r": 0.0,
}

# Gap Configuration
GAP_FRACTIONS = [0.05, 0.10, 0.15, 0.20, 0.25]
GAP_MORPHOLOGIES = ["random", "clustered", "point_source", "galactic_plane"]

# Algorithm Configuration
ALGORITHMS = ["harmonic_interp", "wiener_filter", "iterative_synthesis"]

# Budget Constraints
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 24.0
MIN_REALIZATIONS = 30

# Data Types
FORCE_FLOAT32 = True

def get_dtype():
    """Return numpy dtype based on FORCE_FLOAT32."""
    return np.float32 if FORCE_FLOAT32 else np.float64

# Ensure directories exist
def ensure_directories():
    """Create all required directories if they do not exist."""
    for d in [DATA_RAW_DIR, DATA_DERIVED_DIR, DATA_METADATA_DIR, DATA_RESULTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Initialize on import
ensure_directories()
