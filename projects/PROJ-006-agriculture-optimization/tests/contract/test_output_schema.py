"""
Contract test for regression output schema (T008).
Validates that `data/processed/regression_results.json` adheres to `contracts/output.schema.yaml`.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict

# Add parent to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestOutputSchema(unittest.TestCase):
    """Tests for the regression output schema contract."""

    def setUp(self):
        """Load the schema and the artifact."""
        self.project_root = Path(__file__).parent.parent.parent
        self.schema_path = self.project_root / "contracts" / "output.schema.yaml"
        self.artifact_path = self.project_root / "data" / "processed" / "regression_results.json"
        
        # Load schema
        import yaml
        with open(self.schema_path, 'r') as f:
            self.schema = yaml.safe_load(f)

    def _validate_required(self, obj: Dict[str, Any], required_fields: list, path: str = ""):
        """Helper to check required fields recursively."""
        for field in required_fields:
            if field not in obj:
                raise AssertionError(f"Missing required field '{field}' at {path}")

    def _validate_type(self, value: Any, expected_type: str, path: str):
        """Helper to check basic types."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        expected = type_map.get(expected_type)
        if expected and not isinstance(value, expected):
            raise AssertionError(f"Type mismatch at {path}: expected {expected_type}, got {type(value).__name__}")

    def test_schema_file_exists(self):
        """Verify the schema definition file exists."""
        self.assertTrue(self.schema_path.exists(), f"Schema file not found: {self.schema_path}")

    def test_artifact_exists(self):
        """Verify the regression results artifact exists."""
        # Note: This test might fail if the pipeline hasn't run yet.
        # It is a contract test, so it validates the artifact format when present.
        self.assertTrue(
            self.artifact_path.exists(),
            f"Artifact not found: {self.artifact_path}. Run `src/analysis/run_regression.py` first."
        )

    def test_artifact_is_valid_json(self):
        """Verify the artifact is valid JSON."""
        with open(self.artifact_path, 'r') as f:
            try:
                self.data = json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"Artifact is not valid JSON: {e}")

    def test_top_level_structure(self):
        """Validate top-level required keys."""
        self._validate_required(self.data, self.schema["required"])

    def test_metadata_structure(self):
        """Validate metadata section."""
        meta = self.data["metadata"]
        self._validate_required(meta, self.schema["properties"]["metadata"]["required"])
        self._validate_type(meta["timestamp"], "string", "metadata.timestamp")
        self._validate_type(meta["pipeline_version"], "string", "metadata.pipeline_version")

    def test_models_structure(self):
        """Validate models section."""
        models = self.data["models"]
        self._validate_required(models, self.schema["properties"]["models"]["required"])
        
        for model_name in ["model_1_stability", "model_2_food_security"]:
            model = models[model_name]
            self._validate_required(model, self.schema["properties"]["models"]["properties"][model_name]["required"])
            
            # Check fit_stats
            fit_stats = model["fit_stats"]
            required_stats = self.schema["properties"]["models"]["properties"][model_name]["properties"]["fit_stats"]["required"]
            self._validate_required(fit_stats, required_stats)
            
            # Check coefficients list
            coeffs = model["coefficients"]
            self.assertIsInstance(coeffs, list)
            self.assertGreater(len(coeffs), 0, f"No coefficients found in {model_name}")
            
            for i, coeff in enumerate(coeffs):
                req = self.schema["properties"]["models"]["properties"][model_name]["properties"]["coefficients"]["items"]["required"]
                self._validate_required(coeff, req, f"models.{model_name}.coefficients[{i}]")

    def test_diagnostics_structure(self):
        """Validate diagnostics section."""
        diag = self.data["diagnostics"]
        self._validate_required(diag, self.schema["properties"]["diagnostics"]["required"])
        self._validate_type(diag["max_vif"], "number", "diagnostics.max_vif")

    def test_sensitivity_structure(self):
        """Validate sensitivity analysis array."""
        sens = self.data["sensitivity"]
        self.assertIsInstance(sens, list)
        # Should have at least one entry if sensitivity analysis was run
        # (Depending on implementation, this might be empty if skipped, but schema requires it)
        
        if len(sens) > 0:
            item = sens[0]
            req = self.schema["properties"]["sensitivity"]["items"]["required"]
            self._validate_required(item, req)

    def test_no_extra_properties(self):
        """Ensure no unexpected top-level keys exist (strict mode)."""
        allowed_keys = set(self.schema["properties"].keys())
        actual_keys = set(self.data.keys())
        extra = actual_keys - allowed_keys
        self.assertEqual(len(extra), 0, f"Unexpected keys found: {extra}")


if __name__ == '__main__':
    unittest.main()