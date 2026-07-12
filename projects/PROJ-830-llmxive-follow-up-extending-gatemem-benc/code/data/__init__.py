"""
Data module initialization.
Exposes public API for data loading and preprocessing.
"""
from .loader import fetch_gatemem, validate_fields, inject_fallback_data, run_validation_pipeline
from .preprocess import clean_and_format, run_preprocessing_pipeline

__all__ = [
    "fetch_gatemem",
    "validate_fields",
    "inject_fallback_data",
    "run_validation_pipeline",
    "clean_and_format",
    "run_preprocessing_pipeline"
]