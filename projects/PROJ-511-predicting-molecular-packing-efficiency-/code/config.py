"""
Environment configuration for the molecular packing efficiency pipeline.

Defines constants and environment variable accessors for:
- Crystallography Open Database (COD) download URL
- HuggingFace model path for SMILES tokenization
- Local data directories
"""

import os
from typing import Optional

# --- External Data Sources ---

# COD Base URL for CIF downloads
# Using the public API endpoint for search and download
COD_BASE_URL: str = "https://www.crystallography.net/cod"
COD_SEARCH_API: str = "https://www.crystallography.net/cod/search.php"
COD_DOWNLOAD_TEMPLATE: str = "https://www.crystallography.net/cod/{id}.cif.gz"

# HuggingFace Model Configuration
# Frozen model for SMILES BPE tokenization (as per FR-004 and T024)
HF_MODEL_NAME: str = "seyonec/PubChem10M_SMILES_BPE_60k"
HF_CACHE_DIR: Optional[str] = os.getenv("HF_HOME", None)

# --- Local Paths (Relative to Project Root) ---

# Ensure these match the directory structure created in T001
PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
RAW_CIF_DIR: str = os.path.join(DATA_DIR, "raw_cif")
MODELS_DIR: str = os.path.join(PROJECT_ROOT, "models")
RESULTS_DIR: str = os.path.join(PROJECT_ROOT, "results")

# --- Runtime Constraints ---

# Maximum number of CIFs to fetch in a single batch (safety limit)
MAX_CIF_BATCH_SIZE: int = 500

# Timeout for network requests (seconds)
REQUEST_TIMEOUT: int = 30

# --- Initialization ---

def ensure_directories() -> None:
    """
    Create necessary data directories if they do not exist.
    This function is idempotent and safe to call at the start of any pipeline step.
    """
    for directory in [DATA_DIR, RAW_CIF_DIR, MODELS_DIR, RESULTS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)