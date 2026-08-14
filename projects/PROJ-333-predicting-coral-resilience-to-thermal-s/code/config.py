import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# NCBI Configuration
# Override: Spec FR-001 lists PRJNA292777, but Plan.md confirms PRJNA321023 contains the required thermal stress data. Source: Plan.md Technical Context.
NCBI_BIOPROJECT_ID = "PRJNA321023"
NCBI_REFSEQ_ASSEMBLY = "GCF_000163615.2"

# Resource Limits
MAX_RAM_GB = 7

# Thresholds (Placeholders - to be determined in research phase)
MIN_SAMPLES_FOR_FILTER = None  # TODO: Determine in research phase
MIN_COUNT_THRESHOLD = None  # TODO: Determine in research phase

def ensure_directories() -> None:
    """Creates required data directories if they do not exist."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    (DATA_RAW / "reference").mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED / "quant").mkdir(parents=True, exist_ok=True)

def get_thresholds() -> dict:
    """Returns current threshold configuration."""
    return {
        "min_samples": MIN_SAMPLES_FOR_FILTER,
        "min_count": MIN_COUNT_THRESHOLD,
        "max_ram_gb": MAX_RAM_GB
    }
