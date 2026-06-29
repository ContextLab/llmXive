"""Contract test for model_trace.nc schema validation."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def schema_path():
    return Path(__file__).parent / "../../contracts/model_trace_schema.json"


def test_model_trace_schema_loads(schema_path):
    """Test that the model trace schema file loads correctly."""
    with open(schema_path) as f:
        schema = json.load(f)
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "model" in schema["title"].lower()
    assert "trace" in schema["title"].lower()


def test_model_trace_schema_has_required_metadata():
    """Test that the schema requires all metadata fields."""
    with open(Path(__file__).parent / "../../contracts/model_trace_schema.json") as f:
        schema = json.load(f)
    required_metadata = [
        "file_format", "created_by", "created_at", "random_seed",
        "num_samples", "num_warmup", "num_chains", "model_type", "sampler"
    ]
    for field in required_metadata:
        assert field in schema["properties"]["metadata"]["required"]


def test_model_trace_schema_has_required_variables():
    """Test that the schema requires all model variables."""
    with open(Path(__file__).parent / "../../contracts/model_trace_schema.json") as f:
        schema = json.load(f)
    required_vars = ["beta", "alpha", "sigma", "mu", "size", "user_intercept", "message_intercept"]
    for var in required_vars:
        assert var in schema["properties"]["required_variables"]["contains"]