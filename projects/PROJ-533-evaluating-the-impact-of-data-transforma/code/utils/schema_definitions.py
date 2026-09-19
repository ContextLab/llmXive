"""
Schema definitions for CSV output files in the data transformation sensitivity pipeline.
This module provides functions to retrieve the exact headers for each CSV file
to ensure consistency across the pipeline.
"""
from typing import List

def get_imputation_log_headers() -> List[str]:
    """
    Returns the headers for the imputation log CSV file.
    
    Headers: dataset_id, variable, imputation_method, rate
    
    Returns:
        List of header strings.
    """
    return ["dataset_id", "variable", "imputation_method", "rate"]

def get_exclusions_headers() -> List[str]:
    """
    Returns the headers for the exclusions log CSV file.
    
    Headers: dataset_id, reason, details
    
    Returns:
        List of header strings.
    """
    return ["dataset_id", "reason", "details"]

def get_filter_results_headers() -> List[str]:
    """
    Returns the headers for the filter results CSV file.
    
    This schema is defined for T016a and used by T016.
    Headers: dataset_id, shapiro_p, sample_size, included
    
    Returns:
        List of header strings.
    """
    return ["dataset_id", "shapiro_p", "sample_size", "included"]
