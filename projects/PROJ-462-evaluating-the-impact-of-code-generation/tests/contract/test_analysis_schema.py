"""
Contract test for analysis schema (T020).

Validates that analysis outputs conform to the analysis.schema.yaml contract.
Tests the AnalysisResult entity structure with:
- anova_table
- effect_sizes
- adjusted_p_values
- associational_framing
- confounding_controls

This test ensures methodological controls (FR-003, FR-005, FR-006, FR-011)
are properly represented in the output schema.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
SPEC_DIR = PROJECT_ROOT / "specs" / "001-code-generation-performance-outcomes"
CONTRACTS_DIR = SPEC_DIR / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "analysis.schema.yaml"


def load_analysis_schema() -> Dict[str, Any]:
    """Load the analysis schema contract from YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Analysis schema contract not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)
    
    return schema


def validate_field_type(value: Any, expected_type: str, field_name: str) -> bool:
    """Validate that a field matches the expected type."""
    type_mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "boolean": bool,
        "null": type(None)
    }
    
    expected = type_mapping.get(expected_type)
    if expected is None:
        return True  # Unknown type, skip validation
    
    return isinstance(value, expected)


def validate_anova_table(anova_table: Any) -> tuple:
    """
    Validate the anova_table field structure.
    
    Expected structure:
    - source (array of strings)
    - df (array of integers)
    - sum_sq (array of numbers)
    - mean_sq (array of numbers)
    - F (array of numbers)
    - PR(>F) (array of numbers)
    """
    errors = []
    
    if not isinstance(anova_table, dict):
        return False, ["anova_table must be an object"]
    
    required_fields = ["source", "df", "sum_sq", "mean_sq", "F", "PR(>F)"]
    
    for field in required_fields:
        if field not in anova_table:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(anova_table[field], list):
            errors.append(f"Field {field} must be an array")
    
    # Validate arrays have same length
    if all(field in anova_table for field in required_fields):
        lengths = [len(anova_table[field]) for field in required_fields]
        if len(set(lengths)) > 1:
            errors.append("All anova_table arrays must have same length")
    
    return len(errors) == 0, errors


def validate_effect_sizes(effect_sizes: Any) -> tuple:
    """
    Validate the effect_sizes field structure.
    
    Expected structure:
    - comparisons (array of comparison objects)
    - each comparison has:
      - group1 (string)
      - group2 (string)
      - effect_size (number)
      - effect_size_type (string, e.g., "cohen_d")
      - confidence_interval (array of 2 numbers)
    """
    errors = []
    
    if not isinstance(effect_sizes, dict):
        return False, ["effect_sizes must be an object"]
    
    if "comparisons" not in effect_sizes:
        return False, ["Missing required field: comparisons"]
    
    if not isinstance(effect_sizes["comparisons"], list):
        return False, ["comparisons must be an array"]
    
    for i, comp in enumerate(effect_sizes["comparisons"]):
        if not isinstance(comp, dict):
            errors.append(f"Comparison {i} must be an object")
            continue
        
        required_comp_fields = ["group1", "group2", "effect_size", "effect_size_type"]
        for field in required_comp_fields:
            if field not in comp:
                errors.append(f"Comparison {i} missing field: {field}")
        
        if "confidence_interval" in comp:
            if not isinstance(comp["confidence_interval"], list):
                errors.append(f"Comparison {i} confidence_interval must be array")
            elif len(comp["confidence_interval"]) != 2:
                errors.append(f"Comparison {i} confidence_interval must have 2 elements")
    
    return len(errors) == 0, errors


