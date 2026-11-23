import os
from pathlib import Path

# Project Root (assumed to be the directory containing this file's parent)
# If running as a module, we resolve relative to this file
_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = _ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"

# State Directory
STATE_DIR = _ROOT / "state"
STATE_PROJECTS_DIR = STATE_DIR / "projects"

# Dataset Identifiers (HuggingFace)
DATASET_BOOK_CORPUS = "tr-books-tokenized"
DATASET_BEIR = "Tr-beir-formatted"

# Hyperparameters & Seeds
RANDOM_SEED = 42
MAX_SEQ_LENGTH = 512
BATCH_SIZE = 32

# Feature Extraction Params
NGRAM_SIZE = 4
MAX_PARSE_DEPTH = 20

def ensure_directories() -> None:
    """
    Ensure all required data directories exist.
    Calls setup_directories logic to create raw, processed, and results folders.
    """
    dirs = [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, STATE_DIR, STATE_PROJECTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
