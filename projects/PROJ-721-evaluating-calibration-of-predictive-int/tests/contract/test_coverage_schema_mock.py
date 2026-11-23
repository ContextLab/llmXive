"""
Mock-based contract test for results/coverage.csv schema.

This test validates the schema logic using a mock DataFrame that
conforms to the expected structure, without requiring the full
pipeline to have run. It ensures the schema definition is correct
and the test logic works as intended.
"""

import os
import yaml
import pandas as pd
import pytest
from pathlib import Path
from tests.contract.test_coverage_schema import load_schema, TestCoverageSchema

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "output.schema.yaml"


@pytest.fixture(scope="class")
def mock_schema():
    """Load the schema definition."""
    return load_schema()

@pytest.fixture(scope="class")
def mock_df(mock_schema):
    """Create a mock DataFrame that strictly adheres to the schema."""
    allowed_nominal = mock_schema["constraints"]["nominal_coverage"]
    data = {
        "series_id": ["M4_001", "M4_002"],
        "model": ["ARIMA", "ARIMA"],
        "horizon": [1, 2],
        "nominal_coverage": [0.80, 0.95],
        "empirical_coverage": [0.79, 0.94],
        "deviation": [0.01, 0.01],
        "p_raw": [0.05, 0.03],
        "p_value": [0.05, 0.03]
    }
    df = pd.DataFrame(data)
    # Ensure specific dtypes match schema expectations
    df["horizon"] = df["horizon"].astype("int64")
    df["nominal_coverage"] = df["nominal_coverage"].astype("float64")
    df["empirical_coverage"] = df["empirical_coverage"].astype("float64")
    df["deviation"] = df["deviation"].astype("float64")
    df["p_raw"] = df["p_raw"].astype("float64")
    df["p_value"] = df["p_value"].astype("float64")
    return df

class TestCoverageSchemaMock(TestCoverageSchema):
    """Run the same schema tests against a mock DataFrame."""

    @pytest.fixture(scope="class")
    def df(self, mock_df):
        return mock_df

    @pytest.fixture(scope="class")
    def schema(self, mock_schema):
        return mock_schema