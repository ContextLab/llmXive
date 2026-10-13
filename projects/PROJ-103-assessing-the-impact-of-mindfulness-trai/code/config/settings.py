"""
Core configuration for the mindfulness‑DMN analysis pipeline.

This module defines the canonical configuration keys required by downstream
components. All keys are typed with standard Python type hints to enable
static checking and documentation generation.
"""

from typing import Dict, Any, Tuple

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
