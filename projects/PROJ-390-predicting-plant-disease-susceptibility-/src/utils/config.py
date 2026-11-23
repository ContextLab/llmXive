"""
Configuration management for the Plant Disease Susceptibility project.

Centralizes project paths, random seeds, species lists, and hyperparameters.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# --- Constants ---
RANDOM_SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

# Species Configuration
# Mapping species names to their Reference Genome Accession IDs
# Sources: NCBI RefSeq, Ensembl, Sol Genomics Network, Phytozome
SPECIES_ACCESSIONS = {
    "wheat": "GCA_000003205.5",
    "rice": "GCA_001433935.2",
    "maize": "GCA_000005005.4",
    "tomato": "GCA_000188115.5",
    "soybean": "GCA_000004195.3"
}

# Detailed species info including common names and expected data types
SPECIES_INFO = {
    "wheat": {
        "scientific_name": "Triticum aestivum",
        "accession_id": "GCA_000003205.5",
        "genome_size_gb": 15.0,
        "ploidy": 6,
        "primary_data_source": "NCBI RefSeq"
    },
    "rice": {
        "scientific_name": "Oryza sativa",
        "accession_id": "GCA_001433935.2",
        "genome_size_gb": 0.43,
        "ploidy": 2,
        "primary_data_source": "Ensembl"
    },
    "maize": {
        "scientific_name": "Zea mays",
        "accession_id": "GCA_000005005.4",
        "genome_size_gb": 2.3,
        "ploidy": 2,
        "primary_data_source": "NCBI RefSeq"
    },
    "tomato": {
        "scientific_name": "Solanum lycopersicum",
        "accession_id": "GCA_000188115.5",
        "genome_size_gb": 0.95,
        "ploidy": 2,
        "primary_data_source": "Sol Genomics Network"
    },
    "soybean": {
        "scientific_name": "Glycine max",
        "accession_id": "GCA_000004195.3",
        "genome_size_gb": 1.1,
        "ploidy": 4,
        "primary_data_source": "Phytozome"
    }
}

# Hyperparameters for the pipeline
HYPERPARAMETERS = {
    "knn_imputer": {
        "n_neighbors": 5
    },
    "model_training": {
        "max_grid_search_combinations": 50,
        "random_state": RANDOM_SEED
    },
    "validation": {
        "permutation_count": 1000,
        "permutation_seed": RANDOM_SEED
    },
    "data_split": {
        "train_ratio": 0.7,
        "val_ratio": 0.15,
        "test_ratio": 0.15
    }
}

def get_species_accession(species_name: str) -> str:
    """
    Retrieve the reference genome accession ID for a given species.
    
    Args:
        species_name: Lowercase name of the species (e.g., 'wheat', 'rice').
        
    Returns:
        The accession ID string.
        
    Raises:
        KeyError: If the species is not in the supported list.
    """
    if species_name not in SPECIES_ACCESSIONS:
        raise KeyError(f"Species '{species_name}' not found in configuration. Supported: {list(SPECIES_ACCESSIONS.keys())}")
    return SPECIES_ACCESSIONS[species_name]

def get_species_info(species_name: str) -> Dict[str, Any]:
    """
    Retrieve detailed information about a species.
    
    Args:
        species_name: Lowercase name of the species.
        
    Returns:
        Dictionary containing species metadata.
        
    Raises:
        KeyError: If the species is not in the supported list.
    """
    if species_name not in SPECIES_INFO:
        raise KeyError(f"Species '{species_name}' not found in configuration.")
    return SPECIES_INFO[species_name]

def ensure_paths_exist() -> None:
    """
    Ensure all required project directories exist.
    Creates them if they do not exist.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        MODELS_DIR,
        TEMPLATES_DIR,
        SRC_DIR,
        TESTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def save_config_to_json(output_path: Optional[Path] = None) -> Path:
    """
    Save the current configuration state to a JSON file.
    
    Args:
        output_path: Optional custom path. Defaults to data/processed/config_snapshot.json.
        
    Returns:
        The path to the saved file.
    """
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "config_snapshot.json"
    
    config_data = {
        "random_seed": RANDOM_SEED,
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "data_raw": str(DATA_RAW_DIR),
            "data_processed": str(DATA_PROCESSED_DIR),
            "models": str(MODELS_DIR),
            "templates": str(TEMPLATES_DIR)
        },
        "species": SPECIES_ACCESSIONS,
        "species_details": SPECIES_INFO,
        "hyperparameters": HYPERPARAMETERS
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
    
    return output_path
