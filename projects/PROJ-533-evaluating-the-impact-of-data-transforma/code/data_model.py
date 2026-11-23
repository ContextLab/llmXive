"""
Skeleton file for data model definitions.

This module serves as the primary entry point for data model classes.
It re-exports the core classes (Dataset, Transformation, TestResult)
defined in code/utils/data_model.py to maintain a clean public API.

Dependency: T009 (logging_config) - logging infrastructure is assumed to be
configured by the time this module is used in the pipeline.
"""

# Re-export core data model classes from the utility module
# to provide a clean import path: from code.data_model import Dataset
from code.utils.data_model import (
    Dataset,
    Transformation,
    TestResult
)

__all__ = [
    "Dataset",
    "Transformation",
    "TestResult"
]