"""
Project Configuration Module.

Handles random seeds, file paths, and study parameters.
"""

import os
from pathlib import Path
from typing import Final, Dict, Any
from datetime import datetime

# Root directory of the project
_ROOT_DIR = Path(__file__).resolve().parents[1]

# Study Period
START_DATE: Final[datetime] = datetime(2023, 1, 1)
END_DATE: Final[datetime] = datetime(2023, 12, 31)
RANDOM_SEED: Final[int] = 42

# Directory Paths
DATA_RAW_DIR: Final[Path] = _ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = _ROOT_DIR / "data" / "processed"
DATA_ARTIFACTS_DIR: Final[Path] = _ROOT_DIR / "data" / "artifacts"
CODE_DIR: Final[Path] = _ROOT_DIR / "code"
TESTS_DIR: Final[Path] = _ROOT_DIR / "tests"

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary of configuration parameters.
    """
    return {
        "start_date": START_DATE,
        "end_date": END_DATE,
        "seed": RANDOM_SEED,
        "data_raw_dir": DATA_RAW_DIR,
        "data_processed_dir": DATA_PROCESSED_DIR,
        "data_artifacts_dir": DATA_ARTIFACTS_DIR,
        "code_dir": CODE_DIR,
        "tests_dir": TESTS_DIR,
    }
