"""
Data schemas for validation.
"""
import pandas as pd
from typing import Dict, List, Any
import json
from pathlib import Path

SCHEMAS = {
    "github_raw_metrics": {
        "columns": ["url", "unique_authors", "raw_line_count", "kloc"],
        "types": {
            "url": "object",
            "unique_authors": "int64",
            "raw_line_count": "int64",
            "kloc": "float64"
        },
        "required": ["url", "unique_authors", "raw_line_count", "kloc"]
    },
    "target_list": {
        "columns": ["url", "language", "stars", "age"],
        "types": {
            "url": "object",
            "language": "object",
            "stars": "int64",
            "age": "int64"
        },
        "required": ["url", "language", "stars", "age"]
    },
    "repo_metrics": {
        "columns": ["url", "language", "unique_authors", "kloc", "cve_count", "project_age", "release_count"],
        "types": {
            "url": "object",
            "language": "object",
            "unique_authors": "int64",
            "kloc": "float64",
            "cve_count": "int64",
            "project_age": "float64",
            "release_count": "int64"
        },
        "required": ["url", "language", "unique_authors", "kloc", "cve_count"]
    }
}

def get_schema(name: str) -> Dict[str, Any]:
    """Get schema by name."""
    if name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {name}")
    return SCHEMAS[name]

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate a DataFrame against a schema."""
    # Check required columns
    required_cols = schema.get("required", [])
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check types
    type_map = schema.get("types", {})
    for col, expected_type in type_map.items():
        if col in df.columns:
            if expected_type == "object" and not df[col].dtype == object:
                if not df[col].dtype == "object" and not df[col].dtype.name.startswith("str"):
                    logger = __import__('logging').getLogger(__name__)
                    logger.warning(f"Column {col} has type {df[col].dtype}, expected {expected_type}")
            elif expected_type == "int64" and not str(df[col].dtype).startswith("int"):
                logger = __import__('logging').getLogger(__name__)
                logger.warning(f"Column {col} has type {df[col].dtype}, expected {expected_type}")
            elif expected_type == "float64" and not str(df[col].dtype).startswith("float"):
                logger = __import__('logging').getLogger(__name__)
                logger.warning(f"Column {col} has type {df[col].dtype}, expected {expected_type}")

    return True