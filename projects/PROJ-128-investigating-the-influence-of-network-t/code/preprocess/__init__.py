"""
Preprocessing module for HCP OpenNeuro data (dMRI/fMRI).
Provides utilities for loading and initial data handling.
"""
from .loader import load_hcp_data, load_hcp_dmri, load_hcp_fmri

__all__ = [
    "load_hcp_data",
    "load_hcp_dmri",
    "load_hcp_fmri",
]
