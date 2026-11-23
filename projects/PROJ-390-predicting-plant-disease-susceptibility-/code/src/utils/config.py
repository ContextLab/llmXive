"""
Configuration management for the Plant Disease Susceptibility Project.

Provides centralized access to project paths, random seeds, and species lists.
Ensures consistent configuration across the pipeline.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Root directory of the project
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Random seed for reproducibility (FR-007, Constitution Principle)
RANDOM_SEED: int = 42

# Species configuration
# Mapping of common names to their reference genome accession IDs
SPECIES_CONFIG: Dict[str, Dict[str, Any]] = {
    "wheat": {
        "common_name": "Wheat",
        "scientific_name": "Triticum aestivum",
        "accession_id": "GCA_000003205.5",
        "source": "RefSeq"
    },
    "rice": {
        "common_name": "Rice",
        "scientific_name": "Oryza sativa",
        "accession_id": "GCA_001433935.2",
        "source": "Ensembl"
    },
    "maize": {
        "common_name": "Maize",
        "scientific_name": "Zea mays",
        "accession_id": "GCA_000005005.4",
        "source": "RefSeq"
    },
    "tomato": {
        "common_name": "Tomato",
        "scientific_name": "Solanum lycopersicum",
        "accession_id": "GCA_000188115.5",
        "source": "Sol Genomics Network (SL4.0)"
    },
    "soybean": {
        "common_name": "Soybean",
        "scientific_name": "Glycine max",
        "accession_id": "GCA_000004195.3",
        "source": "Phytozome (Wm82.a2.v1)"
    }
}

# List of supported species names
SUPPORTED_SPECIES: List[str] = list(SPECIES_CONFIG.keys())

# Path constants relative to root
PATHS: Dict[str, Path] = {
    "root": _ROOT_DIR,
    "src": _ROOT_DIR / "src",
    "tests": _ROOT_DIR / "tests",
    "data_raw": _ROOT_DIR / "data" / "raw",
    "data_processed": _ROOT_DIR / "data" / "processed",
    "models": _ROOT_DIR / "models",
    "templates": _ROOT_DIR / "templates",
    "figures": _ROOT_DIR / "figures",
    "specs": _ROOT_DIR / "specs",
}

# Hyperparameters and defaults
HYPERPARAMS: Dict[str, Any] = {
    "knn_neighbors": 5,
    "max_distance_km": 50,
    "ld_threshold": 0.8,
    "permutation_count": 1000,
    "validation_p_threshold": 0.05,
    "max_retries": 3,
    "batch_size": 100,
}

# Environment variable keys for sensitive data (optional overrides)
ENV_KEYS: Dict[str, str] = {
    "NCBI_EMAIL": "NCBI_EMAIL",
    "NCBI_API_KEY": "NCBI_API_KEY",
}

def get_species_accession(species_name: str) -> Optional[str]:
    """
    Retrieve the reference genome accession ID for a given species.
    
    Args:
        species_name: Common name of the species (e.g., 'wheat', 'rice').
        
    Returns:
        The accession ID string if found, None otherwise.
    """
    species_lower = species_name.lower()
    if species_lower in SPECIES_CONFIG:
        return SPECIES_CONFIG[species_lower]["accession_id"]
    return None

def get_species_info(species_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full configuration info for a species.
    
    Args:
        species_name: Common name of the species.
        
    Returns:
        Dictionary containing species info or None if not found.
    """
    species_lower = species_name.lower()
    return SPECIES_CONFIG.get(species_lower)

def ensure_paths_exist() -> None:
    """
    Create all required directory paths if they do not exist.
    This is a helper to ensure the file structure is ready before processing.
    """
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)

def save_config_to_json(output_path: Optional[Path] = None) -> Path:
    """
    Export the current configuration to a JSON file.
    
    Args:
        output_path: Optional path to save the config. Defaults to data/processed/config_snapshot.json.
        
    Returns:
        The path where the config was saved.
    """
    if output_path is None:
        output_path = PATHS["data_processed"] / "config_snapshot.json"
    
    config_data = {
        "random_seed": RANDOM_SEED,
        "supported_species": SUPPORTED_SPECIES,
        "species_details": SPECIES_CONFIG,
        "hyperparameters": HYPERPARAMS,
        "paths": {k: str(v) for k, v in PATHS.items()}
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
    
    return output_path

# Initialize paths on module load to ensure structure exists
# This is safe to call multiple times due to exist_ok=True
ensure_paths_exist()
