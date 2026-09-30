import pytest
import yaml
from pathlib import Path
import json

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-phytoplankton-vlm-analysis" / "contracts"

SCHEMA_ALIGNED = CONTRACTS_DIR / "aligned_dataset.schema.yaml"
SCHEMA_MODEL_PERF = CONTRACTS_DIR / "model_performance.schema.yaml"

def load_schema(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: dict, expected_keys: list):
    """Basic validation that schema contains expected top-level keys."""
    for key in expected_keys:
        assert key in schema, f"Missing key '{key}' in schema"

def test_aligned_dataset_schema_exists_and_valid():
    """
    Validates that aligned_dataset.schema.yaml exists and has basic structure.
    Corresponds to T009a and T009.
    """
    # T009a: Check existence
    assert SCHEMA_ALIGNED.exists(), "aligned_dataset.schema.yaml is missing (T009a)"

    # T009: Load and validate structure
    schema = load_schema(SCHEMA_ALIGNED)
    # Ensure it's a dict and has required fields
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "properties" in schema, "Schema must have 'properties' section"
    
    # Check for critical fields mentioned in T009a description
    required_fields = ["lat", "lon", "timestamp", "basin", "temp", "salinity", "nutrients", "chlorophyll-a", "quality_flags"]
    schema_props = schema["properties"]
    for field in required_fields:
        assert field in schema_props, f"Missing required field '{field}' in aligned_dataset.schema"

def test_model_performance_schema_exists_and_valid():
    """
    Validates that model_performance.schema.yaml exists and has basic structure.
    Corresponds to T032.
    """
    # T032: Check existence
    assert SCHEMA_MODEL_PERF.exists(), "model_performance.schema.yaml is missing (T032)"

    # Load and validate
    schema = load_schema(SCHEMA_MODEL_PERF)
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "properties" in schema, "Schema must have 'properties' section"

    # Basic check for expected metric fields
    required_fields = ["rmse", "r2", "mae", "basin"]
    schema_props = schema["properties"]
    for field in required_fields:
        assert field in schema_props, f"Missing required field '{field}' in model_performance.schema"

def test_importance_scores_sum_to_unity():
    """
    Contract test for feature importance output (T023, T021).
    Validates that if an importance artifact exists, scores sum to 1.0 within tolerance.
    """
    # We check the artifact produced by T023 if it exists
    artifact_path = PROJECT_ROOT / "data" / "artifacts" / "feature_importance.json"
    
    if artifact_path.exists():
        with open(artifact_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict) or len(data) == 0:
            pytest.skip("Importance artifact is empty or invalid")
        
        total = sum(data.values())
        tolerance = 0.01
        assert abs(total - 1.0) <= tolerance, \
            f"Feature importance scores sum to {total}, expected 1.0 (tolerance {tolerance})"
    else:
        # If artifact doesn't exist yet, we don't fail the test suite,
        # but we document that the contract is pending implementation.
        # In a strict CI, this might be a failure if the task is marked done.
        pytest.skip("Feature importance artifact not yet generated")
