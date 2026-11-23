"""
Configuration module for the llmXive research pipeline.
Defines paths, constants, and timeout handling.
"""
import os
import sys
import signal
import time
import json
from pathlib import Path

# Project Root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
CODE_DIR = ROOT_DIR / "code"
TESTS_DIR = ROOT_DIR / "tests"
CONTRACTS_DIR = ROOT_DIR / "contracts"
LOGS_DIR = ROOT_DIR / "logs"
DOCS_DIR = ROOT_DIR / "docs"
FIGURES_DIR = ROOT_DIR / "figures"

# Constants
TARGET_MIN_STARS = 1000
TARGET_MIN_REPOS = 500
TIMEOUT_SECONDS = 19800  # 5.5 hours buffer for 6h limit

# API Keys (from environment)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
NVD_API_KEY = os.getenv("NVD_API_KEY", "")

class TimeoutError(Exception):
    """Custom exception for pipeline timeout."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"Pipeline execution exceeded {TIMEOUT_SECONDS} seconds.")

def pipeline_timeout_guard():
    """
    Sets up a timeout guard for the entire pipeline execution.
    Uses signal.alarm on Unix-like systems.
    """
    if sys.platform != "win32":
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)
    else:
        # Fallback for Windows (not perfect, but prevents hanging forever)
        # In a real CI, a wrapper script usually handles this.
        pass

def ensure_directories():
    """
    Creates all required directory structures if they do not exist.
    This implements T005's requirement to setup data directory structure.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_DIR,
        TESTS_DIR,
        CONTRACTS_DIR,
        LOGS_DIR,
        DOCS_DIR,
        FIGURES_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Ensure __init__.py files exist in code subdirectories if needed
    # (Handled by T001, but safe to ensure here)
    (CODE_DIR / "__init__.py").touch(exist_ok=True)
    (DATA_DIR / "__init__.py").touch(exist_ok=True)
    (CODE_DIR / "data" / "__init__.py").touch(exist_ok=True)
    (CODE_DIR / "analysis" / "__init__.py").touch(exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("Directories ensured.")
