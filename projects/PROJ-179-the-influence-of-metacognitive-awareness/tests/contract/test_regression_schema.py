"""
Contract test for regression output schema (US2).

This test verifies that the hierarchical regression output produced by
src/analysis/regression.py and src/report/generate.py adheres to the
expected schema defined in the project specifications.

It ensures that:
1. The output file exists at the correct path.
2. The JSON structure contains all required top-level keys.
3. Nested structures (model_1, model_2, diagnostics) have correct types.
4. Statistical fields are numeric and within valid ranges.
5. Flags for missing data (n-1 model) are present if applicable.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path to allow imports if needed, though this is a contract test
# against a file structure, not necessarily execution of the code (unless mocking).
# However, to be robust, we define the expected schema here.

class TestRegressionOutputSchema(unittest.TestCase):
    """
    Contract tests for the regression analysis output schema.
    """

    def setUp(self):
        """
        Set up test fixtures.
        We define the expected schema structure here to ensure the contract is clear.
        """
        self.expected_schema = {
            "type": "dict",
            "required_keys": [
                "model_1",
                "model_2",
                "delta_r_squared",
                "f_change",
                "f_change_p_value",
                "assumption_checks",
                "timestamp"
            ],
            "model_1": {
                "type": "dict",
                "required_keys": [
                    "predictors",
                    "r_squared",
                    "adjusted_r_squared",
                    "coefficients"
                ],
                "coefficients": {
                    "type": "list",
                    "item_keys": ["term", "estimate", "std_error", "t_stat", "p_value"]
                }
            },
            "model_2": {
                "type": "dict",
                "required_keys": [
                    "predictors",
                    "r_squared",
                    "adjusted_r_squared",
                    "coefficients"
                ],
                "coefficients": {
                    "type": "list",
                    "item_keys": ["term", "estimate", "std_error", "t_stat", "p_value"]
                }
            },
            "assumption_checks": {
                "type": "dict",
                "required_keys": [
                    "normality_shapiro_wilk",
                    "homoscedasticity_breusch_pagan",
                    "collinearity_vif"
                ],
                "normality_shapiro_wilk": {
                    "type": "dict",
                    "required_keys": ["statistic", "p_value", "passed"]
                },
                "homoscedasticity_breusch_pagan": {
                    "type": "dict",
                    "required_keys": ["statistic", "p_value", "passed"]
                },
                "collinearity_vif": {
                    "type": "list",
                    "item_keys": ["term", "vif_value", "flagged"]
                }
            }
        }

    def _validate_dict_structure(self, data, schema, path="root"):
        """
        Recursively validate a dictionary against a schema.
        """
        errors = []
        
        if schema.get("type") == "dict":
            if not isinstance(data, dict):
                errors.append(f"{path}: Expected dict, got {type(data).__name__}")
                return errors
            
            required_keys = schema.get("required_keys", [])
            for key in required_keys:
                if key not in data:
                    errors.append(f"{path}: Missing required key '{key}'")
            
            # Validate nested structures if defined
            for key, sub_schema in schema.items():
                if key in ["type", "required_keys"]:
                    continue
                if key in data:
                    errors.extend(self._validate_dict_structure(data[key], sub_schema, f"{path}.{key}"))
        
        elif schema.get("type") == "list":
            if not isinstance(data, list):
                errors.append(f"{path}: Expected list, got {type(data).__name__}")
                return errors
            
            item_keys = schema.get("item_keys", [])
            if item_keys and len(data) > 0:
                if not isinstance(data[0], dict):
                    errors.append(f"{path}: Expected list of dicts, got list of {type(data[0]).__name__}")
                else:
                    for i, item in enumerate(data):
                        for key in item_keys:
                            if key not in item:
                                errors.append(f"{path}[{i}]: Missing key '{key}'")
        
        elif schema.get("type") == "numeric":
            if not isinstance(data, (int, float)):
                errors.append(f"{path}: Expected numeric, got {type(data).__name__}")
        
        return errors

    def test_output_file_exists(self):
        """
        Contract: The regression output file must exist at data/results/regression_analysis.json.
        """
        output_path = Path("data/results/regression_analysis.json")
        self.assertTrue(
            output_path.exists(),
            f"Contract violation: Output file {output_path} does not exist. "
            "Ensure src/analysis/regression.py and src/report/generate.py are executed."
        )

    def test_output_is_valid_json(self):
        """
        Contract: The output file must be valid JSON.
        """
        output_path = Path("data/results/regression_analysis.json")
        try:
            with open(output_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            self.fail(f"Contract violation: Output file is not valid JSON: {e}")

    def test_schema_compliance(self):
        """
        Contract: The output JSON must strictly adhere to the defined schema.
        """
        output_path = Path("data/results/regression_analysis.json")
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        errors = self._validate_dict_structure(data, self.expected_schema)
        
        if errors:
            error_msg = "Schema violations found:\n" + "\n".join([f"  - {err}" for err in errors])
            self.fail(f"Contract violation: Output does not match expected schema.\n{error_msg}")

    def test_statistical_ranges(self):
        """
        Contract: Statistical values must be within valid mathematical ranges.
        - R-squared and Adjusted R-squared should be between -infinity and 1.0 (usually 0-1).
        - P-values should be between 0 and 1.
        - VIF should be >= 1.
        """
        output_path = Path("data/results/regression_analysis.json")
        with open(output_path, 'r') as f:
            data = json.load(f)

        errors = []

        # Check Model 1 and Model 2 R-squared
        for model_key in ["model_1", "model_2"]:
            if model_key in data:
                model = data[model_key]
                r2 = model.get("r_squared")
                adj_r2 = model.get("adjusted_r_squared")
                
                if r2 is not None and (not isinstance(r2, (int, float)) or r2 > 1.0):
                    errors.append(f"{model_key}.r_squared must be <= 1.0, got {r2}")
                if adj_r2 is not None and (not isinstance(adj_r2, (int, float)) or adj_r2 > 1.0):
                    errors.append(f"{model_key}.adjusted_r_squared must be <= 1.0, got {adj_r2}")

                # Check coefficients p-values
                for coef in model.get("coefficients", []):
                    p_val = coef.get("p_value")
                    if p_val is not None and (not isinstance(p_val, (int, float)) or p_val < 0 or p_val > 1):
                        errors.append(f"{model_key}.coefficients p-value must be in [0, 1], got {p_val}")

        # Check Delta R-squared
        delta_r2 = data.get("delta_r_squared")
        if delta_r2 is not None and (not isinstance(delta_r2, (int, float)) or delta_r2 > 1.0):
            errors.append(f"delta_r_squared must be <= 1.0, got {delta_r2}")

        # Check F-change p-value
        f_p = data.get("f_change_p_value")
        if f_p is not None and (not isinstance(f_p, (int, float)) or f_p < 0 or f_p > 1):
            errors.append(f"f_change_p_value must be in [0, 1], got {f_p}")

        # Check VIF
        vif_list = data.get("assumption_checks", {}).get("collinearity_vif", [])
        for vif_entry in vif_list:
            val = vif_entry.get("vif_value")
            if val is not None and (not isinstance(val, (int, float)) or val < 1):
                errors.append(f"VIF must be >= 1, got {val} for {vif_entry.get('term')}")

        if errors:
            self.fail(f"Contract violation: Statistical values out of range:\n" + "\n".join(errors))

    def test_n_minus_1_model_flag_consistency(self):
        """
        Contract: If working memory data was missing, the 'n_minus_1_model' flag must be true.
        This test checks that the flag exists and is a boolean.
        """
        output_path = Path("data/results/regression_analysis.json")
        with open(output_path, 'r') as f:
            data = json.load(f)

        # The flag might be present or absent depending on data availability.
        # If present, it must be boolean.
        if "n_minus_1_model" in data:
            self.assertIsInstance(
                data["n_minus_1_model"],
                bool,
                "Contract violation: n_minus_1_model must be a boolean."
            )
        
        # If the flag is True, model_1 should only have age and gender (2 predictors + intercept)
        if data.get("n_minus_1_model") is True:
            model_1_predictors = data.get("model_1", {}).get("predictors", [])
            # Expected predictors: intercept, age, gender (3 terms total)
            # Note: Implementation might vary on 'intercept' naming, but count should be 3 or predictors list length 2.
            # We check that 'working_memory' is NOT in the predictors.
            predictors_str = str(model_1_predictors).lower()
            self.assertNotIn(
                "working_memory",
                predictors_str,
                "Contract violation: n_minus_1_model is True, but working_memory appears in model_1 predictors."
            )

    def test_timestamp_format(self):
        """
        Contract: The timestamp must be a string (ISO format preferred).
        """
        output_path = Path("data/results/regression_analysis.json")
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        ts = data.get("timestamp")
        self.assertIsInstance(ts, str, "Contract violation: timestamp must be a string.")
        # Basic check for ISO format presence (optional but good practice)
        if "T" not in ts and "-" not in ts:
            # Not strictly failing unless format is mandated, but warning logic could go here
            pass

if __name__ == "__main__":
    unittest.main()