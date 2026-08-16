"""
Unit tests for code/ingestion.py.

Tests schema validation and data loading logic.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from ingestion import DataSchemaError, validate_schema


def test_validate_schema_missing_columns():
    """Test that missing required columns raise DataSchemaError."""
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "other_col": ["a", "b", "c"]
    })
    required_cols = ["recommended_categories", "enrolled_categories"]

    with pytest.raises(DataSchemaError) as exc_info:
        validate_schema(df, required_cols)

    assert "Required columns" in str(exc_info.value)
    assert "recommended_categories" in str(exc_info.value)
    assert "enrolled_categories" in str(exc_info.value)


def test_validate_schema_valid():
    """Test that a valid dataframe passes validation."""
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "recommended_categories": [["A"], ["B"], ["C"]],
        "enrolled_categories": [["X"], ["Y"], ["Z"]]
    })
    required_cols = ["recommended_categories", "enrolled_categories"]

    # Should not raise
    validate_schema(df, required_cols)


def test_validate_schema_partial_missing():
    """Test that partial missing columns raise DataSchemaError."""
    df = pd.DataFrame({
        "user_id": [1, 2, 3],
        "recommended_categories": [["A"], ["B"], ["C"]]
        # missing enrolled_categories
    })
    required_cols = ["recommended_categories", "enrolled_categories"]

    with pytest.raises(DataSchemaError) as exc_info:
        validate_schema(df, required_cols)

    assert "enrolled_categories" in str(exc_info.value)
    assert "recommended_categories" not in str(exc_info.value)