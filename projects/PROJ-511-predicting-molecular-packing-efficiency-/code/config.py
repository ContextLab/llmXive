import os
from typing import Optional
from pathlib import Path

# Default configuration values
DEFAULT_COD_URL = "https://www.crystallography.net/cod/"
DEFAULT_HF_MODEL_PATH = "seyonec/PubChem10M_SMILES_BPE_60k"
DEFAULT_DATA_DIR = "data"
DEFAULT_MODELS_DIR = "models"
DEFAULT_RESULTS_DIR = "results"

def ensure_directories(base_path: Optional[Path] = None) -> None:
    """
    Ensure that required project directories exist.
    
    Args:
        base_path: Base path for directories (defaults to project root)
    """
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code",
        base_path / "data",
        base_path / "data" / "raw_cif",
        base_path / "models",
        base_path / "results",
        base_path / "contracts",
        base_path / "specs"
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_cod_url() -> str:
    """Get the COD download URL from environment or default."""
    return os.getenv("COD_URL", DEFAULT_COD_URL)

def get_hf_model_path() -> str:
    """Get the HuggingFace model path from environment or default."""
    return os.getenv("HF_MODEL_PATH", DEFAULT_HF_MODEL_PATH)

def get_data_dir() -> Path:
    """Get the data directory path."""
    base_path = Path(__file__).resolve().parent.parent
    return base_path / "data"

def get_models_dir() -> Path:
    """Get the models directory path."""
    base_path = Path(__file__).resolve().parent.parent
    return base_path / "models"

def get_results_dir() -> Path:
    """Get the results directory path."""
    base_path = Path(__file__).resolve().parent.parent
    return base_path / "results"
