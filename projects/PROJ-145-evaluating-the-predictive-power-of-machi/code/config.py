"""
Configuration constants and utilities for the project.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_MODELS = DATA_DIR / "models"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = CODE_DIR / "logs"

# --- Hyperparameters & Seeds ---
RANDOM_SEED = 42
N_NOVEL_SAMPLES = 100  # Example value, adjust as needed
EXPECTED_AFLOW_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Placeholder, to be updated

# --- Element List ---
# Broad list of transition and post-transition metals
ELEMENT_SOURCE_LIST = [
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Al", "Si", "P", "S", "Cl", "K", "Ca", "Ga", "Ge", "As", "Se", "Br",
    "Rb", "Sr", "In", "Sn", "Sb", "Te", "I", "Cs", "Ba",
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho",
    "Er", "Tm", "Yb", "Lu"
]

# --- Logging Configuration ---
def setup_logging():
    """Configure logging to output to code/logs/app.log with rotating file handler."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "app.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Console handler (optional, for immediate feedback)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def ensure_dirs():
    """Ensure all required directories exist."""
    for d in [DATA_RAW, DATA_PROCESSED, DATA_MODELS, FIGURES_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Initialize logging on import if needed, or call explicitly
# setup_logging()
