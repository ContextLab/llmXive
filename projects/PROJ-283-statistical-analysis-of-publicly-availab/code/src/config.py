import os
from pathlib import Path

# Project Root
_ROOT = Path(__file__).resolve().parents[1]

# Random Seeds
RANDOM_SEED: int = 42

# File Path Constants
DIR_DATA_RAW: Path = _ROOT / "data" / "raw"
DIR_DATA_PROCESSED: Path = _ROOT / "data" / "processed"
DIR_DATA_RESULTS: Path = _ROOT / "data" / "results"
DIR_SPECS: Path = _ROOT / "specs"
DIR_SPECS_CONTRACTS: Path = DIR_SPECS / "contracts"

# Lichess Dataset URL Constants
# Official Lichess Game Export (PGN)
LICHES_BASE_URL: str = "https://database.lichess.org"
LICHES_GAMES_URL_TEMPLATE: str = (
    f"{LICHES_BASE_URL}/lichess_db_standard_rated_{{year}}.pgn.xz"
)

# Alternative: HuggingFace Dataset for Chess (if preferred for programmatic access)
# Using a specific version of the dataset to ensure reproducibility
HF_DATASET_NAME: str = "chess/lichess-game-database"
HF_DATASET_CONFIG: str = "pgn"

# Configuration for Sampling/Testing
SAMPLE_SIZE_SMALL: int = 100
SAMPLE_SIZE_MEDIUM: int = 10000

# Validation Thresholds
MOVE_TIME_MISSING_THRESHOLD: float = 0.05  # 5%
VALID_GAME_INCLUSION_THRESHOLD: float = 0.95  # 95%

def get_contract_path(contract_name: str) -> Path:
    """
    Returns the full path to a specific contract schema file.
    
    Args:
        contract_name: The filename of the schema (e.g., 'game_record.schema.yaml')
        
    Returns:
        Path to the schema file.
    """
    return DIR_SPECS_CONTRACTS / contract_name

def get_data_path(sub_path: str) -> Path:
    """
    Returns a full path relative to the data directory.
    
    Args:
        sub_path: Relative path under data/ (e.g., 'raw/games.pgn.xz')
        
    Returns:
        Full Path object.
    """
    return DIR_DATA_RAW / sub_path if not sub_path.startswith("processed") and not sub_path.startswith("results") \
           else (DIR_DATA_PROCESSED / sub_path if sub_path.startswith("processed") else DIR_DATA_RESULTS / sub_path.replace("results/", ""))