"""
Core configuration for the mindfulness‑DMN analysis pipeline.

This module defines the canonical configuration keys required by downstream
components. In addition to the data structures required by the pipeline,
helper accessor functions are provided so that other modules (and the unit
tests) can retrieve configuration values in a type‑safe way.
"""

from typing import Dict, Any

# ----------------------------------------------------------------------
# Paths to various data folders (relative to the project root)
# ----------------------------------------------------------------------
dataset_paths: Dict[str, str] = {
    "raw": "data/raw",
    "processed": "data/processed",
    "results": "data/results",
    "metadata": "data/metadata",
}

# ----------------------------------------------------------------------
# Pre‑processing parameters (used by fMRIPrep or the Nilearn fallback)
# ----------------------------------------------------------------------
preprocessing_params: Dict[str, Any] = {
    "nthreads": 2,
    "omp_nthreads": 2,
    "mem_mb": 6000,
    "smoothing_fwhm": 6.0,
    "bandpass": (0.01, 0.1),  # Hz
    "output_space": "MNI152NLin2009cAsym",
}

# ----------------------------------------------------------------------
# Atlas choice for ROI definition
# ----------------------------------------------------------------------
atlas_choice: str = "AAL"  # AAL atlas – aligns with Constitution Principle VI

# ----------------------------------------------------------------------
# Motion‑exclusion thresholds
# ----------------------------------------------------------------------
motion_thresholds: Dict[str, float] = {
    "translation_mm": 3.0,   # maximum allowed translation in mm
    "rotation_deg": 3.0,     # maximum allowed rotation in degrees
}

# ----------------------------------------------------------------------
# Statistical thresholds for hypothesis testing
# ----------------------------------------------------------------------
statistical_thresholds: Dict[str, float] = {
    "primary_t": 3.1,   # primary NBS t‑threshold
    "fwe_alpha": 0.05,  # family‑wise error rate for NBS
    "pvalue": 0.05,     # standard significance level
}

# ----------------------------------------------------------------------
# Accessor helpers – used by the pipeline and unit‑tests
# ----------------------------------------------------------------------
def get_dataset_paths() -> Dict[str, str]:
    """Return the dictionary mapping logical dataset keys to relative paths."""
    return dataset_paths

def get_preprocessing_params() -> Dict[str, Any]:
    """Return the dictionary of preprocessing parameters."""
    return preprocessing_params

def get_atlas_choice() -> str:
    """Return the name of the atlas to be used for ROI definition."""
    return atlas_choice

def get_motion_thresholds() -> Dict[str, float]:
    """Return the motion‑exclusion thresholds."""
    return motion_thresholds

def get_statistical_thresholds() -> Dict[str, float]:
    """Return the statistical thresholds used throughout the analysis."""
    return statistical_thresholds
