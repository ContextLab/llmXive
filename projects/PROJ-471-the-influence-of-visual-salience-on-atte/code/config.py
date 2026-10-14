"""
Configuration management for the Visual Salience project.
Defines paths, random seeds, and hyperparameters.
Loads environment variables using python-dotenv and validates required keys.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Attempt to import dotenv; if missing, log a warning but do NOT abort execution.
try:
    from dotenv import load_dotenv
except ImportError:
    logging.warning(
        "python-dotenv is not installed. Environment variables will be read from the "
        "system environment only. To use a .env file, add python-dotenv to requirements.txt."
    )
    load_dotenv = lambda *_args, **_kwargs: None  # type: ignore

# Project Root
_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env file in the project root if possible
_env_file = _ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    logging.warning(f".env file not found at {_env_file}. Ensure required keys are set in the environment.")

# --- Validation Logic ---
REQUIRED_ENV_KEYS = ["HF_TOKEN", "DATA_PATH", "SEED", "GPU_DEVICE"]

def _validate_env_vars() -> None:
    """
    Validates that all required environment variables are set and non‑empty.
    Logs a warning for any missing keys instead of raising an exception,
    allowing scripts that do not strictly need these variables (e.g., the
    ingestion script when the dataset is intentionally missing) to run.
    """
    missing_keys = []
    for key in REQUIRED_ENV_KEYS:
        val = os.getenv(key)
        if not val or val.strip() == "":
            missing_keys.append(key)

    if missing_keys:
        logging.warning(
            f"Missing optional environment variables: {', '.join(missing_keys)}. "
            "Proceeding with defaults where possible."
        )

# Perform validation immediately upon module load (warnings only)
_validate_env_vars()

# --- Paths ---
class Paths:
    ROOT: Path = _ROOT
    CODE: Path = _ROOT / "code"
    DATA: Path = _ROOT / "data"
    DATA_RAW: Path = DATA / "raw"
    DATA_INTERIM: Path = DATA / "interim"
    DATA_PROCESSED: Path = DATA / "processed"
    DATA_FIGURES: Path = _ROOT / "figures"
    DOCS: Path = _ROOT / "docs"
    SPEC: Path = _ROOT / "specs"

    # Specific subdirectories for artifacts
    SALIENCE_MAPS: Path = DATA_PROCESSED / "salience_maps"
    FIXATION_METRICS: Path = DATA_INTERIM
    ALIGNED_METRICS: Path = DATA_PROCESSED
    RESULTS: Path = DATA_PROCESSED

    @classmethod
    def ensure_dirs(cls):
        for path in [
            cls.DATA_RAW,
            cls.DATA_INTERIM,
            cls.DATA_PROCESSED,
            cls.DATA_FIGURES,
            cls.DOCS,
            cls.SALIENCE_MAPS,
        ]:
            path.mkdir(parents=True, exist_ok=True)

# --- Hyperparameters ---
class Hyperparams:
    # Random Seeds - Loaded from ENV with fallback to default if not strictly required by validation
    SEED: int = int(os.getenv("SEED", "42"))
    TORCH_SEED: int = SEED
    NUMPY_SEED: int = SEED

    # Salience Generation (DeepGaze II)
    SALIENCE_MODEL_NAME: str = "deepgaze2"
    SALIENCE_BATCH_SIZE: int = 16
    SALIENCE_DEVICE: str = os.getenv("GPU_DEVICE", "cpu")
    SALIENCE_MAX_MEMORY_GB: float = 6.0  # Safety margin under 7GB limit

    # Segmentation (YOLOv8)
    SEGMENTATION_MODEL_NAME: str = "yolov8n.pt"  # nano for speed
    SEGMENTATION_CONF_THRESHOLD: float = 0.25
    SEGMENTATION_IOU_THRESHOLD: float = 0.45
    SEGMENTATION_TARGET_CLASSES: list = None  # Initialized below

    # Analysis
    LMM_MAX_ITER: int = 1000
    FDR_METHOD: str = "fdr_bh"  # Benjamini-Hochberg
    VIF_THRESHOLD: float = 5.0
    POWER_TARGET: float = 0.80
    MIN_SAMPLE_SIZE: int = 30

    @classmethod
    def get(cls) -> Dict[str, Any]:
        return {
            "seed": cls.SEED,
            "salience_model": cls.SALIENCE_MODEL_NAME,
            "salience_device": cls.SALIENCE_DEVICE,
            "segmentation_model": cls.SEGMENTATION_MODEL_NAME,
            "vif_threshold": cls.VIF_THRESHOLD,
            "power_target": cls.POWER_TARGET,
        }

# Initialize default target classes for segmentation (Face only, Weapons excluded per SCR)
Hyperparams.SEGMENTATION_TARGET_CLASSES = ["face"]

# --- Global Config Loader ---
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file if provided, otherwise return defaults.
    Environment variables take precedence if set in the YAML or used for defaults.
    """
    if config_path is None:
        config_path = str(_ROOT / "config.yaml")

    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    return Hyperparams.get()

def get_seed() -> int:
    return Hyperparams.SEED

def get_paths() -> Paths:
    return Paths

def get_hyperparams() -> Dict[str, Any]:
    return Hyperparams.get()

# Immediate directory creation for safety
Paths.ensure_dirs()
