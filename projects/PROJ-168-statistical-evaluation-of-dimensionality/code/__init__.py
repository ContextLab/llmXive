"""
llmXive Statistical Evaluation of Dimensionality Reduction Techniques.

This package provides the core modules for downloading, preprocessing,
analyzing, and modeling gene expression data.
"""

from .config import ensure_paths, set_global_seed, get_accession_seed, set_case_study_mode, Config

__all__ = [
    "ensure_paths",
    "set_global_seed",
    "get_accession_seed",
    "set_case_study_mode",
    "Config"
]

__version__ = "0.1.0"
