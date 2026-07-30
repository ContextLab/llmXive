"""
Environment configuration for the molecular packing efficiency project.

Defines constants for external data sources (COD URL) and model paths (HuggingFace).
These values are used by download_cif.py and feature_assembly.py.
"""
import os
from typing import Optional

# --- External Data Sources ---
# Crystallography Open Database (COD) search API URL
# Used by download_cif.py to fetch CIF files
COD_SEARCH_URL = "https://www.crystallography.net/cod/search.json"

# HuggingFace model repository for SMILES tokenization
# Used by feature_assembly.py to encode SMILES strings
HF_MODEL_PATH = "seyonec/PubChem10M_SMILES_BPE_60k"

# --- Local Paths ---
# Base directory for project artifacts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_CIF_DIR = os.path.join(DATA_DIR, "raw_cif")
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CONTRACTS_DIR = os.path.join(BASE_DIR, "contracts")
SPECS_DIR = os.path.join(BASE_DIR, "specs")

def ensure_directories() -> None:
    """
    Creates all required project directories if they do not exist.
    Ensures the project structure required by T001 is present.
    """
    directories = [
        DATA_DIR,
        RAW_CIF_DIR,
        MODELS_DIR,
        RESULTS_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
        os.path.join(BASE_DIR, "code"),
        os.path.join(BASE_DIR, "tests"),
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
          os.makedirs(directory)
          print(f"Created directory: {directory}")