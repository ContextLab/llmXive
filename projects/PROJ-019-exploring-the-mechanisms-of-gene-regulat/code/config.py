"""
Project configuration constants for llmXive gene regulation pipeline.

Defines directory paths, retry limits, and dataset version constants
required by the pipeline modules.
"""

import os
from pathlib import Path

# --- Directory Paths ---
# Base project root is assumed to be the parent of 'code'
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Temporary directory for downloads and intermediate processing
# Can be overridden by environment variable TMP_DIR
TMP_DIR = Path(os.getenv("TMP_DIR", _PROJECT_ROOT / "data" / "tmp"))

# Data directories
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_DIR = _PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"

# Ensure directory structure exists (optional, but good for robustness)
# Note: We don't force creation here to avoid side-effects on import,
# but main.py or specific scripts should ensure these exist before writing.
# Uncomment if you want automatic creation on import:
# TMP_DIR.mkdir(parents=True, exist_ok=True)
# DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
# DATA_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
# DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- Retry Limits ---
# Maximum number of retry attempts for network requests (FR-006)
MAX_RETRIES = 3

# Initial delay for exponential backoff in seconds
INITIAL_RETRY_DELAY = 1.0

# Maximum delay cap for exponential backoff in seconds
MAX_RETRY_DELAY = 60.0

# --- Dataset Versions ---
# ENCODE data version (can be updated as needed)
ENCODE_VERSION = "v3"

# JASPAR database version (CORE release)
JASPAR_VERSION = "2024"

# Reference genome assembly
GENOME_ASSEMBLY = "hg38"

# --- Disk Space Constraints ---
# Minimum required free space in bytes (14 GB)
MIN_FREE_SPACE_BYTES = 14 * 1024 * 1024 * 1024

# --- FIMO Configuration ---
# FIMO p-value threshold for motif scanning (FR-003)
FIMO_PVALUE_THRESHOLD = 0.0001

# --- Enrichment Configuration ---
# Minimum motif count for statistical testing
MIN_MOTIF_COUNT = 5

# --- Visualization Configuration ---
# Silhouette score threshold for validation warning (US-3-SC1)
MIN_SILHOUETTE_SCORE = 0.4

# --- Logging Configuration ---
# Default log level
LOG_LEVEL = "INFO"

# Log file path (optional, can be overridden)
LOG_FILE = _PROJECT_ROOT / "data" / "logs" / "pipeline.log"

# --- Cell Types ---
# List of cell types to process (as per US1)
CELL_TYPES = [
    "GM",
    "K562",
    "HepG2",
    "H1-hESC",
    "IMR90"
]

# --- File Naming Patterns ---
# Pattern for ENCODE peak files (placeholder, actual URLs defined in download.py)
ENCODE_PEAK_PATTERN = "{cell_type}_peaks.bed.gz"

# Pattern for JASPAR motifs file
JASPAR_MOTIFS_FILE = "JASPAR2024_CORE_vertebrates_non-redundant_pfms_meme.txt"

# Pattern for output files
INGESTION_SUMMARY_FILE = "ingestion_summary.json"
ENRICHMENT_MATRIX_FILE = "enrichment_matrix.csv"
HEATMAP_FILE = "heatmap.png"
VALIDATION_REPORT_FILE = "validation_report.json"
SUMMARY_TABLE_FILE = "summary_table.csv"
