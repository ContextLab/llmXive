# data_generation package
"""
Package for synthetic microstructure generation and stiffness computation.
Provides functions to generate images, calculate topological metrics, and
compute effective stiffness tensors using FFT-based homogenization.
"""
from .generate_microstructures import generate_microstructure, save_microstructure, calculate_topological_metrics, main
from .compute_stiffness import load_microstructure, compute_stiffness_tensor, main as compute_main
from .validate_tensors import load_schema, validate_schema_conformity, compute_vrh_bounds, validate_vrh_bounds, validate_dataset, main as validate_main
from .log_derivation import load_metadata_entries, aggregate_derivation_log, main as log_main

__all__ = [
    "generate_microstructure",
    "save_microstructure",
    "calculate_topological_metrics",
    "load_microstructure",
    "compute_stiffness_tensor",
    "load_schema",
    "validate_schema_conformity",
    "compute_vrh_bounds",
    "validate_vrh_bounds",
    "validate_dataset",
    "load_metadata_entries",
    "aggregate_derivation_log",
]
