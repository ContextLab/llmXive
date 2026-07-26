import os
from pathlib import Path

# Base project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = Path(os.getenv("TMP_DIR", PROJECT_ROOT / "data" / "tmp"))
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
TMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Disk space constraint (14 GB in bytes)
MIN_DISK_SPACE_BYTES = 14 * 1024**3

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 60.0     # seconds

# Dataset versions
ENCODE_VERSION = "v10"
JASPAR_VERSION = "2024"
GENOME_BUILD = "hg38"

# Output file names
INGESTION_SUMMARY_FILE = "ingestion_summary.json"
ENRICHMENT_MATRIX_FILE = "enrichment_matrix.csv"
HEATMAP_FILE = "heatmap.png"
VALIDATION_REPORT_FILE = "validation_report.json"
SUMMARY_TABLE_FILE = "summary_table.csv"