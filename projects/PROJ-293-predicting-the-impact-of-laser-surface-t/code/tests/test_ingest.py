import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# The test ensures that the ingestion step produced a merged CSV with the
# required canonical columns and at least one distinct source identifier.
def test_fetch_and_schema():
    merged_path = paths.data("intermediate", "merged.csv")
    validation_path = paths.results("source_validation.json")

    # Verify files exist
    assert merged_path.exists(), f"{merged_path} does not exist"
    assert validation_path.exists(), f"{validation_path} does not exist"

    # Load merged data
    df = pd.read_csv(merged_path)

    required_columns = [
        "pulse_duration",
        "power",
        "scanning_speed",
        "wear_rate",
    ]
    for col in required_columns:
        assert col in df.columns, f"Missing required column {col}"

    # At least one distinct source_id
    assert "source_id" in df.columns, "source_id column missing"
    assert df["source_id"].nunique() >= 1, "No distinct source_id values found"

    # Verify validation JSON contains expected keys and warnings handling
    with validation_path.open("r", encoding="utf-8") as f:
        validation = json.load(f)

    assert "source_count" in validation
    assert "source_ids" in validation
    assert validation["source_count"] == len(validation["source_ids"])

    # If fewer than 3 sources, a warning entry must be present
    if validation["source_count"] < 3:
        assert "warnings" in validation
        assert "data_source_limitation" in validation["warnings"]
