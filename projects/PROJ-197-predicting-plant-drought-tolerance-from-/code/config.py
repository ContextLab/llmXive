"""
Configuration management for the Drought Tolerance Prediction pipeline.

This module centralizes species lists, random seeds, and synthetic data parameters
to ensure reproducibility and consistency across the pipeline.
"""

import os
from typing import Dict, List, Any, Optional

# ============================================================================
# Random Seeds (Reproducibility)
# ============================================================================
# Centralized random seed as per T006 requirements.
# Used for synthetic data generation, train/test splitting, and model initialization.
RANDOM_SEED: int = 42

# ============================================================================
# Species Lists
# ============================================================================
# List of target species for the study.
# In a real scenario, this would be populated from the TRY database or a specific
# study list. For now, we define a placeholder list that can be extended.
TARGET_SPECIES: List[str] = [
    "Arabidopsis thaliana",
    "Oryza sativa",
    "Zea mays",
    "Sorghum bicolor",
    "Triticum aestivum",
    "Glycine max",
    "Medicago truncatula",
    "Populus trichocarpa",
    "Vitis vinifera",
    "Solanum lycopersicum",
    "Brachypodium distachyon",
    "Setaria italica",
    "Panicum virgatum",
    "Saccharum officinarum",
    "Hordeum vulgare",
    "Sesamum indicum",
    "Cicer arietinum",
    "Gossypium raimondii",
    "Salix purpurea",
    "Eucalyptus grandis",
]

# ============================================================================
# Synthetic Data Parameters
# ============================================================================
# Parameters for generating synthetic genomic data and labels (T012, T016)
SYNTHETIC_CONFIG: Dict[str, Any] = {
    # Number of synthetic samples to generate if no real data is found
    "num_samples": 500,
    # Standard deviation for noise in synthetic physiological traits
    "trait_noise_std": 0.1,
    # Lower bound for synthetic phylogenetic distance matrix (T016)
    "phylo_dist_min": 0.01,
    # Upper bound for synthetic phylogenetic distance matrix (T016)
    "phylo_dist_max": 1.0,
    # Threshold for genomic marker sum to determine drought tolerance label (T012)
    # label = 1 if sum(genomic_markers) >= threshold
    "label_threshold": 12,
    # Number of genomic markers to simulate per species
    "num_genomic_markers": 20,
}

# ============================================================================
# Gene Lists
# ============================================================================
# Full list of 20 genomic markers for synthetic generation (T012)
GENOMIC_MARKER_LIST: List[str] = [
    "NCED3", "ABF3", "P5CS", "DREB2A", "ERF1",
    "ABI5", "RD29A", "COR15A", "LEA3", "HSP70",
    "SOD", "APX1", "CAT1", "GPX1", "MDHAR",
    "DHAR", "GSTU", "ZAT12", "WRKY33", "MYB96",
]

# Validation gene list for final report analysis (T029)
# Subset of 15 genes used for feature importance validation
VALIDATION_GENE_LIST: List[str] = [
    "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A",
    "LEA3", "HSP70", "SOD", "APX1", "CAT1",
    "GPX1", "MDHAR", "DHAR", "GSTU", "ZAT12",
]

# ============================================================================
# Model Training Parameters
# ============================================================================
# Default hyperparameter search space for n_estimators (T020c)
N_ESTIMATORS_GRID: List[int] = [100, 200, 500]

# KNN Baseline parameters (T021)
KNN_BASELINE_K: int = 5

# ============================================================================
# Data Paths
# ============================================================================
# Base directory for data artifacts
DATA_ROOT: str = "data"
RAW_DATA_DIR: str = os.path.join(DATA_ROOT, "raw")
PROCESSED_DATA_DIR: str = os.path.join(DATA_ROOT, "processed")
LOGS_DIR: str = os.path.join(DATA_ROOT, "logs")

# Output file paths
SYNTHETIC_GENOMICS_PATH: str = os.path.join(PROCESSED_DATA_DIR, "synthetic_genomics.csv")
SYNTHETIC_PHYLO_MATRIX_PATH: str = os.path.join(PROCESSED_DATA_DIR, "synthetic_phylo_matrix.npy")
MERGED_DATASET_PATH: str = os.path.join(PROCESSED_DATA_DIR, "merged_dataset.csv")
METRICS_PATH: str = os.path.join(LOGS_DIR, "metrics.json")

# ============================================================================
# Utility Functions
# ============================================================================
def get_config() -> Dict[str, Any]:
    """Return a dictionary of all configuration parameters."""
    return {
        "random_seed": RANDOM_SEED,
        "target_species": TARGET_SPECIES,
        "synthetic_config": SYNTHETIC_CONFIG,
        "genomic_marker_list": GENOMIC_MARKER_LIST,
        "validation_gene_list": VALIDATION_GENE_LIST,
        "n_estimators_grid": N_ESTIMATORS_GRID,
        "knn_baseline_k": KNN_BASELINE_K,
        "data_paths": {
            "raw": RAW_DATA_DIR,
            "processed": PROCESSED_DATA_DIR,
            "logs": LOGS_DIR,
            "synthetic_genomics": SYNTHETIC_GENOMICS_PATH,
            "synthetic_phylo_matrix": SYNTHETIC_PHYLO_MATRIX_PATH,
            "merged_dataset": MERGED_DATASET_PATH,
            "metrics": METRICS_PATH,
        },
    }

def validate_config() -> bool:
    """
    Validate that all critical configuration values are present and valid.
    Returns True if valid, raises ValueError otherwise.
    """
    if not isinstance(RANDOM_SEED, int) or RANDOM_SEED < 0:
        raise ValueError("RANDOM_SEED must be a non-negative integer.")
    
    if not isinstance(TARGET_SPECIES, list) or len(TARGET_SPECIES) == 0:
        raise ValueError("TARGET_SPECIES must be a non-empty list.")
    
    if not isinstance(GENOMIC_MARKER_LIST, list) or len(GENOMIC_MARKER_LIST) != 20:
        raise ValueError("GENOMIC_MARKER_LIST must contain exactly 20 markers.")
    
    if not isinstance(VALIDATION_GENE_LIST, list) or len(VALIDATION_GENE_LIST) != 15:
        raise ValueError("VALIDATION_GENE_LIST must contain exactly 15 markers.")
    
    if not isinstance(SYNTHETIC_CONFIG, dict):
        raise ValueError("SYNTHETIC_CONFIG must be a dictionary.")
    
    return True

# Ensure directories exist on import (optional safety check)
def ensure_directories() -> None:
    """Create data directories if they do not exist."""
    for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
        os.makedirs(path, exist_ok=True)

# Run directory check on module load
ensure_directories()