"""
Configuration module for the BCC Steel Yield Strength prediction pipeline.

Defines project paths, random seeds, API keys, and external data URLs.
"""
import os
import json
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random Seed for reproducibility
SEED = 42

# Error Codes
ERR_INSUFFICIENT_DATA = "ERR_INSUFFICIENT_DATA"
ERR_API_UNAVAILABLE = "ERR_API_UNAVAILABLE"
ERR_FILE_NOT_FOUND = "ERR_FILE_NOT_FOUND"

# Directory Paths
DIR_CODE = PROJECT_ROOT / "code"
DIR_DATA = PROJECT_ROOT / "data"
DIR_DATA_RAW = DIR_DATA / "raw"
DIR_DATA_INTERMEDIATE = DIR_DATA / "intermediate"
DIR_DATA_PROCESSED = DIR_DATA / "processed"
DIR_DATA_PROVENANCE = DIR_DATA / "provenance"
DIR_DATA_RESULTS = DIR_DATA / "results"
DIR_TESTS = PROJECT_ROOT / "tests"
DIR_TESTS_UNIT = DIR_TESTS / "unit"
DIR_TESTS_INTEGRATION = DIR_TESTS / "integration"
DIR_TESTS_CONTRACT = DIR_TESTS / "contract"
DIR_SPECS = PROJECT_ROOT / "specs"
DIR_CONTRACTS = PROJECT_ROOT / "contracts"

# Ensure directories exist (lazy initialization)
def ensure_dirs():
    """Create all project directories if they do not exist."""
    dirs = [
        DIR_CODE,
        DIR_DATA,
        DIR_DATA_RAW,
        DIR_DATA_INTERMEDIATE,
        DIR_DATA_PROCESSED,
        DIR_DATA_PROVENANCE,
        DIR_DATA_RESULTS,
        DIR_TESTS,
        DIR_TESTS_UNIT,
        DIR_TESTS_INTEGRATION,
        DIR_TESTS_CONTRACT,
        DIR_SPECS,
        DIR_CONTRACTS,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# API Configuration
def get_mp_api_key() -> Optional[str]:
    """
    Retrieve the Materials Project API key from environment variables.
    Returns None if not found.
    """
    return os.getenv("MP_API_KEY")

# External Data URLs
# Using the MatNavi NIMS dataset for BCC Fe-alloys as the experimental source
EXPERIMENTAL_DATA_URL = "https://matnavi.nims.go.jp/data/000000000001/000000000001.csv"

# Fallback or alternative source if the primary is restricted, 
# pointing to a known public dataset structure if available.
# For this implementation, we rely on the URL defined above or local raw data.

# Model Configuration
MODEL_SEED = SEED
CV_FOLDS = 5
MAX_ITERATIONS = 1000

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = DIR_DATA_PROVENANCE / "pipeline.log"
PROVENANCE_FILE = DIR_DATA_PROVENANCE / "dft_queries.jsonl"

# Configuration Object
class Config:
    def __init__(self):
        self.ROOT = PROJECT_ROOT
        self.SEED = SEED
        self.ERR_INSUFFICIENT_DATA = ERR_INSUFFICIENT_DATA
        self.ERR_API_UNAVAILABLE = ERR_API_UNAVAILABLE
        self.ERR_FILE_NOT_FOUND = ERR_FILE_NOT_FOUND
        
        self.DIR_CODE = DIR_CODE
        self.DIR_DATA = DIR_DATA
        self.DIR_DATA_RAW = DIR_DATA_RAW
        self.DIR_DATA_INTERMEDIATE = DIR_DATA_INTERMEDIATE
        self.DIR_DATA_PROCESSED = DIR_DATA_PROCESSED
        self.DIR_DATA_PROVENANCE = DIR_DATA_PROVENANCE
        self.DIR_DATA_RESULTS = DIR_DATA_RESULTS
        self.DIR_TESTS = DIR_TESTS
        self.DIR_TESTS_UNIT = DIR_TESTS_UNIT
        self.DIR_TESTS_INTEGRATION = DIR_TESTS_INTEGRATION
        self.DIR_TESTS_CONTRACT = DIR_TESTS_CONTRACT
        self.DIR_SPECS = DIR_SPECS
        self.DIR_CONTRACTS = DIR_CONTRACTS
        
        self.MP_API_KEY = get_mp_api_key()
        self.EXPERIMENTAL_DATA_URL = EXPERIMENTAL_DATA_URL
        
        self.MODEL_SEED = MODEL_SEED
        self.CV_FOLDS = CV_FOLDS
        self.MAX_ITERATIONS = MAX_ITERATIONS
        
        self.LOG_LEVEL = LOG_LEVEL
        self.LOG_FILE = LOG_FILE
        self.PROVENANCE_FILE = PROVENANCE_FILE

# Global instance
CONFIG = Config()

if __name__ == "__main__":
    # Validate configuration
    print(f"Project Root: {CONFIG.ROOT}")
    print(f"Seed: {CONFIG.SEED}")
    print(f"MP API Key present: {CONFIG.MP_API_KEY is not None}")
    print(f"Experimental Data URL: {CONFIG.EXPERIMENTAL_DATA_URL}")
    print("Ensuring directories...")
    ensure_dirs()
    print("Directories ready.")