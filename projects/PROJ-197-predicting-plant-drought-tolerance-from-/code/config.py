"""
Configuration management for the project.

Manages species lists, random seeds, and execution modes.
"""
import os
import random
from typing import Dict, List, Any, Optional
import numpy as np
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_LOGS = PROJECT_ROOT / "data" / "logs"
DOCS_REPORTS = PROJECT_ROOT / "docs" / "reports"

# Execution Mode
# If True: allow synthetic data fallback if real fetch fails.
# If False: fail loudly (raise critical error) if real fetch fails.
VALIDATION_MODE = os.getenv("VALIDATION_MODE", "True").lower() == "true"

# Species List (Sample)
SPECIES_LIST = [
    "Arabidopsis_thaliana",
    "Oryza_sativa",
    "Zea_mays",
    "Sorghum_bicolor",
    "Triticum_aestivum",
    "Hordeum_vulgare",
    "Brachypodium_distachyon",
    "Setaria_italica",
    "Panicum_virgatum",
    "Saccharum_officinarum",
    "Glycine_max",
    "Medicago_truncatula",
    "Lotus_japonicus",
    "Vitis_vinifera",
    "Populus_trichocarpa",
    "Solanium_lycopersicum",
    "Solanum_tuberosum",
    "Capsicum_annuum",
    "Cucumis_sativus",
    "Cucurbita_ maxima",
    "Brassica_oleracea",
    "Raphanus_sativus",
    "Pisum_sativum",
    "Cicer_arietinum",
    "Cajanus_cajan"
]

# Training Genes (20)
TRAINING_GENES = [
    "NCED3", "ABF3", "P5CS", "DREB2A", "ERF1",
    "ABI5", "RD29A", "COR15A", "LEA3", "HSP70",
    "SOD", "APX1", "CAT1", "GPX1", "MDHAR",
    "DHAR", "GSTU", "ZAT12", "WRKY33", "MYB96"
]

# Validation Genes (15) - Disjoint from Training Genes
VALIDATION_GENES = [
    "ABF2", "DREB1B", "NAC072", "WRKY40", "bZIP28",
    "bZIP63", "ABI1", "ABI2", "PP2CA", "SnRK2.1",
    "SnRK2.5", "SnRK2.7", "RD26", "RD29B", "COR15B"
]

# Random Seed
RANDOM_SEED = 42

# Synthetic Data Parameters
SYNTHETIC_PARAMS = {
    "n_samples": len(SPECIES_LIST),
    "noise_level": 0.1
}

def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return {
        "species_list": SPECIES_LIST,
        "training_genes": TRAINING_GENES,
        "validation_genes": VALIDATION_GENES,
        "random_seed": RANDOM_SEED,
        "synthetic_params": SYNTHETIC_PARAMS,
        "validation_mode": VALIDATION_MODE
    }

def validate_config() -> bool:
    """Validate configuration."""
    # Check disjointness of training and validation genes
    train_set = set(TRAINING_GENES)
    val_set = set(VALIDATION_GENES)
    if train_set.intersection(val_set):
        raise ValueError("Training and validation genes must be disjoint.")
    return True

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for dir_path in [DATA_RAW, DATA_PROCESSED, DATA_LOGS, DOCS_REPORTS]:
        dir_path.mkdir(parents=True, exist_ok=True)

def check_fetch_status(url: str) -> bool:
    """Check if a URL is accessible."""
    import requests
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

# Initialize random seeds
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
