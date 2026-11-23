"""
Configuration module for schema standardization and environment management.
"""
from .loader import load_schema_map, get_target_columns, get_source_columns_for_target, get_mapping_for_source

__all__ = [
    "load_schema_map",
    "get_target_columns",
    "get_source_columns_for_target",
    "get_mapping_for_source"
]