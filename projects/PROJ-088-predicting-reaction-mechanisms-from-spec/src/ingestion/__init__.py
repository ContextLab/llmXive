"""
Ingestion package for loading and preprocessing spectroscopic data.

This package handles:
- Loading raw data from NIST WebBook and PubChem
- Provenance filtering to ensure kinetic study labels
- Spectral preprocessing (normalization, binning, outlier detection)
- Data validation and quality checks
"""

from .load_nist import load_nist_data, main as load_nist_main
from .load_pubchem import load_pubchem_data, main as load_pubchem_main
from .preprocess import (
    normalize_spectrum,
    bin_spectrum,
    detect_outliers,
    validate_class_balance,
    preprocess_dataset,
    main as preprocess_main
)
from .provenance_filter import (
    is_valid_provenance,
    should_exclude_row,
    filter_by_provenance,
    validate_provenance_consistency
)

__all__ = [
    # Loaders
    'load_nist_data',
    'load_nist_main',
    'load_pubchem_data',
    'load_pubchem_main',
    
    # Preprocessing functions
    'normalize_spectrum',
    'bin_spectrum',
    'detect_outliers',
    'validate_class_balance',
    'preprocess_dataset',
    'preprocess_main',
    
    # Provenance filtering
    'is_valid_provenance',
    'should_exclude_row',
    'filter_by_provenance',
    'validate_provenance_consistency'
]

__version__ = "0.1.0"
