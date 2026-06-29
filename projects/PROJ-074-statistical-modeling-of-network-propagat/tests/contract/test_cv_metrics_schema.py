"""Contract test for cv_metrics.json schema validation."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def schema_path():
    return Path(__file__).parent / "../../contracts/cv_metrics_schema.json"


@pytest.fixture
def sample_cv_metrics(tmp_path):
    """Create a valid sample cv_metrics.json for testing."""
    metrics = {
        "waic": {"value": 1234.5, "se": 45.6},
        "loo_cv": {"value": 1240.2, "se": 46.1, "pareto_k_values": [0.3, 0.4, 0.5]},
        "coverage_rates": {
            "nominal_50": 0.48,
            "nominal_80": 0.79,
            "nominal_95": 0.94,
            "nominal_99": 0.98
        },
        "folds": [
            {"fold_id": 1, "held_out_user": "u1", "num_cascades": 5, "fold_waic": 250.0},
            {"fold_id": 2, "held_out_user": "u2", "num_cascades": 6, "fold_waic": 260.0}
        ],
        "method": "leave-one-user-out",
        "created_at": "2024-01-15T10:30:00Z",
        "random_seed": 12345
    }
    json_path = tmp_path / "cv_metrics.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    return json_path


def test_cv_metrics_schema_loads(schema_path):
    """Test that the CV metrics schema file loads correctly."""
    with open(schema_path) as f:
        schema = json.load(f)
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "cv" in schema["title"].lower()


def test_cv_metrics_has_required_keys(sample_cv_metrics):
    """Test that cv_metrics.json contains all required keys per T028."""
    with open(sample_cv_metrics) as f:
        metrics = json.load(f)
    required_keys = ["waic", "loo_cv", "coverage_rates", "folds", "method"]
    for key in required_keys:
        assert key in metrics, f"Missing required key: {key}"


def test_cv_metrics_method_is_louocv(sample_cv_metrics):
    """Test that method is leave-one-user-out."""
    with open(sample_cv_metrics) as f:
        metrics = json.load(f)
    assert metrics["method"] == "leave-one-user-out"


def test_cv_metrics_coverage_rates(sample_cv_metrics):
    """Test that coverage_rates contains all nominal levels."""
    with open(sample_cv_metrics) as f:
        metrics = json.load(f)
    required_levels = ["nominal_50", "nominal_80", "nominal_95", "nominal_99"]
    for level in required_levels:
        assert level in metrics["coverage_rates"], f"Missing coverage level: {level}"