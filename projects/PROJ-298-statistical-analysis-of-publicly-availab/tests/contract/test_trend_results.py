"""
Contract test for trend output schema in US1.
Validates the structure and content of trend_results.json, ensuring
Growth/Decline/Stable/Insufficient Data classifications are correct.
"""
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Import validation utilities from the project
from utils.contract_validation import load_contract, validate_schema, ContractValidationError

# Path constants relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
TREND_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "trend_results.json"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


def load_trend_results() -> Dict[str, Any]:
    """Load the trend results JSON file."""
    if not TREND_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Trend results file not found at {TREND_RESULTS_PATH}")
    with open(TREND_RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_trend_contract() -> Dict[str, Any]:
    """Load the contract definition for trend results."""
    contract_path = CONTRACTS_DIR / "trend_results_schema.json"
    if not contract_path.exists():
        raise FileNotFoundError(f"Contract file not found at {contract_path}")
    with open(contract_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_trend_results_schema():
    """
    Contract test: Verify trend_results.json matches the expected schema.
    Validates:
    - Top-level structure
    - Required fields per tag entry
    - Valid classification categories
    - Numeric types for slopes and p-values
    """
    # Load data and contract
    try:
        results = load_trend_results()
        contract = get_trend_contract()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load required files: {e}")

    # Validate against schema
    try:
        validate_schema(results, contract)
    except ContractValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")

    # Additional specific checks
    assert isinstance(results, list), "Root must be a list of tag results"
    assert len(results) > 0, "Results list must not be empty"

    valid_classifications = {"Growth", "Decline", "Stable", "Insufficient Data"}

    for entry in results:
        assert "tag" in entry, "Missing 'tag' field"
        assert "classification" in entry, "Missing 'classification' field"
        assert "slope" in entry, "Missing 'slope' field"
        assert "p_value" in entry, "Missing 'p_value' field"
        assert "power" in entry, "Missing 'power' field"

        # Validate classification
        classification = entry["classification"]
        assert classification in valid_classifications, (
            f"Invalid classification '{classification}'. Must be one of {valid_classifications}"
        )

        # Validate numeric fields
        assert isinstance(entry["slope"], (int, float)), "Slope must be numeric"
        assert isinstance(entry["p_value"], (int, float)), "P-value must be numeric"
        assert isinstance(entry["power"], (int, float)), "Power must be numeric"

        # Validate classification logic consistency
        p_val = entry["p_value"]
        power = entry["power"]

        if p_val < 0.05:
            assert classification in {"Growth", "Decline"}, (
                f"Significant result (p={p_val}) must be Growth or Decline, got {classification}"
            )
            # Check slope direction consistency
            if classification == "Growth":
                assert entry["slope"] > 0, "Growth must have positive slope"
            elif classification == "Decline":
                assert entry["slope"] < 0, "Decline must have negative slope"
        else:
            if power < 0.8:
                assert classification == "Insufficient Data", (
                    f"Non-significant with low power ({power}) must be 'Insufficient Data', got {classification}"
                )
            else:
                assert classification == "Stable", (
                    f"Non-significant with high power ({power}) must be 'Stable', got {classification}"
                )


def test_trend_results_contains_significant_tags():
    """
    Integration check: Ensure the results contain at least one tag with p < 0.05
    to verify the Mann-Kendall pipeline produced meaningful statistical results.
    """
    results = load_trend_results()
    significant_tags = [r for r in results if r["p_value"] < 0.05]
    assert len(significant_tags) > 0, (
        "No significant tags (p < 0.05) found. "
        "This suggests the Mann-Kendall test may not have detected trends or data is missing."
    )


def test_trend_results_classification_distribution():
    """
    Verify that the results include examples of the different classification types
    to ensure the classification logic is functioning across the spectrum.
    """
    results = load_trend_results()
    classifications = {r["classification"] for r in results}

    # We expect at least Growth/Decline and Stable/Insufficient Data if data is sufficient
    # This is a soft check to ensure the logic isn't broken into a single category
    assert len(classifications) >= 2, (
        f"All tags fell into a single classification '{list(classifications)[0]}'. "
        "Expected a mix of Growth/Decline/Stable/Insufficient Data."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