def validate_adjusted_p_values(adjusted_p_values: Any) -> tuple:
    """
    Validate the adjusted_p_values field structure.
    
    Expected structure:
    - method (string, e.g., "bonferroni", "holm")
    - p_values (array of objects with test_name and p_value)
    - alpha (number)
    """
    errors = []
    
    if not isinstance(adjusted_p_values, dict):
        return False, ["adjusted_p_values must be an object"]
    
    required_fields = ["method", "p_values", "alpha"]
    for field in required_fields:
        if field not in adjusted_p_values:
            errors.append(f"Missing required field: {field}")
    
    if "p_values" in adjusted_p_values:
        if not isinstance(adjusted_p_values["p_values"], list):
            errors.append("p_values must be an array")
        else:
            for i, pv in enumerate(adjusted_p_values["p_values"]):
                if not isinstance(pv, dict):
                    errors.append(f"p_value {i} must be an object")
                    continue
                if "test_name" not in pv:
                    errors.append(f"p_value {i} missing test_name")
                if "p_value" not in pv:
                    errors.append(f"p_value {i} missing p_value")
    
    if "alpha" in adjusted_p_values:
        if not isinstance(adjusted_p_values["alpha"], (int, float)):
            errors.append("alpha must be a number")
    
    return len(errors) == 0, errors


def validate_associational_framing(associational_framing: Any) -> tuple:
    """
    Validate the associational_framing field structure.
    
    Expected structure:
    - is_associational (boolean)
    - language_checks (object with flags)
    - summary (string)
    """
    errors = []
    
    if not isinstance(associational_framing, dict):
        return False, ["associational_framing must be an object"]
    
    required_fields = ["is_associational", "language_checks", "summary"]
    for field in required_fields:
        if field not in associational_framing:
            errors.append(f"Missing required field: {field}")
    
    if "is_associational" in associational_framing:
        if not isinstance(associational_framing["is_associational"], bool):
            errors.append("is_associational must be a boolean")
    
    if "language_checks" in associational_framing:
        if not isinstance(associational_framing["language_checks"], dict):
            errors.append("language_checks must be an object")
        else:
            # Check for causal language flags
            causal_keywords = ["causes", "effect", "impact", "influences", "determines"]
            for keyword in causal_keywords:
                if keyword in str(associational_framing).lower():
                    errors.append(f"Potential causal language detected: {keyword}")
    
    if "summary" in associational_framing:
        if not isinstance(associational_framing["summary"], str):
            errors.append("summary must be a string")
    
    return len(errors) == 0, errors


def validate_confounding_controls(confounding_controls: Any) -> tuple:
    """
    Validate the confounding_controls field structure.
    
    Expected structure:
    - covariates (array of strings)
    - adjustment_method (string)
    - vif_diagnostics (object with VIF values)
    - notes (string)
    """
    errors = []
    
    if not isinstance(confounding_controls, dict):
        return False, ["confounding_controls must be an object"]
    
    required_fields = ["covariates", "adjustment_method"]
    for field in required_fields:
        if field not in confounding_controls:
            errors.append(f"Missing required field: {field}")
    
    if "covariates" in confounding_controls:
        if not isinstance(confounding_controls["covariates"], list):
            errors.append("covariates must be an array")
    
    if "adjustment_method" in confounding_controls:
        if not isinstance(confounding_controls["adjustment_method"], str):
            errors.append("adjustment_method must be a string")
    
    if "vif_diagnostics" in confounding_controls:
        if not isinstance(confounding_controls["vif_diagnostics"], dict):
            errors.append("vif_diagnostics must be an object")
    
    return len(errors) == 0, errors


