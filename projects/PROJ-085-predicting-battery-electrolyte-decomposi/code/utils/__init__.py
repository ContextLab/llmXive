"""
Utility package initializer for the Battery Electrolyte Decomposition project.

This module re-exports the most commonly used symbols from the submodules
so that they can be imported directly via ``utils`` if desired.  It also
ensures that importing ``utils`` does not raise errors due to missing
symbols (the previous implementation attempted to import
``get_reactions_schema_template`` and ``create_empty_reactions_yaml``,
which are not part of the current code base).
"""

# Re-export constants
from .constants import (
    FARADAY_C,
    PHI_VALUES,
    get_potential_bin,
    DEFAULT_SEED,
    get_default_seed,
    load_reactions,
    compute_sha256,
    save_checksums,
    load_checksums,
    validate_file,
    validate_all_checksums,
    register_file,
    compute_directory_checksums,
)

# Re-export data models
from .models import (
    MoleculeType,
    ElectrolyteMolecule,
    DecompositionEvent,
    FeatureVector,
)

# Re-export logging utilities
from .logging_config import (
    get_logger,
    log_missing_geometric_data,
    log_metallic_outlier,
    log_feature_extraction_error,
)

__all__ = [
    # constants
    "FARADAY_C",
    "PHI_VALUES",
    "get_potential_bin",
    "DEFAULT_SEED",
    "get_default_seed",
    "load_reactions",
    "compute_sha256",
    "save_checksums",
    "load_checksums",
    "validate_file",
    "validate_all_checksums",
    "register_file",
    "compute_directory_checksums",
    # models
    "MoleculeType",
    "ElectrolyteMolecule",
    "DecompositionEvent",
    "FeatureVector",
    # logging helpers
    "get_logger",
    "log_missing_geometric_data",
    "log_metallic_outlier",
    "log_feature_extraction_error",
]
