"""
Configuration management for the pipeline.
"""
import os
from typing import Optional
from pathlib import Path

def get_base_dir() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_base_dir() / "data"

def get_models_dir() -> Path:
    """Get the models directory path."""
    return get_base_dir() / "models"

def get_results_dir() -> Path:
    """Get the results directory path."""
    return get_base_dir() / "results"

def get_cod_url() -> str:
    """Get the Crystallography Open Database URL."""
    return os.getenv("COD_URL", "https://www.crystallography.net/cod/")

def get_hf_model_path() -> str:
    """Get the HuggingFace model path."""
    return os.getenv("HF_MODEL_PATH", "seyonec/PubChem10M_SMILES_BPE_60k")

def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    dirs = [
        get_data_dir(),
        get_models_dir(),
        get_results_dir(),
        get_base_dir() / "data" / "raw_cif"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