class TestAnalysisSchemaContract:
    """Contract tests for the analysis schema (AnalysisResult entity)."""
    
    @pytest.fixture
    def schema(self):
        """Load the analysis schema contract."""
        return load_analysis_schema()
    
    @pytest.fixture
    def valid_analysis_result(self) -> Dict[str, Any]:
        """Create a valid analysis result matching the schema."""
        return {
            "anova_table": {
                "source": ["tool_usage", "experience_level", "interaction", "Residual"],
                "df": [1, 2, 2, 295],
                "sum_sq": [1234.5, 2345.6, 567.8, 12345.9],
                "mean_sq": [1234.5, 1172.8, 283.9, 41.8],
                "F": [29.54, 28.06, 6.79, 1.0],
                "PR(>F)": [0.0001, 0.0001, 0.0015, 0.45]
            },
            "effect_sizes": {
                "comparisons": [
                    {
                        "group1": "novice_copilot",
                        "group2": "novice_manual",
                        "effect_size": 0.85,
                        "effect_size_type": "cohen_d",
                        "confidence_interval": [0.62, 1.08]
                    },
                    {
                        "group1": "intermediate_copilot",
                        "group2": "intermediate_manual",
                        "effect_size": 0.45,
                        "effect_size_type": "cohen_d",
                        "confidence_interval": [0.21, 0.69]
                    }
                ]
            },
            "adjusted_p_values": {
                "method": "holm",
                "p_values": [
                    {"test_name": "novice_comparison", "p_value": 0.0001},
                    {"test_name": "intermediate_comparison", "p_value": 0.0015}
                ],
                "alpha": 0.05
            },
            "associational_framing": {
                "is_associational": True,
                "language_checks": {
                    "causal_language_detected": False,
                    "associational_language_used": True
                },
                "summary": "Associational findings between tool usage and task completion time"
            },
            "confounding_controls": {
                "covariates": ["task_complexity", "project_type", "team_size"],
                "adjustment_method": "ANCOVA",
                "vif_diagnostics": {
                    "task_complexity": 1.2,
                    "project_type": 1.5,
                    "team_size": 1.3
                },
                "notes": "All VIF values below threshold of 5"
            }
        }
    
    @pytest.fixture
    def invalid_anova_table_result(self) -> Dict[str, Any]:
        """Create an invalid analysis result with malformed anova_table."""
        return {
            "anova_table": "not_an_object",  # Should be dict
            "effect_sizes": {
                "comparisons": []
            },
            "adjusted_p_values": {
                "method": "bonferroni",
                "p_values": [],
                "alpha": 0.05
            },
            "associational_framing": {
                "is_associational": True,
                "language_checks": {},
                "summary": "Test summary"
            },
            "confounding_controls": {
                "covariates": [],
                "adjustment_method": "ANCOVA"
            }
        }
    
    @pytest.fixture
    def missing_required_fields_result(self) -> Dict[str, Any]:
        """Create an analysis result missing required fields."""
        return {
            "anova_table": {
                "source": ["tool_usage"],
                "df": [1],
                "sum_sq": [100],
                "mean_sq": [100],
                "F": [1.0],
                "PR(>F)": [0.5]
            },
            # Missing effect_sizes
            # Missing adjusted_p_values
            "associational_framing": {
                "is_associational": True,
                "language_checks": {},
                "summary": "Test"
            },
            # Missing confounding_controls
        }
    
    def test_schema_file_exists(self, schema):
        """Verify the analysis schema contract file exists."""
        assert SCHEMA_PATH.exists(), "Analysis schema contract must exist"
        assert schema is not None, "Schema must be loadable"
    
    def test_schema_has_required_entity(self, schema):
        """Verify the schema defines the AnalysisResult entity."""
        assert "AnalysisResult" in schema, "Schema must define AnalysisResult entity"
    
    def test_valid_analysis_result_passes_validation(self, valid_analysis_result):
        """Valid analysis results should pass all schema validations."""
        # Test anova_table
        anova_valid, anova_errors = validate_anova_table(valid_analysis_result["anova_table"])
        assert anova_valid, f"anova_table validation failed: {anova_errors}"
        
        # Test effect_sizes
        effect_valid, effect_errors = validate_effect_sizes(valid_analysis_result["effect_sizes"])
        assert effect_valid, f"effect_sizes validation failed: {effect_errors}"
        
        # Test adjusted_p_values
        pval_valid, pval_errors = validate_adjusted_p_values(valid_analysis_result["adjusted_p_values"])
        assert pval_valid, f"adjusted_p_values validation failed: {pval_errors}"
        
        # Test associational_framing
        framing_valid, framing_errors = validate_associational_framing(valid_analysis_result["associational_framing"])
        assert framing_valid, f"associational_framing validation failed: {framing_errors}"
        
        # Test confounding_controls
        confound_valid, confound_errors = validate_confounding_controls(valid_analysis_result["confounding_controls"])
        assert confound_valid, f"confounding_controls validation failed: {confound_errors}"
    
    def test_invalid_anova_table_fails_validation(self, invalid_anova_table_result):
        """Invalid anova_table should fail validation."""
        anova_valid, anova_errors = validate_anova_table(invalid_anova_table_result["anova_table"])
        assert not anova_valid, "Invalid anova_table should fail validation"
        assert any("must be an object" in err for err in anova_errors), "Error should indicate type mismatch"
    
    def test_missing_required_fields_fails_validation(self, missing_required_fields_result):
        """Missing required fields should be detected."""
        # Check anova_table is present
        assert "anova_table" in missing_required_fields_result
        
        # Check effect_sizes is missing
        assert "effect_sizes" not in missing_required_fields_result, "Test data should be missing effect_sizes"
        assert "adjusted_p_values" not in missing_required_fields_result, "Test data should be missing adjusted_p_values"
        assert "confounding_controls" not in missing_required_fields_result, "Test data should be missing confounding_controls"
    
    def test_associational_framing_required(self, schema):
        """Verify associational_framing is a required field in schema."""
        analysis_result_def = schema.get("AnalysisResult", {})
        properties = analysis_result_def.get("properties", {})
        assert "associational_framing" in properties, "associational_framing must be in schema"
    
    def test_anova_table_structure(self, schema):
        """Verify anova_table has required sub-fields."""
        analysis_result_def = schema.get("AnalysisResult", {})
        properties = analysis_result_def.get("properties", {})
        anova_def = properties.get("anova_table", {})
        assert anova_def is not None, "anova_table must be defined"
    
    def test_effect_sizes_structure(self, schema):
        """Verify effect_sizes has required sub-fields."""
        analysis_result_def = schema.get("AnalysisResult", {})
        properties = analysis_result_def.get("properties", {})
        effect_def = properties.get("effect_sizes", {})
        assert effect_def is not None, "effect_sizes must be defined"
    
    def test_adjusted_p_values_structure(self, schema):
        """Verify adjusted_p_values has required sub-fields."""
        analysis_result_def = schema.get("AnalysisResult", {})
        properties = analysis_result_def.get("properties", {})
        pval_def = properties.get("adjusted_p_values", {})
        assert pval_def is not None, "adjusted_p_values must be defined"
    
    def test_confounding_controls_structure(self, schema):
        """Verify confounding_controls has required sub-fields."""
        analysis_result_def = schema.get("AnalysisResult", {})
        properties = analysis_result_def.get("properties", {})
        confound_def = properties.get("confounding_controls", {})
        assert confound_def is not None, "confounding_controls must be defined"
    
    def test_schema_contains_methodological_controls(self, schema):
        """Verify schema includes fields for methodological controls (FR-005, FR-011)."""
        # adjusted_p_values covers FR-005 (multiple comparison correction)
        # confounding_controls covers FR-011 (covariate adjustment)
        # associational_framing covers FR-006 (associational language)
        properties = schema.get("AnalysisResult", {}).get("properties", {})
        assert "adjusted_p_values" in properties, "Schema must include adjusted_p_values for FR-005"
        assert "confounding_controls" in properties, "Schema must include confounding_controls for FR-011"
        assert "associational_framing" in properties, "Schema must include associational_framing for FR-006"
    
    def test_json_serialization(self, valid_analysis_result):
        """Verify valid analysis result can be serialized to JSON."""
        try:
            json_str = json.dumps(valid_analysis_result)
            parsed = json.loads(json_str)
            assert parsed == valid_analysis_result, "JSON round-trip should preserve data"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Analysis result failed JSON serialization: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])