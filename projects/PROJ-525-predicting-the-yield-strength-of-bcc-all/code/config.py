"""
Configuration management for the BCC Yield Strength project.
Defines path constants based on project root structure.
Supports .env file for environment-specific overrides.
"""
import os
from pathlib import Path

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional; if not installed, proceed without .env support
    pass

# Determine project root (assuming this file is at code/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths (can be overridden via env vars: DATA_RAW_DIR, etc.)
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", PROJECT_ROOT / "data" / "raw"))
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", PROJECT_ROOT / "data" / "processed"))
CODE_DIR = Path(os.getenv("CODE_DIR", PROJECT_ROOT / "code"))
TESTS_DIR = Path(os.getenv("TESTS_DIR", PROJECT_ROOT / "tests"))
FIGURES_DIR = Path(os.getenv("FIGURES_DIR", PROJECT_ROOT / "figures"))

# Ensure directories exist (idempotent)
def ensure_dirs():
    """Create all configured data and output directories if they do not exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Run on import to ensure structure exists immediately
ensure_dirs()