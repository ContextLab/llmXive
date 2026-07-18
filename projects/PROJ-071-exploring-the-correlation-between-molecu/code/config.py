"""
Centralized configuration management for the llmXive pipeline.
Replaces all hardcoded paths with configurable constants.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root Resolution
# Assumes the script is run from the project root or code/ directory.
# We resolve the root based on the location of this config file.
_CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CURRENT_DIR.parent

# Directory Constants
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_OUTPUTS_DIR = DATA_DIR / "outputs"
DATA_CHECKSUMS_FILE = DATA_DIR / "checksums.txt"
DATA_ERRORS_LOG = DATA_DIR / "errors.log"
DATA_INSUFFICIENCY_REPORT = DATA_DIR / "data_insufficiency_report.md"

FIGURES_DIR = PROJECT_ROOT / "figures"
RESULTS_REPORT = PROJECT_ROOT / "results_report.md"
REPRODUCIBILITY_REPORT = PROJECT_ROOT / "reproducibility_report.json"

# Ensure directories exist
def ensure_directories():
    """Create necessary data directories if they don't exist."""
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_OUTPUTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Data Source Constants
HUGGINGFACE_DATASET_ID = "Synthyra/FDA-Approved-Drugs"
DEFAULT_DEGRADATION_COLUMN = "half_life_hours"
MIN_SAMPLE_SIZE = 30

# Analysis Constants
CORRELATION_THRESHOLD = 0.5
P_VALUE_THRESHOLD = 0.05
ARRHENIUS_STANDARD_TEMP = 298.15  # 25°C in Kelvin
STANDARD_PH = 7.4
COVERAGE_THRESHOLD = 0.50

# Visualization Constants
SCATTER_PLOT_TEMPLATE = "scatter_{feature}_vs_half_life.png"
RESIDUALS_PLOT = "residuals.png"
QQ_PLOT = "qq_plot.png"

# Logging Constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.getenv("PIPELINE_LOG_LEVEL", "INFO")

# Reproducibility Constants
REQUIRED_PACKAGES = [
    "rdkit",
    "pandas",
    "scikit-learn",
    "numpy",
    "matplotlib",
    "seaborn",
    "pyyaml",
    "requests",
    "datasets"
]

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary of all current configuration settings.
    Useful for logging or passing to functions that need context.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "data_outputs": str(DATA_OUTPUTS_DIR),
        "figures_dir": str(FIGURES_DIR),
        "huggingface_dataset": HUGGINGFACE_DATASET_ID,
        "min_sample_size": MIN_SAMPLE_SIZE,
        "correlation_threshold": CORRELATION_THRESHOLD,
        "p_value_threshold": P_VALUE_THRESHOLD,
        "standard_temp_k": ARRHENIUS_STANDARD_TEMP,
        "standard_ph": STANDARD_PH,
        "log_level": LOG_LEVEL
    }