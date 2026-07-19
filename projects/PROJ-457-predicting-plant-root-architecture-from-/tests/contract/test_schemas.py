"""
Contract tests for research pipeline output schemas.
Validates that generated artifacts conform to defined YAML/JSON schemas.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

try:
    import yaml
except ImportError:
    # Fallback for environments without PyYAML installed but schema is YAML
    yaml = None

from config import get_config


def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if yaml is None:
        raise ImportError("PyYAML is required to load YAML schemas. Install with: pip install pyyaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> list:
    """
    A simplified JSON Schema validator for the specific structures required.
    Checks 'type', 'required', and basic 'properties' constraints.
    Returns a list of error messages.
    """
    errors = []

    def _validate(obj: Any, expected_type: str, path: str, required_fields: list = None, properties: dict = None):
        # Type check
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        if expected_type in type_map:
            if not isinstance(obj, type_map[expected_type]):
                # Special case for number accepting int
                if expected_type == "number" and isinstance(obj, int):
                    pass
                else:
                    errors.append(f"{path}: Expected {expected_type}, got {type(obj).__name__}")
                    return

        # Required fields check (only for objects)
        if expected_type == "object" and required_fields:
            for field in required_fields:
                if field not in obj:
                    errors.append(f"{path}: Missing required field '{field}'")

        # Recursive property check
        if expected_type == "object" and properties:
            for key, value_schema in properties.items():
                if key in obj:
                    _validate(
                        obj[key],
                        value_schema.get("type", "any"),
                        f"{path}.{key}",
                        value_schema.get("required"),
                        value_schema.get("properties")
                    )
        elif expected_type == "array" and properties and "items" in properties:
            # Handle simple array item validation if 'items' has a type
            item_schema = properties.get("items", {})
            if isinstance(item_schema, dict) and "type" in item_schema:
                for i, item in enumerate(obj):
                    _validate(
                        item,
                        item_schema["type"],
                        f"{path}[{i}]"
                    )

    _validate(data, schema.get("type", "any"), "root", schema.get("required"), schema.get("properties"))
    return errors


class TestFinalReportSchema(unittest.TestCase):
    """Contract test for the final research report schema."""

    def setUp(self):
        """Load the schema from the contracts directory."""
        self.schema_path = project_root / "contracts" / "output.schema.yaml"
        self.report_path = project_root / "artifacts" / "reports" / "final_report.json"
        self.assertTrue(self.schema_path.exists(), f"Schema file not found: {self.schema_path}")
        self.schema = load_yaml_schema(self.schema_path)

    def test_final_report_schema_validates_structure(self):
        """
        Validates `contracts/output.schema.yaml` structure (tables, metrics, deviations).
        Ensures that if a final report exists, it matches the schema.
        If the report doesn't exist yet, this test verifies the schema is valid
        and would accept a correctly formed report.
        """
        # 1. Verify schema structure itself (basic sanity check)
        self.assertIn("required", self.schema, "Schema must have 'required' fields")
        self.assertIn("properties", self.schema, "Schema must have 'properties'")

        required_top_level = self.schema["required"]
        expected_keys = [
            "report_metadata", "executive_summary", "methodology",
            "model_results", "biological_plausibility", "spec_deviations",
            "success_criteria_metrics", "appendices"
        ]
        for key in expected_keys:
            self.assertIn(key, required_top_level, f"Schema must require '{key}'")

        # 2. If the report artifact exists, validate it against the schema
        if self.report_path.exists():
            with open(self.report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            errors = validate_json_against_schema(report_data, self.schema)
            if errors:
                self.fail(f"Final report validation failed:\n" + "\n".join(errors))
        else:
            # If report doesn't exist, we assert that the schema is at least well-formed
            # and would theoretically accept the expected structure.
            # This prevents the test from failing simply because T034 hasn't run yet.
            self.skipTest("Final report artifact not found at {}. Skipping validation.".format(self.report_path))


class TestModelMetricsSchema(unittest.TestCase):
    """Contract test for model metrics schema (consumed by T034)."""

    def test_model_metrics_schema_validates_fields(self):
        """
        Validates `artifacts/reports/model_metrics.json` structure.
        Ensures it contains LMM and RF metrics as defined in T029.
        """
        metrics_path = project_root / "artifacts" / "reports" / "model_metrics.json"

        if not metrics_path.exists():
            self.skipTest(f"Model metrics file not found at {metrics_path}. Skipping validation.")

        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Basic structural checks based on T029 requirements
        self.assertIn("lmm_metrics", data, "Missing lmm_metrics")
        self.assertIn("random_forest_metrics", data, "Missing random_forest_metrics")
        self.assertIn("comparison", data, "Missing comparison")

        lmm = data["lmm_metrics"]
        rf = data["random_forest_metrics"]
        comp = data["comparison"]

        # Check LMM fields
        self.assertIn("adjusted_r_squared", lmm, "LMM missing adjusted_r_squared")
        self.assertIn("rmse", lmm, "LMM missing rmse")
        self.assertIn("p_values", lmm, "LMM missing p_values")

        # Check RF fields
        self.assertIn("r_squared", rf, "RF missing r_squared")
        self.assertIn("rmse", rf, "RF missing rmse")

        # Check comparison fields
        self.assertIn("r_squared_delta", comp, "Comparison missing r_squared_delta")


class TestMetricsSchema(unittest.TestCase):
    """Contract test for success criteria metrics (T035a/b)."""

    def test_metrics_schema_validates_redefined_criteria(self):
        """
        Validates `artifacts/reports/metrics.json` contains redefined SC-001 and SC-005.
        """
        metrics_path = project_root / "artifacts" / "reports" / "metrics.json"

        if not metrics_path.exists():
            self.skipTest(f"Metrics file not found at {metrics_path}. Skipping validation.")

        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # T035a: P/N Availability Rate
        self.assertIn("pn_availability_rate", data, "Missing pn_availability_rate (SC-001 redefinition)")
        self.assertIn("original_sc001_metric", data, "Missing note on original SC-001 metric")

        # T035b: Species Exclusion Ratio
        self.assertIn("species_exclusion_ratio", data, "Missing species_exclusion_ratio (SC-005)")


if __name__ == "__main__":
    unittest.main()