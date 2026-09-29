"""
Contract tests for the evaluation output schema (T025).

This module verifies that `code/scripts/evaluate.py` produces an output file
(`data/results/evaluation.json`) that strictly adheres to the schema defined
in `contracts/evaluation.schema.yaml`.

It validates:
1. Top-level keys and their types.
2. Nested structure for method comparisons and statistical tests.
3. Specific constraints (e.g., p-values must be floats between 0 and 1).
4. Presence of required fields for Wilcoxon tests and Bootstrap CIs.
"""

import json
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "evaluation.schema.yaml"
EVALUATION_RESULTS_PATH = PROJECT_ROOT / "data" / "results" / "evaluation.json"

def load_schema() -> Dict[str, Any]:
    """Load the evaluation schema definition from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. "
                    "Ensure T005 (contracts) is completed.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def load_predictions(file_path: Path) -> Dict[str, Any]:
    """Load the evaluation results JSON file."""
    if not file_path.exists():
        pytest.fail(f"Evaluation results file not found at {file_path}. "
                    "Ensure T026a (evaluate.py) has been executed successfully.")
    with open(file_path, "r") as f:
        return json.load(f)

def validate_field_type(value: Any, expected_type: str, field_path: str) -> None:
    """
    Validate that a value matches the expected type string from the schema.
    Supported types: 'string', 'number', 'integer', 'boolean', 'object', 'array'.
    """
    if expected_type == 'string':
        assert isinstance(value, str), f"{field_path}: Expected string, got {type(value).__name__}"
    elif expected_type in ('number', 'integer', 'float'):
        assert isinstance(value, (int, float)), f"{field_path}: Expected number, got {type(value).__name__}"
    elif expected_type == 'boolean':
        assert isinstance(value, bool), f"{field_path}: Expected boolean, got {type(value).__name__}"
    elif expected_type == 'object':
        assert isinstance(value, dict), f"{field_path}: Expected object, got {type(value).__name__}"
    elif expected_type == 'array':
        assert isinstance(value, list), f"{field_path}: Expected array, got {type(value).__name__}"
    else:
        raise ValueError(f"Unknown type constraint: {expected_type}")

def validate_constraints(value: Any, constraints: Dict[str, Any], field_path: str) -> None:
    """
    Validate value against specific constraints defined in the schema.
    """
    if "min" in constraints:
        assert value >= constraints["min"], f"{field_path}: Value {value} is less than min {constraints['min']}"
    if "max" in constraints:
        assert value <= constraints["max"], f"{field_path}: Value {value} is greater than max {constraints['max']}"
    if "required_keys" in constraints and isinstance(value, dict):
        for key in constraints["required_keys"]:
            assert key in value, f"{field_path}: Missing required key '{key}'"

def validate_schema_recursive(data: Any, schema: Dict[str, Any], path: str = "root") -> None:
    """
    Recursively validate data against the schema definition.
    """
    if "type" in schema:
        validate_field_type(data, schema["type"], path)

    if "constraints" in schema:
        validate_constraints(data, schema["constraints"], path)

    if schema.get("type") == "object" and "properties" in schema:
        assert isinstance(data, dict), f"{path}: Expected object, got {type(data).__name__}"
        for prop_name, prop_schema in schema["properties"].items():
            if prop_name in data:
                validate_schema_recursive(data[prop_name], prop_schema, f"{path}.{prop_name}")
            elif prop_schema.get("required", False):
                pytest.fail(f"{path}: Missing required property '{prop_name}'")

    if schema.get("type") == "array" and "items" in schema:
        assert isinstance(data, list), f"{path}: Expected array, got {type(data).__name__}"
        for i, item in enumerate(data):
            validate_schema_recursive(item, schema["items"], f"{path}[{i}]")

@pytest.fixture
def schema() -> Dict[str, Any]:
    """Fixture to load the schema."""
    return load_schema()

@pytest.fixture
def evaluation_results() -> Dict[str, Any]:
    """Fixture to load the evaluation results."""
    return load_predictions(EVALUATION_RESULTS_PATH)

class TestEvaluationSchema:
    """
    Test suite to verify the evaluation output schema matches the contract.

    This test ensures that `code/scripts/evaluate.py` (T026a) generates
    a valid `data/results/evaluation.json` file as specified in
    `contracts/evaluation.schema.yaml` (T005).
    """

    def test_schema_file_exists(self, schema):
        """Verify the schema definition itself is loadable."""
        assert schema is not None
        assert "type" in schema

    def test_top_level_structure(self, evaluation_results, schema):
        """Verify the top-level keys and types match the schema."""
        validate_schema_recursive(evaluation_results, schema)

    def test_required_method_comparisons(self, evaluation_results):
        """
        Verify that all expected methods are present in the comparison results.
        Based on T026a requirements: Bayesian, Shewhart, CUSUM, VAE.
        """
        assert "method_comparisons" in evaluation_results, "Missing 'method_comparisons' key"
        comparisons = evaluation_results["method_comparisons"]
        assert isinstance(comparisons, dict), "'method_comparisons' must be an object"

        required_methods = ["Bayesian", "Shewhart", "CUSUM", "VAE"]
        for method in required_methods:
            assert method in comparisons, f"Missing comparison data for method: {method}"
            method_data = comparisons[method]
            assert "f1_score" in method_data, f"Missing 'f1_score' for {method}"
            assert "precision" in method_data, f"Missing 'precision' for {method}"
            assert "recall" in method_data, f"Missing 'recall' for {method}"

    def test_statistical_tests_present(self, evaluation_results):
        """
        Verify that statistical test results (Wilcoxon, Bootstrap) are present.
        """
        assert "statistical_tests" in evaluation_results, "Missing 'statistical_tests' key"
        stats = evaluation_results["statistical_tests"]

        # Check for Wilcoxon results (Primary test per T026a)
        assert "wilcoxon" in stats, "Missing 'wilcoxon' results in statistical_tests"
        wilcoxon = stats["wilcoxon"]
        assert isinstance(wilcoxon, dict), "'wilcoxon' must be an object"
        assert "p_value" in wilcoxon, "Missing 'p_value' in wilcoxon results"
        assert isinstance(wilcoxon["p_value"], (int, float)), "'p_value' must be a number"
        assert 0.0 <= wilcoxon["p_value"] <= 1.0, "'p_value' must be between 0 and 1"

        # Check for Bootstrap CI results (Secondary test per T026a)
        assert "bootstrap_ci" in stats, "Missing 'bootstrap_ci' results in statistical_tests"
        bootstrap = stats["bootstrap_ci"]
        assert isinstance(bootstrap, dict), "'bootstrap_ci' must be an object"
        assert "ci_lower" in bootstrap, "Missing 'ci_lower' in bootstrap results"
        assert "ci_upper" in bootstrap, "Missing 'ci_upper' in bootstrap results"
        assert isinstance(bootstrap["ci_lower"], (int, float)), "'ci_lower' must be a number"
        assert isinstance(bootstrap["ci_upper"], (int, float)), "'ci_upper' must be a number"

    def test_threshold_strategy_applied(self, evaluation_results):
        """
        Verify that the threshold strategy used is recorded in the output.
        """
        assert "threshold_strategy" in evaluation_results, "Missing 'threshold_strategy' key"
        strategy = evaluation_results["threshold_strategy"]
        assert isinstance(strategy, dict), "'threshold_strategy' must be an object"
        assert "strategy" in strategy, "Missing 'strategy' type in threshold_strategy"
        assert "value" in strategy, "Missing 'value' in threshold_strategy"

    def test_metadata_present(self, evaluation_results):
        """
        Verify that metadata (timestamp, version) is present.
        """
        assert "metadata" in evaluation_results, "Missing 'metadata' key"
        meta = evaluation_results["metadata"]
        assert "timestamp" in meta, "Missing 'timestamp' in metadata"
        assert "pipeline_version" in meta, "Missing 'pipeline_version' in metadata"