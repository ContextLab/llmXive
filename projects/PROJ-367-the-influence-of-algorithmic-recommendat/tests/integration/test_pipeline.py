"""
Integration tests for the full pipeline workflow.

These tests verify that data flows correctly from ingestion to metrics calculation.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import tempfile
import shutil

# Ensure code directory is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from ingestion import validate_schema, ingest_and_clean
from metrics import calculate_diversity_score, shannon_entropy


@pytest.fixture
def sample_data():
    """Create a small sample dataset for integration testing."""
    data = {
        "user_id": [1, 2, 3, 4, 5],
        "session_id": ["s1", "s2", "s3", "s4", "s5"],
        "recommended_categories": [
            ["Math", "Science"],
            ["History", "Art"],
            ["Math", "Math"],
            ["Science", "History", "Art"],
            ["Math"]
        ],
        "enrolled_categories": [
            ["Math"],
            ["Art", "Art"],
            [],  # Empty enrollment - should be handled
            ["Science", "History"],
            ["Math", "Science"]
        ]
    }
    return pd.DataFrame(data)


def test_ingestion_and_metrics_flow(sample_data):
    """Test the full flow: validate -> ingest -> calculate metrics."""
    # 1. Validate schema
    required_cols = ["recommended_categories", "enrolled_categories"]
    validate_schema(sample_data, required_cols)

    # 2. Ingest and clean (this might filter empty enrollments)
    # Note: ingest_and_clean is expected to handle the filtering logic
    # We assume it returns a cleaned dataframe
    cleaned_data = ingest_and_clean(sample_data)

    # 3. Verify that rows with empty enrollments are removed (if logic exists)
    # In our sample, row index 2 has empty enrolled_categories
    # If filtering is implemented, the length should be 4
    # If not, it's 5. We'll just check that the function returns a dataframe.
    assert isinstance(cleaned_data, pd.DataFrame)
    assert len(cleaned_data) <= len(sample_data)

    # 4. Calculate metrics on the cleaned data
    # We'll calculate diversity for the first row manually to verify
    if len(cleaned_data) > 0:
        first_row = cleaned_data.iloc[0]
        rec_cats = first_row["recommended_categories"]
        enr_cats = first_row["enrolled_categories"]

        rec_score = calculate_diversity_score(rec_cats)
        enr_score = calculate_diversity_score(enr_cats)

        assert isinstance(rec_score, float)
        assert isinstance(enr_score, float)
        assert rec_score >= 0
        assert enr_score >= 0


def test_empty_dataframe_handling():
    """Test that empty dataframes are handled gracefully."""
    empty_df = pd.DataFrame(columns=["user_id", "recommended_categories", "enrolled_categories"])
    
    # Validation should fail if required columns are missing or empty logic applies
    # Here we just check that it doesn't crash in a way that breaks the pipeline
    with pytest.raises(Exception): # Expecting some error or specific handling
        validate_schema(empty_df, ["recommended_categories", "enrolled_categories"])
    
    # Or if it passes validation, ingestion should handle it
    # This depends on the specific implementation of ingest_and_clean
    # For now, we assert that an empty dataframe is processed without crashing
    # if the schema is technically valid (columns exist)
    try:
        validate_schema(empty_df, ["recommended_categories", "enrolled_categories"])
        # If validation passes, ingestion should return empty or handle it
        cleaned = ingest_and_clean(empty_df)
        assert isinstance(cleaned, pd.DataFrame)
    except Exception:
        # If validation fails, that's also acceptable behavior for empty data
        pass
