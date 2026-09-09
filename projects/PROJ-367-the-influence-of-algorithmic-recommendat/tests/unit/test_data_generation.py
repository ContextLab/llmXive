"""
Unit tests for data_generation.py
"""
import os
import tempfile
import pandas as pd
import pytest

from code.data_generation import generate_synthetic_dataset, CATEGORIES, CLUSTERS
from code.config import ProjectConfig

def test_synthetic_dataset_structure():
    """Test that the generated dataset has the correct structure and columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_synthetic.csv")
        df = generate_synthetic_dataset(
            n_users=10,
            n_sessions_per_user=5,
            seed=42,
            output_path=output_path
        )

        # Check file exists
        assert os.path.exists(output_path)

        # Check columns
        expected_cols = ["user_id", "session_id", "timestamp", "recommended_categories", "enrolled_categories", "primary_cluster"]
        assert list(df.columns) == expected_cols

        # Check row count
        expected_rows = 10 * 5
        assert len(df) == expected_rows

def test_synthetic_data_types():
    """Test that the generated data has the correct types and formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_synthetic.csv")
        df = generate_synthetic_dataset(
            n_users=5,
            n_sessions_per_user=3,
            seed=42,
            output_path=output_path
        )

        # Check user_id is integer
        assert df["user_id"].dtype in [int, "int64", "int32"]

        # Check session_id format
        assert df["session_id"].iloc[0].startswith("1_S")

        # Check timestamp format (ISO 8601)
        assert "T" in df["timestamp"].iloc[0]

        # Check categories are semicolon-separated strings
        assert isinstance(df["recommended_categories"].iloc[0], str)
        assert isinstance(df["enrolled_categories"].iloc[0], str)

        # Check categories are from the predefined list
        for _, row in df.iterrows():
            rec_cats = row["recommended_categories"].split(";")
            enroll_cats = row["enrolled_categories"].split(";") if row["enrolled_categories"] else []
            for cat in rec_cats:
                assert cat in CATEGORIES
            for cat in enroll_cats:
                assert cat in CATEGORIES

def test_synthetic_data_consistency():
    """Test that enrolled categories are a subset of recommended categories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_synthetic.csv")
        df = generate_synthetic_dataset(
            n_users=10,
            n_sessions_per_user=10,
            seed=42,
            output_path=output_path
        )

        for _, row in df.iterrows():
            rec_cats = set(row["recommended_categories"].split(";"))
            enroll_cats = set(row["enrolled_categories"].split(";")) if row["enrolled_categories"] else set()
            # Enrolled must be a subset of recommended
            assert enroll_cats.issubset(rec_cats), f"Enrolled {enroll_cats} not subset of Recommended {rec_cats}"