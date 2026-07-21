"""
Data module for the Code Authorship Diversity project.
Handles data ingestion, processing, and schema validation.
"""
from .schemas import get_schema, validate_dataframe

__all__ = ["get_schema", "validate_dataframe"]
