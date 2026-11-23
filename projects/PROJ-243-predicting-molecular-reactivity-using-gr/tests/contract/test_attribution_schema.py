"""
Contract test for attribution output schema (T027).

This test validates that the attribution output artifact produced by
code/05_attribution.py (and related US3 tasks) strictly adheres to the
expected schema defined in the project specification.

It ensures:
1. The artifact file exists at the expected path.
2. The top-level structure contains required keys.
3. The 'attributions' list contains objects with required fields:
   - molecule_id (str)
   - substructure_smiles (str)
   - importance_score (float, 0.0 <= score <= 1.0)
   - reference_match (bool)
   - reference_substructure_id (str or null)
4. The 'summary' object contains required metrics.
5. Data types are strictly enforced.
"""

import os
import json
import pytest
from typing import Any, Dict, List

# Expected artifact path based on project conventions
ARTIFACT_PATH = "artifacts/attribution_maps.json"

# Schema definition constants
REQUIRED_TOP_LEVEL_KEYS = {"attributions", "summary"}
REQUIRED_ATTRIBUTION_KEYS = {
    "molecule_id",
    "substructure_smiles",
    "importance_score",
    "reference_match",
    "reference_substructure_id"
}
REQUIRED_SUMMARY_KEYS = {
    "total_attributions",
    "average_importance_score",
    "match_rate",
    "total_reference_matches"
}

# Expected types
EXPECTED_TYPES = {
    "molecule_id": str,
    "substructure_smiles": str,
    "importance_score": (int, float),
    "reference_match": bool,
    "reference_substructure_id": (str, type(None)),
    "total_attributions": int,
    "average_importance_score": (int, float),
    "match_rate": (int, float),
    "total_reference_matches": int
}

def load_artifact() -> Dict[str, Any]:
    """Load the attribution artifact from disk."""
    if not os.path.exists(ARTIFACT_PATH):
        raise FileNotFoundError(
            f"Attribution artifact not found at {ARTIFACT_PATH}. "
            "Ensure code/05_attribution.py has been executed."
        )
    
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_artifact_exists_and_is_valid_json():
    """Verify the artifact file exists and is valid JSON."""
    data = load_artifact()
    assert isinstance(data, dict), "Root element must be a dictionary."

def test_top_level_keys_present():
    """Verify all required top-level keys are present."""
    data = load_artifact()
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
    assert not missing_keys, f"Missing required top-level keys: {missing_keys}"

def test_attributions_structure():
    """Verify the 'attributions' list structure and content."""
    data = load_artifact()
    attributions = data.get("attributions")
    
    assert isinstance(attributions, list), "'attributions' must be a list."
    assert len(attributions) > 0, "'attributions' list must not be empty."
    
    for i, entry in enumerate(attributions):
        assert isinstance(entry, dict), f"Attribution entry {i} must be a dictionary."
        
        # Check required keys
        missing_keys = REQUIRED_ATTRIBUTION_KEYS - set(entry.keys())
        assert not missing_keys, (
            f"Attribution entry {i} missing keys: {missing_keys}"
        )
        
        # Check types
        for key, expected_type in EXPECTED_TYPES.items():
            if key in entry:
                value = entry[key]
                assert isinstance(value, expected_type), (
                    f"Attribution entry {i} key '{key}' has type {type(value)}, "
                    f"expected {expected_type}. Value: {value}"
                )
        
        # Validate value constraints
        score = entry["importance_score"]
        assert 0.0 <= score <= 1.0, (
            f"Importance score {score} at index {i} must be between 0.0 and 1.0."
        )
        
        if entry["reference_match"]:
            assert entry["reference_substructure_id"] is not None, (
                f"If reference_match is True at index {i}, "
                "reference_substructure_id must not be None."
            )

def test_summary_structure():
    """Verify the 'summary' object structure and content."""
    data = load_artifact()
    summary = data.get("summary")
    
    assert isinstance(summary, dict), "'summary' must be a dictionary."
    
    missing_keys = REQUIRED_SUMMARY_KEYS - set(summary.keys())
    assert not missing_keys, f"Summary missing required keys: {missing_keys}"
    
    # Validate types and constraints for summary
    total_attributions = summary["total_attributions"]
    assert total_attributions > 0, "total_attributions must be > 0."
    assert total_attributions == len(data["attributions"]), (
        "total_attributions must match the length of the attributions list."
    )
    
    avg_score = summary["average_importance_score"]
    assert 0.0 <= avg_score <= 1.0, (
        f"Average importance score {avg_score} must be between 0.0 and 1.0."
    )
    
    match_rate = summary["match_rate"]
    assert 0.0 <= match_rate <= 1.0, (
        f"Match rate {match_rate} must be between 0.0 and 1.0."
    )
    
    total_matches = summary["total_reference_matches"]
    assert total_matches >= 0, "total_reference_matches must be >= 0."
    assert total_matches <= total_attributions, (
        "total_reference_matches cannot exceed total_attributions."
    )
    
    # Verify match_rate calculation consistency (with tolerance for float)
    expected_rate = total_matches / total_attributions if total_attributions > 0 else 0.0
    assert abs(match_rate - expected_rate) < 1e-6, (
        f"Match rate {match_rate} does not match calculated rate {expected_rate}."
    )