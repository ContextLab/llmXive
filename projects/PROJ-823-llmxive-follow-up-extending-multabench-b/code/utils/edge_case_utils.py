"""
Utility functions for edge case handling in the MulTaBench pipeline.

This module re-exports key functions from embeddings.edge_case_handler
for convenient access from other modules.
"""
from embeddings.edge_case_handler import (
    EdgeCaseHandler,
    detect_zero_variance_columns,
    detect_missing_fields,
    handle_zero_variance_columns,
    handle_missing_fields,
    preprocess_dataset_for_edge_cases
)

__all__ = [
    'EdgeCaseHandler',
    'detect_zero_variance_columns',
    'detect_missing_fields',
    'handle_zero_variance_columns',
    'handle_missing_fields',
    'preprocess_dataset_for_edge_cases'
]
