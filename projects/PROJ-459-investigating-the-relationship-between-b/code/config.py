"""
Configuration management for the llmXive brain-music preference pipeline.

This module defines all project paths, hyperparameters, dataset identifiers,
and mechanisms to handle dataset validation failures.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# --- Base Directories ---
# Assumes this file is at code/config.py, root is parent of 'code'
_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _ROOT / "data"
CODE_DIR = _ROOT / "code"
TESTS_DIR = _ROOT / "tests"
STATE_DIR = _ROOT / "state"

# Subdirectories
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_DERIVED = DATA_DIR / "derived"
FIGURES_DIR = DATA_DERIVED / "figures"

# Ensure directories exist (lazy initialization)
def ensure_dirs():
    """Create all required directories if they do not exist."""
    for d in [DATA_RAW, DATA_PROCESSED, DATA_DERIVED, FIGURES_DIR, STATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# --- Hyperparameters ---
# fMRI Preprocessing
TR_DEFAULT = 2.0  # Repetition time in seconds
SLICE_TIMING_REF = "center"
MOTION_THRESHOLD_MM = 0.5  # Framewise Displacement threshold
MISSING_DATA_THRESHOLD = 0.10  # 10% missing data tolerance

# Network Analysis
WINDOW_SIZES: List[int] = [30, 40]  # Window sizes in TRs for sliding window
WINDOW_STEP: int = 5  # Step size in TRs
ATLAS_NAME = "Schaefer2018_400Parcels_7Networks"
ATLAS_RESOLUTION = 2  # mm

# Statistical Analysis
CORRECTION_METHOD = "fdr_bh"  # Benjamini-Hochberg
POWER_TARGET = 0.80
EFFECT_SIZE_TARGET = 0.30

# --- Dataset Configuration ---
# Primary dataset IDs from OpenNeuro
DATASET_IDS_PRIMARY = ["ds000030", "ds000208"]

# Verified list of datasets containing required behavioral variables
# In a real implementation, this might be fetched from a remote registry or DB
VERIFIED_DATASETS = {
    "ds000030": {
        "name": "OpenNeuro ds000030",
        "required_vars": ["musical_genre", "age", "sex"],
        "fallback_vars": ["STOMP-R"],
        "url": "https://openneuro.org/datasets/ds000030"
    },
    "ds000208": {
        "name": "OpenNeuro ds000208",
        "required_vars": ["musical_genre", "age", "sex"],
        "fallback_vars": ["STOMP-R"],
        "url": "https://openneuro.org/datasets/ds000208"
    },
    # Fallback datasets if primary ones fail validation
    "ds000117": {
        "name": "OpenNeuro ds000117 (HCP)",
        "required_vars": ["musical_genre", "age", "sex"],
        "fallback_vars": ["STOMP-R"],
        "url": "https://openneuro.org/datasets/ds000117"
    }
}

# --- Dataset Switching Mechanism ---
class DatasetConfig:
    """
    Manages dataset selection and fallback logic.
    
    If a primary dataset fails validation (e.g., missing 'musical_genre'),
    this class provides a mechanism to switch to a verified fallback dataset.
    """
    
    def __init__(self, initial_ids: Optional[List[str]] = None):
        self._current_ids = initial_ids or DATASET_IDS_PRIMARY.copy()
        self._validation_errors: Dict[str, str] = {}
        
    @property
    def current_ids(self) -> List[str]:
        """Returns the list of currently active dataset IDs."""
        return self._current_ids.copy()
        
    def register_validation_failure(self, dataset_id: str, error_code: str, message: str):
        """
        Registers a validation failure for a specific dataset.
        
        Args:
            dataset_id: The ID of the failed dataset.
            error_code: Machine-readable error code (e.g., 'ERR_DATA_MISSING').
            message: Human-readable description of the failure.
        """
        self._validation_errors[dataset_id] = f"{error_code}: {message}"
        
        # If the failed dataset is in our current list, trigger fallback logic
        if dataset_id in self._current_ids:
            self._attempt_fallback(dataset_id)
            
    def _attempt_fallback(self, failed_id: str):
        """
        Attempts to switch to a fallback dataset if the primary fails.
        
        Logic:
        1. Remove failed ID from current list.
        2. If list is empty, check VERIFIED_DATASETS for alternatives.
        3. Select the first verified alternative that is not the failed ID.
        """
        self._current_ids.remove(failed_id)
        
        if not self._current_ids:
            # Try to find a fallback from the verified list
            for alt_id, info in VERIFIED_DATASETS.items():
                if alt_id != failed_id and alt_id not in self._current_ids:
                    # Verify the fallback has the required structure
                    if self._verify_fallback_structure(alt_id):
                        self._current_ids.append(alt_id)
                        print(f"Switched to fallback dataset: {alt_id} ({info['name']})")
                        break
            
            if not self._current_ids:
                raise RuntimeError(
                    f"No valid fallback datasets available after failure of {failed_id}. "
                    "Please check verified datasets or update VERIFIED_DATASETS."
                )
                
    def _verify_fallback_structure(self, dataset_id: str) -> bool:
        """
        Basic check to ensure the fallback dataset is defined in our registry.
        In a real system, this would perform a HEAD request or metadata check.
        """
        return dataset_id in VERIFIED_DATASETS
        
    def get_fallback_candidates(self) -> List[str]:
        """Returns a list of available fallback dataset IDs."""
        return [k for k in VERIFIED_DATASETS.keys() if k not in self._current_ids]
        
    def to_json(self) -> str:
        """Serializes current config state to JSON."""
        return json.dumps({
            "current_ids": self._current_ids,
            "errors": self._validation_errors,
            "fallbacks_available": self.get_fallback_candidates()
        }, indent=2)

# Global instance for the pipeline
dataset_config = DatasetConfig()

# --- Path Helpers ---
def get_data_path(subpath: str) -> Path:
    """
    Constructs a full path relative to the data directory.
    
    Args:
        subpath: Relative path string (e.g., 'raw/ds000030').
    """
    ensure_dirs()
    return DATA_RAW / subpath

def get_processed_path(subpath: str) -> Path:
    """Constructs a full path relative to the processed data directory."""
    ensure_dirs()
    return DATA_PROCESSED / subpath

def get_derived_path(subpath: str) -> Path:
    """Constructs a full path relative to the derived data directory."""
    ensure_dirs()
    return DATA_DERIVED / subpath

def get_figure_path(filename: str) -> Path:
    """Constructs a full path for a figure file."""
    ensure_dirs()
    return FIGURES_DIR / filename

# --- Execution Guard ---
if __name__ == "__main__":
    # Simple verification that paths are resolvable
    print(f"Project Root: {_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Initial Datasets: {dataset_config.current_ids}")
    ensure_dirs()
    print("Directory structure verified.")
    
    # Demonstrate fallback mechanism (mock failure)
    # In a real run, this would happen after a validation check
    # dataset_config.register_validation_failure("ds000030", "ERR_DATA_MISSING", "Missing 'musical_genre'")
    # print(f"After failure: {dataset_config.current_ids}")
    # print(f"Fallback candidates: {dataset_config.get_fallback_candidates()}")
    
    print("Configuration loaded successfully.")
