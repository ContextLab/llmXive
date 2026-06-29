"""
Contract tests for US1: Data Ingestion and Salience Computation.

Specifically validates the schema and range constraints for salience scores
produced by the preprocessing pipeline.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure code/ is importable
_code_root = Path(__file__).parent.parent.parent / "code"
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from data_models import Scenario
from utils.logger import get_logger

logger = get_logger(__name__)


def _load_processed_data() -> pd.DataFrame:
    """
    Helper to load the processed salience data.
    Expects data/processed/salience_scores.csv to exist (produced by T014).
    """
    data_path = Path(__file__).parent.parent.parent / "data" / "processed" / "salience_scores.csv"
    if not data_path.exists():
        pytest.skip(f"Data file not found: {data_path}. Run preprocessing tasks first.")
    return pd.read_csv(data_path)


def test_schema_validates_salience_score_range():
    """
    Contract test: Verify that every row in the processed dataset has a
    numeric salience_score within the normalized range [0.0, 1.0].

    This enforces the contract that the salience computation pipeline
    (T013) and merging logic (T014) produce valid normalized scores.
    """
    df = _load_processed_data()

    # Assert column exists
    assert "salience_score" in df.columns, "Missing required column 'salience_score'"

    # Assert numeric type
    assert pd.api.types.is_numeric_dtype(df["salience_score"]), \
        "Column 'salience_score' must be numeric"

    # Assert range constraints [0.0, 1.0]
    min_score = df["salience_score"].min()
    max_score = df["salience_score"].max()

    assert min_score >= 0.0, f"Salience score minimum {min_score} is below 0.0"
    assert max_score <= 1.0, f"Salience score maximum {max_score} is above 1.0"

    # Assert no NaN values in the score column (schema validity)
    assert not df["salience_score"].isna().any(), \
        "Found NaN values in 'salience_score' column"

    logger.info(f"Schema validation passed: {len(df)} rows, range [{min_score:.4f}, {max_score:.4f}]")