"""Contract test for posterior_summary.csv schema validation."""
import json
import pandas as pd
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


@pytest.fixture
def schema_path():
    return Path(__file__).parent / "../../contracts/posterior_summary_schema.json"


@pytest.fixture
def schema(schema_path):
    """Load the posterior summary JSON schema."""
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def sample_posterior_csv(tmp_path):
    """Create a valid sample posterior_summary.csv for testing."""
    df = pd.DataFrame({
        "predictor": ["mean_degree", "clustering_coeff", "susceptibility_score"],
        "mean": [0.15, -0.08, 0.42],
        "sd": [0.05, 0.03, 0.08],
        "lower_95": [0.05, -0.14, 0.26],
        "upper_95": [0.25, -0.02, 0.58],
        "prob_nonzero": [0.98, 0.92, 0.99],
        "direction_consistent": ["TRUE", "TRUE", "TRUE"]
    })
    csv_path = tmp_path / "posterior_summary.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_posterior_schema_loads(schema):
    """Test that the posterior schema file loads correctly."""
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "posterior" in schema.get("title", "").lower()


def test_posterior_csv_has_required_columns(sample_posterior_csv):
    """Test that posterior_summary.csv contains all required columns per T024."""
    df = pd.read_csv(sample_posterior_csv)
    required_columns = [
        "predictor", "mean", "sd", "lower_95", "upper_95",
        "prob_nonzero", "direction_consistent"
    ]
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"


def test_posterior_csv_no_missing_values(sample_posterior_csv):
    """Test that posterior_summary.csv has no missing values."""
    df = pd.read_csv(sample_posterior_csv)
    assert df.isnull().sum().sum() == 0, "Posterior summary contains missing values"


def test_direction_consistent_values(sample_posterior_csv):
    """Test that direction_consistent is TRUE or FALSE."""
    df = pd.read_csv(sample_posterior_csv)
    assert df["direction_consistent"].isin(["TRUE", "FALSE"]).all()


def test_prob_nonzero_range(sample_posterior_csv):
    """Test that prob_nonzero is in [0, 1]."""
    df = pd.read_csv(sample_posterior_csv)
    assert df["prob_nonzero"].between(0, 1).all()


def test_posterior_csv_validates_against_schema(sample_posterior_csv, schema):
    """Test that posterior_summary.csv validates against the JSON schema."""
    df = pd.read_csv(sample_posterior_csv)
    # Convert DataFrame to list of records for JSON schema validation
    records = df.to_dict(orient="records")

    # Validate against schema
    try:
        validate(instance=records, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")


def test_posterior_csv_invalid_schema_raises_error(tmp_path, schema):
    """Test that an invalid posterior_summary.csv fails schema validation."""
    df = pd.DataFrame({
        "predictor": ["mean_degree"],
        "mean": [0.15],
        "sd": [0.05],
        "lower_95": [0.05],
        "upper_95": [0.25],
        "prob_nonzero": [1.5],  # Invalid: outside [0, 1]
        "direction_consistent": ["TRUE"]
    })
    csv_path = tmp_path / "invalid_posterior.csv"
    df.to_csv(csv_path, index=False)

    records = df.to_dict(orient="records")

    with pytest.raises(ValidationError):
        validate(instance=records, schema=schema)


def test_posterior_csv_direction_consistent_invalid_values(tmp_path, schema):
    """Test that invalid direction_consistent values fail schema validation."""
    df = pd.DataFrame({
        "predictor": ["mean_degree"],
        "mean": [0.15],
        "sd": [0.05],
        "lower_95": [0.05],
        "upper_95": [0.25],
        "prob_nonzero": [0.95],
        "direction_consistent": ["INVALID"]  # Invalid: not TRUE or FALSE
    })
    csv_path = tmp_path / "invalid_direction.csv"
    df.to_csv(csv_path, index=False)

    records = df.to_dict(orient="records")

    with pytest.raises(ValidationError):
        validate(instance=records, schema=schema)
