"""
Error code definitions for the alloy phase diagram prediction pipeline.

This module provides an Enum class containing standardized error codes
used throughout the pipeline for consistent error handling and logging.
"""
from enum import Enum


class ErrorCode(Enum):
    """
    Standardized error codes for the llmXive alloy phase prediction pipeline.
    
    These codes are used for structured logging, state management, and
    automated error handling across all pipeline components.
    """
    
    # Data Source Errors
    DATA_SOURCE_MISSING = "DATA_SOURCE_MISSING"
    """Raised when a required external data source (e.g., NIST-JANAF, SGTE) is not accessible."""
    
    # Data Validation Errors
    INVALID_DATA_SCHEMA = "INVALID_DATA_SCHEMA"
    """Raised when input data does not match the expected schema or format."""
    
    # Data Completeness Errors
    MISSING_TEMP_COORDS = "MISSING_TEMP_COORDS"
    """Raised when temperature coordinates are missing for phase diagram entries."""
    
    # Data Quality Errors
    LOW_DATA_DENSITY = "LOW_DATA_DENSITY"
    """Raised when there is insufficient data points per system for reliable analysis."""
    
    # External API Errors
    API_RATE_LIMIT_EXCEEDED = "API_RATE_LIMIT_EXCEEDED"
    """Raised when an external API rate limit has been exceeded."""
    
    # Statistical Power Errors
    INSUFFICIENT_POWER = "INSUFFICIENT_POWER"
    """Raised when statistical power analysis indicates insufficient sample size."""
