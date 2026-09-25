import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# NCBI Configuration
# BioProject ID updated via T004b (Spec Amendment). Original PRJNA superseded.
# T004b Record: AMEND-001 - Updated to PRJNA321023 as per Plan.md technical context.
NCBI_BIOPROJECT_ID = "PRJNA321023"
NCBI_REFSEQ_ASSEMBLY = "GCF_000163615.2"

# Resource Limits
MAX_RAM_GB = 7

# Thresholds (Provisional values per Constitution Check VII & T009b Strategy)
# MIN_COUNT_THRESHOLD=10 is provisional per T009b. Research phase may update this value.
MIN_COUNT_THRESHOLD = 10
# MIN_SAMPLES_FOR_FILTER is provisional per T009b. Research phase may update this value.
MIN_SAMPLES_FOR_FILTER = 3

def ensure_directories() -> None:
    """Creates required data directories if they do not exist."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    (DATA_RAW / "reference").mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED / "quant").mkdir(parents=True, exist_ok=True)
    (DATA_RAW / "PRJNA321023").mkdir(parents=True, exist_ok=True)

def get_thresholds() -> dict:
    """Returns current threshold configuration."""
    return {
        "min_samples": MIN_SAMPLES_FOR_FILTER,
        "min_count": MIN_COUNT_THRESHOLD,
        "max_ram_gb": MAX_RAM_GB,
        "bioproject_id": NCBI_BIOPROJECT_ID
    }
