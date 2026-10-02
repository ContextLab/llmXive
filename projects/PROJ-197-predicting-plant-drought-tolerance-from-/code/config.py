"""
Configuration management for the drought tolerance prediction pipeline.
Handles species lists, random seeds, and execution modes.
"""
import os
import random
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path

# Global Configuration
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Execution Modes
# If True: allow synthetic data fallback if real fetch fails (for validation/testing)
# If False: fail loudly on real fetch failure (Production mode)
VALIDATION_MODE = os.environ.get("VALIDATION_MODE", "False").lower() == "true"

# Species List (Example subset)
SPECIES_LIST = [
    "Arabidopsis thaliana",
    "Solanum lycopersicum",
    "Oryza sativa",
    "Zea mays",
    "Glycine max",
    "Triticum aestivum",
    "Populus trichocarpa",
    "Vitis vinifera",
    "Medicago truncatula",
    "Brachypodium distachyon"
]

# Gene Lists
TRAINING_GENES = [
    "NCED3", "ABF3", "P5CS", "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A", "LEA3", "HSP70",
    "SOD", "APX1", "CAT1", "GPX1", "MDHAR", "DHAR", "GSTU", "ZAT12", "WRKY33", "MYB96"
]

# 15 Independent Validation Genes (Strictly disjoint from TRAINING_GENES)
# ABA-signaling genes not used in the synthetic label generation (T012)
VALIDATION_GENES = [
    "ABF2", "DREB1B", "NAC072", "WRKY40", "bZIP28", "bZIP63", "ABI1", "ABI2", "PP2CA",
    "SnRK2.1", "SnRK2.5", "SnRK2.7", "RD26", "RD29B", "COR15B"
]

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"
FIGURES_DIR = BASE_DIR / "figures"
CODE_DIR = BASE_DIR / "code"

def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return {
        "random_seed": RANDOM_SEED,
        "validation_mode": VALIDATION_MODE,
        "species_list": SPECIES_LIST,
        "training_genes": TRAINING_GENES,
        "validation_genes": VALIDATION_GENES,
        "paths": {
            "base": str(BASE_DIR),
            "data": str(DATA_DIR),
            "raw": str(RAW_DIR),
            "processed": str(PROCESSED_DIR),
            "logs": str(LOGS_DIR),
            "figures": str(FIGURES_DIR),
            "code": str(CODE_DIR)
        }
    }

def validate_config() -> bool:
    """Validate the current configuration."""
    # Check if required directories exist (or can be created)
    for path_str in get_config()["paths"].values():
        if path_str:
            p = Path(path_str)
            if not p.exists():
                # Allow creation
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception:
                    return False
    return True

def ensure_directories(*args, **kwargs) -> None:
    """
    Ensure required directories exist.
    Accepts various call signatures for flexibility:
    - ensure_directories()
    - ensure_directories([path1, path2])
    - ensure_directories(path1, path2)
    - ensure_directories(config_dict)
    """
    paths_to_create = []

    if args:
        if isinstance(args[0], list):
            paths_to_create = args[0]
        elif isinstance(args[0], dict):
            # If a config dict is passed, extract paths
            if "paths" in args[0]:
                paths_to_create = list(args[0]["paths"].values())
            else:
                paths_to_create = list(args[0].values())
        else:
            paths_to_create = list(args)
    
    # Also check kwargs if passed
    if "paths" in kwargs:
        if isinstance(kwargs["paths"], list):
            paths_to_create.extend(kwargs["paths"])
        else:
            paths_to_create.append(kwargs["paths"])

    # Use default paths if none provided
    if not paths_to_create:
        config = get_config()
        paths_to_create = list(config["paths"].values())

    for path_str in paths_to_create:
        if path_str:
            p = Path(path_str)
            if not p.exists():
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    # Log error but don't necessarily crash if it's just a directory creation issue
                    # unless critical
                    pass

def check_fetch_status(status: str) -> bool:
    """Check if a fetch status is valid."""
    return status in ["SUCCESS", "FAILED", "RETRY"]

# Verification: Ensure no overlap between training and validation genes
def verify_gene_disjoint() -> bool:
    """
    Verify that VALIDATION_GENES are strictly disjoint from TRAINING_GENES.
    Returns True if disjoint, False otherwise.
    """
    training_set = set(TRAINING_GENES)
    validation_set = set(VALIDATION_GENES)
    overlap = training_set.intersection(validation_set)
    if overlap:
        raise ValueError(f"Gene overlap detected between training and validation sets: {overlap}")
    return True