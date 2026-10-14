"""
Configuration constants and utilities for the project.
"""
import logging
import logging.handlers
import sys
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_MODELS = PROJECT_ROOT / "models"
DATA_RESULTS = DATA_DIR / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = CODE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

# --- Hyperparameters & Seeds ---
RANDOM_SEED = 42
CV_FOLDS = 5
N_NOVEL_SAMPLES = 100  # Example value, adjust as needed
NOVEL_TARGET_SIZE = 5000  # Target size of the True Novel set (T009)
MIN_ELEMENTS = 5  # Minimum number of elements for HEA systems (FR-001)
VARIANCE_CLAMP = 1e-6  # Minimum variance to avoid numerical instability
DISTANCE_THRESHOLD_SIGMA = 0.5  # Minimum distance from training centroid (in sigma)
MAX_RETRIES = 3  # Maximum retries for remote fetches with exponential backoff
RETRY_BASE_DELAY = 2.0  # Base delay in seconds (2s, 4s, 8s)
MAX_PIPELINE_HOURS = 6.0  # SC-004 runtime budget

# --- Logging configuration ---
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per log file
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# --- Expected checksums ---
# Placeholder SHA-256 of the raw HEA dataset; to be updated in T027 when the
# verified dataset replaces data/raw/hea_placeholder.csv.
# The current value is the SHA-256 of the empty string, serving as a placeholder.
EXPECTED_AFLOW_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# --- Hugging Face dataset ---
HF_DATASET_NAME = "AdrianM0/afrow"  # AFLOW thermodynamics dataset identifier

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
def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure logging to output to code/logs/app.log with rotating file handler.

    Creates the logs directory on first use, attaches a
    RotatingFileHandler (10 MB max, 5 backups) writing timestamped
    entries, and mirrors records to stdout for immediate feedback.

    Args:
        level: The logging level to apply to the root logger.

    Returns:
        The configured root logger.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers so repeated calls do not duplicate records.
    logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def ensure_dirs():
    """Ensure all required directories exist."""
    for d in [DATA_RAW, DATA_PROCESSED, DATA_MODELS, DATA_RESULTS, FIGURES_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
