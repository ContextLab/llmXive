import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Allowed family‑wise error correction methods
ALLOWED_FWE_METHODS = {"max-t", "bonferroni"}

@dataclass
class Config:
    WINDOW_SIZES: List[int] = None
    STEP: int = 5
    ATLAS_PATH: Optional[str] = None
    DATA_PATH: Optional[str] = None
    FWE_METHOD: str = "max-t"

    def __post_init__(self):
        if self.WINDOW_SIZES is None:
            # Default window lengths (in seconds) used throughout the pipeline
            self.WINDOW_SIZES = [20, 30, 40]

_config: Optional[Config] = None

def get_config() -> Config:
    """Return a singleton Config instance, optionally overridden by environment variables.

    Environment variables:
        WINDOW_SIZES – comma‑separated list of integers (e.g. "20,30,40")
        STEP – integer step size between sliding windows
        ATLAS_PATH – path to the brain atlas file
        DATA_PATH – root data directory
        FWE_METHOD – family‑wise error correction method (must be in ALLOWED_FWE_METHODS)
    """
    global _config
    if _config is None:
        _config = Config()
        # Load from a .env file if present
        if os.path.exists(".env"):
            from dotenv import load_dotenv

            load_dotenv()

        if "WINDOW_SIZES" in os.environ:
            _config.WINDOW_SIZES = [
                int(x) for x in os.environ["WINDOW_SIZES"].split(",")
            ]
        if "STEP" in os.environ:
            _config.STEP = int(os.environ["STEP"])
        if "ATLAS_PATH" in os.environ:
            _config.ATLAS_PATH = os.environ["ATLAS_PATH"]
        if "DATA_PATH" in os.environ:
            _config.DATA_PATH = os.environ["DATA_PATH"]
        if "FWE_METHOD" in os.environ:
            _config.FWE_METHOD = os.environ["FWE_METHOD"]

    return _config

def validate_fwe_config() -> None:
    """Validate the FWE_METHOD configured in the Config.

    Raises
    ------
    ValueError
        If the configured FWE_METHOD is not among the allowed methods.
    """
    cfg = get_config()
    if cfg.FWE_METHOD not in ALLOWED_FWE_METHODS:
        allowed = ", ".join(sorted(ALLOWED_FWE_METHODS))
        raise ValueError(
            f"Invalid FWE_METHOD '{cfg.FWE_METHOD}'. Allowed values are: {allowed}."
        )
