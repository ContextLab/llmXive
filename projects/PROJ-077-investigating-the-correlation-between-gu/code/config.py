import os
from pathlib import Path

# Project root is assumed to be the parent of the code directory
PROJECT_ROOT = Path(__file__).parent.parent

# Define required directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
FIGURES_DIR = PROJECT_ROOT / "data" / "processed" / "plots"

def ensure_directories():
    """
    Ensures that all required project directories exist.
    Creates them if they do not exist.
    """
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_DIR,
        TESTS_DIR,
        FIGURES_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Configuration constants
RANDOM_SEED = 42
SAMPLE_LIMIT = 50000  # Per Plan Complexity Tracking: Hard stop at 50k rows to prevent OOM
DQS_REQUIRED = False  # Default to False to allow graceful degradation if dietary data is missing

# Input paths definition
# These paths are used by data_fetcher and data_ingestion to locate source files.
# T050/T051 will handle the logic of populating these or validating their existence.
INPUT_PATHS = {
    "microbiome": DATA_RAW_DIR / "microbiome_data.csv",
    "cognitive": DATA_RAW_DIR / "cognitive_data.csv",
    "dietary": DATA_RAW_DIR / "dietary_data.csv"
}

# Required columns for HEI-2015 calculation (used in T014a/T014c)
HEI_2015_REQUIRED_COLUMNS = [
    "Total Fruits",
    "Whole Fruits",
    "Total Vegetables",
    "Greens and Beans",
    "Whole Grains",
    "Dairy",
    "Total Protein Foods",
    "Seafood and Plant Proteins",
    "Refined Grains",
    "Sodium",
    "Empty Calories"
]

# Participant ID column priority (used in T011)
PARTICIPANT_ID_PRIORITY = ["participant_id", "eid", "subject_id"]