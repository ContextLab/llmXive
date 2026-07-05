"""
Configuration module for the Statistical Evaluation of Dimensionality Reduction Pipeline.

This module handles:
- Path definitions for data, processed data, and results.
- Global random seed management for reproducibility.
- Dataset accessions (GEO IDs) and their metadata.
- Runtime flags (e.g., CASE_STUDY_MODE).
- Source verification and fallback logic for data acquisition.
"""

import os
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# --- Project Root & Path Definitions ---
# Determine the project root based on the location of this file
_CURRENT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = _CURRENT_DIR.parent

# Define standard directories relative to project root
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
CODE_DIR = PROJECT_ROOT / "code"

# Ensure directories exist (lazy initialization)
def ensure_paths():
    """Creates the necessary directory structure if it doesn't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# --- Global Random Seeds ---
# Default seed for reproducibility across the pipeline
GLOBAL_RANDOM_SEED = 42

def set_global_seed(seed: Optional[int] = None):
    """
    Sets the global random seed for numpy, random, and torch (if available).
    
    Args:
        seed: The seed value. If None, uses GLOBAL_RANDOM_SEED.
    """
    if seed is None:
        seed = GLOBAL_RANDOM_SEED
    
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


# --- Dataset Configuration ---
# Primary list of GEO accessions required for the study
TARGET_ACCESSIONS: List[str] = [
    "GSE131907",
    "GSE111322",
    "GSE150728"
]

# Mapping of accession to specific download parameters or metadata if needed
# Currently using standard GEO structure, but extensible
DATASET_METADATA: Dict[str, Dict] = {
    "GSE131907": {
        "description": "Human PBMC scRNA-seq",
        "target_cells": 10000, # Target for sampling if > 10k
    },
    "GSE111322": {
        "description": "Mouse Brain scRNA-seq",
        "target_cells": 10000,
    },
    "GSE150728": {
        "description": "Human Tumor Microenvironment",
        "target_cells": 10000,
    }
}

def get_accession_seed(accession: str) -> int:
    """
    Generates a deterministic random seed based on the accession string.
    This ensures that sampling operations for a specific dataset are reproducible
    regardless of the global seed state.
    
    Args:
        accession: The GEO accession string (e.g., "GSE131907").
    
    Returns:
        An integer seed derived from the hash of the accession.
    """
    hash_obj = hashlib.sha256(accession.encode('utf-8'))
    return int(hash_obj.hexdigest(), 16) % (2**32 - 1)


# --- Runtime Flags ---
# Flag to indicate if the pipeline is running in "Case Study" mode
# (i.e., fewer than the required 3 datasets were found)
CASE_STUDY_MODE: bool = False

def set_case_study_mode(mode: bool):
    """
    Updates the global CASE_STUDY_MODE flag.
    
    Args:
        mode: True if running with limited datasets, False otherwise.
    """
    global CASE_STUDY_MODE
    CASE_STUDY_MODE = mode


# --- Resource Constraints ---
# Maximum RAM usage in GB before aborting (FR-010)
MAX_RAM_GB = 7.0

# Maximum runtime in seconds (optional hard limit)
MAX_RUNTIME_SECONDS = None  # No hard limit by default, can be set via env

# --- Data Source Configuration (T053) ---
# Verified primary sources (GEO FTP/HTTP)
VERIFIED_SOURCES: List[Dict[str, str]] = [
    {
        "type": "geo_ftp",
        "base_url": "ftp.ncbi.nlm.nih.gov/geo/series",
        "priority": 1,
        "description": "Primary GEO FTP server for raw count matrices"
    },
    {
        "type": "geo_http",
        "base_url": "https://ftp.ncbi.nlm.nih.gov/geo/series",
        "priority": 2,
        "description": "HTTP fallback for GEO FTP"
    }
]

# Fallback sources if primary sources fail
FALLBACK_SOURCES: List[Dict[str, str]] = [
    {
        "type": "ucimlrepo",
        "base_url": "https://archive.ics.uci.edu/static/public",
        "priority": 1,
        "description": "UCI Machine Learning Repository as fallback for scRNA-seq datasets",
        "search_params": {"category": "Gene Expression"}
    },
    {
        "type": "figshare",
        "base_url": "https://figshare.com",
        "priority": 2,
        "description": "Figshare repository for supplementary datasets",
        "search_params": {"keywords": "scRNA-seq, count matrix"}
    }
]

def get_source_priority(source_type: str) -> int:
    """
    Returns the priority of a source type.
    
    Args:
        source_type: The type of source (e.g., 'geo_ftp', 'ucimlrepo').
    
    Returns:
        The priority integer (lower is higher priority). Returns 999 if not found.
    """
    # Check verified sources first
    for source in VERIFIED_SOURCES:
        if source["type"] == source_type:
            return source["priority"]
    
    # Check fallback sources
    for source in FALLBACK_SOURCES:
        if source["type"] == source_type:
            return source["priority"] + 100  # Fallbacks have higher numbers (lower priority)
    
    return 999

def get_all_sources_sorted() -> List[Dict[str, str]]:
    """
    Returns all sources sorted by priority (verified first, then fallbacks).
    
    Returns:
        A list of source dictionaries sorted by priority.
    """
    all_sources = VERIFIED_SOURCES + FALLBACK_SOURCES
    return sorted(all_sources, key=lambda x: x["priority"])

def is_verified_source(source_type: str) -> bool:
    """
    Checks if a source type is in the verified sources list.
    
    Args:
        source_type: The type of source to check.
    
    Returns:
        True if the source is verified, False otherwise.
    """
    return any(source["type"] == source_type for source in VERIFIED_SOURCES)

# --- Configuration Helper ---
class Config:
    """
    A simple namespace to access configuration values consistently.
    """
    @staticmethod
    def get_raw_path(accession: str) -> Path:
        """Returns the expected path for a raw dataset."""
        return DATA_RAW_DIR / accession

    @staticmethod
    def get_processed_path(accession: str) -> Path:
        """Returns the expected path for a processed dataset."""
        return DATA_PROCESSED_DIR / f"{accession}_processed.h5ad"

    @staticmethod
    def get_result_path(filename: str) -> Path:
        """Returns the path for a result file."""
        return RESULTS_DIR / filename

    @staticmethod
    def get_figure_path(filename: str) -> Path:
        """Returns the path for a figure file."""
        return FIGURES_DIR / filename

    @staticmethod
    def is_case_study() -> bool:
        """Returns the current case study mode status."""
        return CASE_STUDY_MODE

    @staticmethod
    def get_verified_sources() -> List[Dict[str, str]]:
        """Returns the list of verified sources."""
        return VERIFIED_SOURCES

    @staticmethod
    def get_fallback_sources() -> List[Dict[str, str]]:
        """Returns the list of fallback sources."""
        return FALLBACK_SOURCES

    @staticmethod
    def get_source_by_type(source_type: str) -> Optional[Dict[str, str]]:
        """
        Returns a source dictionary by its type.
        
        Args:
            source_type: The type of source to find.
        
        Returns:
            The source dictionary if found, None otherwise.
        """
        for source in VERIFIED_SOURCES + FALLBACK_SOURCES:
            if source["type"] == source_type:
                return source
        return None

# Initialize paths on module load to ensure structure exists
ensure_paths()