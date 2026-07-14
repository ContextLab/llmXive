import os

# Random Seed Configuration
RANDOM_SEED = 42

# Project Root and Directory Constants
# Assuming the project root is the directory containing this config file's parent,
# or we derive it relative to the current file location if run from code/.
# Standard convention: code/ is at project root or src/. Here we assume code/ is at root based on T001 description.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(_BASE_DIR, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
DATA_RESULTS_DIR = os.path.join(DATA_DIR, "results")

SPECS_DIR = os.path.join(_BASE_DIR, "specs")
CONTRACTS_DIR = os.path.join(SPECS_DIR, "contracts")

CODE_DIR = os.path.join(_BASE_DIR, "code")
TESTS_DIR = os.path.join(_BASE_DIR, "tests")

# Output File Paths
GAMES_PARQUET_PATH = os.path.join(DATA_PROCESSED_DIR, "games.parquet")
MODEL_METRICS_JSON_PATH = os.path.join(DATA_RESULTS_DIR, "model_metrics.json")
DIAGNOSTICS_JSON_PATH = os.path.join(DATA_RESULTS_DIR, "diagnostics.json")

# Lichess Dataset URL Constants
# Using a specific, publicly available Lichess dataset from HuggingFace Datasets
# Dataset: lichess-db (or similar stable source). 
# We use the 'lichess_2023' or a specific PGN URL.
# For robustness, we point to the HuggingFace dataset API or a direct PGN mirror.
# Primary: HuggingFace 'lichess' dataset (requires datasets library, added in T002)
# We define the dataset name and split to load via `load_dataset`
LICHESS_DATASET_NAME = "lichess"
LICHESS_DATASET_SPLIT = "train"

# Alternative: Direct PGN URL for smaller subsets or specific years if HuggingFace is unavailable
# Example: Lichess monthly PGN exports
LICHESS_PGN_BASE_URL = "https://database.lichess.org/"
LICHESS_PGN_YEAR_URL_TEMPLATE = "https://database.lichess.org/lichess_db_{}.pgn.gz"

# Specific dataset URL for the task (if using a direct download approach instead of HF)
# Using a representative sample URL for the 2023 dataset often used in research
SAMPLE_LICHESS_URL = "https://database.lichess.org/lichess_db_2023-01.pgn.gz"

# Configuration Flags
MAX_SAMPLE_SIZE = 1000  # For initial verification (T009)
MOVE_TIME_THRESHOLD_PERCENT = 5.0  # Percentage of games missing move_time to trigger HALT (T009)
MIN_GAME_INCLUSION_RATE = 0.95  # SC-001: Minimum inclusion rate for valid PGNs

def ensure_directories():
    """Ensure all project data directories exist."""
    import os
    dirs = [
        DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR,
        SPECS_DIR, CONTRACTS_DIR, TESTS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)