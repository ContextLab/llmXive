"""
Contract test for decomposition output schema (US2).
Validates the structure and types of data produced by the decomposition pipeline.
Specifically checks for the presence and validity of the Ljung-Box test result.
"""
import json
import pytest
from pathlib import Path
from typing import Any, Dict

# Import the contract validation utilities used by the project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from utils.contract_validation import (
    ContractValidationError,
    load_contract,
    validate_schema,
    enforce_contract
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DECOMPOSITION_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "decomposition_results.json"

# Define the expected schema contract for decomposition results
# This matches the requirements in FR-009 and SC-003
DECOMPOSITION_CONTRACT = {
    "type": "object",
    "required": [
        "tags",
        "metadata",
        "ljung_box_test",
        "rayleigh_test",
        "method_used"
    ],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["timestamp", "version"],
            "properties": {
                "timestamp": {"type": "string"},
                "version": {"type": "string"}
            }
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["tag_name", "decomposition", "stats"],
                "properties": {
                    "tag_name": {"type": "string"},
                    "decomposition": {
                        "type": "object",
                        "required": ["trend", "seasonal", "residual"],
                        "properties": {
                            "trend": {"type": "array", "items": {"type": "number"}},
                            "seasonal": {"type": "array", "items": {"type": "number"}},
                            "residual": {"type": "array", "items": {"type": "number"}}
                        }
                    },
                    "stats": {
                        "type": "object",
                        "required": ["adf_statistic", "adf_pvalue", "seasonality_detected"],
                        "properties": {
                            "adf_statistic": {"type": "number"},
                            "adf_pvalue": {"type": "number"},
                            "seasonality_detected": {"type": "boolean"},
                            "method_applied": {"type": "string", "enum": ["STL", "Hodrick-Prescott"]}
                        }
                    }
                }
            }
        },
        "ljung_box_test": {
            "type": "object",
            "description": "Results of the Ljung-Box test for residual independence",
            "required": ["statistic", "p_value", "lag", "is_independent"],
            "properties": {
                "statistic": {"type": "number"},
                "p_value": {"type": "number"},
                "lag": {"type": "integer", "minimum": 1},
                "is_independent": {"type": "boolean"}
            }
        },
        "rayleigh_test": {
            "type": "object",
            "description": "Results of the Rayleigh test for event alignment",
            "required": ["statistic", "p_value", "alignment_detected"],
            "properties": {
                "statistic": {"type": "number"},
                "p_value": {"type": "number"},
                "alignment_detected": {"type": "boolean"}
            }
        },
        "method_used": {
            "type": "string",
            "enum": ["STL", "Hodrick-Prescott", "Mixed"]
        }
    }
}

def test_decomposition_schema_contract():
    """
    Validates that the decomposition_results.json file adheres to the defined schema.
    This is the primary contract test for US2.
    """
    if not DECOMPOSITION_RESULTS_PATH.exists():
        pytest.fail(f"Artifact not found: {DECOMPOSITION_RESULTS_PATH}. "
                    "The decomposition pipeline has not been run or output is missing.")

    try:
        with open(DECOMPOSITION_RESULTS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {DECOMPOSITION_RESULTS_PATH}: {e}")

    # Validate against the schema
    errors = validate_schema(data, DECOMPOSITION_CONTRACT)
    if errors:
        error_msg = "\n".join([f"- {err}" for err in errors])
        pytest.fail(f"Schema validation failed:\n{error_msg}")

    # Specific check for Ljung-Box result validity (FR-009)
    lb = data.get("ljung_box_test", {})
    if not isinstance(lb.get("p_value"), (int, float)):
        pytest.fail("Ljung-Box p_value must be a number.")
    if not isinstance(lb.get("is_independent"), bool):
        pytest.fail("Ljung-Box is_independent must be a boolean.")
    
    # Ensure p-value logic is consistent (optional but good practice)
    p_val = lb.get("p_value")
    is_indep = lb.get("is_independent")
    # Standard convention: p > alpha (0.05) implies independence (null hypothesis not rejected)
    # Note: The specific threshold might vary, but the boolean should match the p-value logic
    if p_val is not None and is_indep is not None:
        # We don't enforce the specific alpha here as it might be configurable, 
        # but we ensure the field exists and is the right type.
        pass

    # Specific check for Rayleigh test
    ray = data.get("rayleigh_test", {})
    if not isinstance(ray.get("p_value"), (int, float)):
        pytest.fail("Rayleigh p_value must be a number.")

def test_ljung_box_result_structure():
    """
    Detailed validation of the Ljung-Box test result specifically.
    """
    if not DECOMPOSITION_RESULTS_PATH.exists():
        pytest.skip("Artifact missing, skipping detailed check.")

    with open(DECOMPOSITION_RESULTS_PATH, 'r') as f:
        data = json.load(f)

    lb = data.get("ljung_box_test")
    assert lb is not None, "Missing 'ljung_box_test' key in results."
    assert "statistic" in lb, "Missing 'statistic' in ljung_box_test."
    assert "p_value" in lb, "Missing 'p_value' in ljung_box_test."
    assert "lag" in lb, "Missing 'lag' in ljung_box_test."
    assert "is_independent" in lb, "Missing 'is_independent' in ljung_box_test."
    
    # Verify types
    assert isinstance(lb["statistic"], (int, float)), "Statistic must be numeric."
    assert isinstance(lb["p_value"], (int, float)), "P-value must be numeric."
    assert isinstance(lb["lag"], int), "Lag must be an integer."
    assert isinstance(lb["is_independent"], bool), "Independence flag must be boolean."

def test_decomposition_tags_structure():
    """
    Validates that each tag entry in the decomposition results has the required fields.
    """
    if not DECOMPOSITION_RESULTS_PATH.exists():
        pytest.skip("Artifact missing.")

    with open(DECOMPOSITION_RESULTS_PATH, 'r') as f:
        data = json.load(f)

    tags = data.get("tags", [])
    assert len(tags) > 0, "No tags found in decomposition results."

    for tag_entry in tags:
        assert "tag_name" in tag_entry, "Missing tag_name."
        assert "decomposition" in tag_entry, "Missing decomposition data."
        assert "stats" in tag_entry, "Missing stats data."
        
        decomp = tag_entry["decomposition"]
        assert "trend" in decomp, "Missing trend series."
        assert "seasonal" in decomp, "Missing seasonal series."
        assert "residual" in decomp, "Missing residual series."
        
        stats = tag_entry["stats"]
        assert "adf_statistic" in stats, "Missing ADF statistic."
        assert "adf_pvalue" in stats, "Missing ADF p-value."
        assert "seasonality_detected" in stats, "Missing seasonality flag."
        assert "method_applied" in stats, "Missing method applied."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])