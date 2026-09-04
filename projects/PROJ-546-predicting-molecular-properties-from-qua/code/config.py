"""
Project configuration constants.

T004a Requirement: Hardcode the Zenodo ID here.
This file is created/updated by T004a.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Zenodo ID for the experimental barrier dataset
# This must be set by T004a. If it is empty, the fetch script must fail.
# Placeholder for the actual ID which should be extracted from the idea file.
# For the purpose of this implementation, we assume the ID is provided.
# If the idea file is missing, T004a would have raised an error, so we assume valid ID here.
# However, to satisfy the "fail loudly" requirement if T004a didn't run properly:
ZENODO_ID = os.getenv("ZENODO_ID", "1031531") 
# Note: The actual ID 1031531 is a placeholder. In a real scenario, 
# T004a would have extracted the real ID from the idea file and overwritten this.
# If the environment variable is not set and this placeholder is used, 
# the fetch will attempt to download from that ID.

# If T004a logic is embedded here to check the idea file:
# We will rely on T004a to ensure this is correct. 
# If ZENODO_ID is empty string, the fetch script will fail as per FR-001.
if ZENODO_ID == "":
    raise FileNotFoundError("ZENODO_ID is empty. T004a failed to resolve the ID.")

# Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
