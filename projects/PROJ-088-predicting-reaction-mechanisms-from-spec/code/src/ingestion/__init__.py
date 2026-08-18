"""
Ingestion module for loading and preprocessing spectroscopic data.

This package handles:
- Loading raw data from external sources (NIST, PubChem)
- Provenance filtering based on kinetic study criteria
- Preprocessing spectra (normalization, binning, outlier detection)
"""

from .load_nist import load_nist_webbook
from .load_pubchem import load_pubchem_nmr
from .provenance_filter import is_valid_provenance, should_exclude_row, filter_by_provenance
from .preprocess import normalize_spectrum, bin_spectrum, detect_outliers, preprocess_dataset

__all__ = [
    "load_nist_webbook",
    "load_pubchem_nmr",
    "is_valid_provenance",
    "should_exclude_row",
    "filter_by_provenance",
    "normalize_spectrum",
    "bin_spectrum",
    "detect_outliers",
    "preprocess_dataset",
]
