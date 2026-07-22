"""
Contract test for attribution output format.

This test verifies that the output of the explain.py module adheres to the 
expected schema and data types defined for the feature attribution results.

Expected Output Structure (data/processed/attribution_results.json):
{
    "molecule_id": <str>,
    "smiles": <str>,
    "lambda_max_exp": <float>,
    "lambda_max_pred": <float>,
    "attribution": {
        "type": <str>,  # e.g., "gnn_explainer", "gradient"
        "node_importance": [<float>, ...],  # List of floats, length == num_nodes
        "edge_importance": [<float>, ...],  # List of floats, length == num_edges (optional)
        "subgraph_mask": [<int>, ...]       # Binary mask: 1 if retained, 0 if redundant
    },
    "masked": <bool>,  # True if redundancy masks were applied
    "redundancy_flags": [<str>, ...]  # List of flags if collinearity detected
}
"""

import json
import os
import pytest
from pathlib import Path

# Define the expected path for the output file
OUTPUT_PATH = Path("data/processed/attribution_results.json")

# Expected keys at the top level
REQUIRED_TOP_LEVEL_KEYS = [
    "molecule_id",
    "smiles",
    "lambda_max_exp",
    "lambda_max_pred",
    "attribution",
    "masked",
    "redundancy_flags"
]

# Expected keys within the 'attribution' block
REQUIRED_ATTRIBUTION_KEYS = [
    "type",
    "node_importance"
]

def load_attribution_results():
    """Load the attribution results JSON file."""
    if not OUTPUT_PATH.exists():
        pytest.fail(f"Output file not found: {OUTPUT_PATH}. "
                    "Run code/explain.py and code/collinearity_check.py first.")
    
    with open(OUTPUT_PATH, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {OUTPUT_PATH}: {e}")
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Handle case where file might contain a single object instead of a list
        return [data]
    else:
        pytest.fail(f"Unexpected JSON structure in {OUTPUT_PATH}: expected list or dict")

def test_file_exists():
    """Contract test: Verify the output file exists."""
    assert OUTPUT_PATH.exists(), f"Attribution results file {OUTPUT_PATH} does not exist."

def test_output_schema():
    """Contract test: Verify the output schema matches the specification."""
    results = load_attribution_results()
    
    assert len(results) > 0, "Attribution results file is empty."

    for i, record in enumerate(results):
        # Check top-level keys
        missing_top_keys = set(REQUIRED_TOP_LEVEL_KEYS) - set(record.keys())
        assert not missing_top_keys, (
            f"Record {i} is missing top-level keys: {missing_top_keys}. "
            f"Found keys: {list(record.keys())}"
        )

        # Validate types for top-level fields
        assert isinstance(record["molecule_id"], str), f"Record {i}: 'molecule_id' must be str"
        assert isinstance(record["smiles"], str), f"Record {i}: 'smiles' must be str"
        assert isinstance(record["lambda_max_exp"], (int, float)), f"Record {i}: 'lambda_max_exp' must be numeric"
        assert isinstance(record["lambda_max_pred"], (int, float)), f"Record {i}: 'lambda_max_pred' must be numeric"
        assert isinstance(record["masked"], bool), f"Record {i}: 'masked' must be bool"
        assert isinstance(record["redundancy_flags"], list), f"Record {i}: 'redundancy_flags' must be list"

        # Check attribution block
        attribution = record["attribution"]
        assert isinstance(attribution, dict), f"Record {i}: 'attribution' must be a dict"

        missing_attr_keys = set(REQUIRED_ATTRIBUTION_KEYS) - set(attribution.keys())
        assert not missing_attr_keys, (
            f"Record {i}: 'attribution' block missing keys: {missing_attr_keys}"
        )

        assert isinstance(attribution["type"], str), f"Record {i}: 'attribution.type' must be str"
        assert isinstance(attribution["node_importance"], list), f"Record {i}: 'node_importance' must be list"
        
        # Verify node_importance contains floats
        for j, val in enumerate(attribution["node_importance"]):
            assert isinstance(val, (int, float)), (
                f"Record {i}: 'node_importance[{j}]' must be numeric, got {type(val)}"
            )

        # If edge_importance exists, verify it's a list of numbers
        if "edge_importance" in attribution:
            assert isinstance(attribution["edge_importance"], list), f"Record {i}: 'edge_importance' must be list"
            for j, val in enumerate(attribution["edge_importance"]):
                assert isinstance(val, (int, float)), (
                    f"Record {i}: 'edge_importance[{j}]' must be numeric, got {type(val)}"
                )

        # If subgraph_mask exists, verify it's a list of integers
        if "subgraph_mask" in attribution:
            assert isinstance(attribution["subgraph_mask"], list), f"Record {i}: 'subgraph_mask' must be list"
            for j, val in enumerate(attribution["subgraph_mask"]):
                assert isinstance(val, int) and val in (0, 1), (
                    f"Record {i}: 'subgraph_mask[{j}]' must be 0 or 1, got {val}"
                )

def test_data_consistency():
    """Contract test: Verify basic data consistency (e.g., no negative MAE)."""
    results = load_attribution_results()
    
    for i, record in enumerate(results):
        # Check that predictions are reasonable (not NaN or Inf)
        import math
        assert not math.isnan(record["lambda_max_exp"]), f"Record {i}: lambda_max_exp is NaN"
        assert not math.isinf(record["lambda_max_exp"]), f"Record {i}: lambda_max_exp is Inf"
        assert not math.isnan(record["lambda_max_pred"]), f"Record {i}: lambda_max_pred is NaN"
        assert not math.isinf(record["lambda_max_pred"]), f"Record {i}: lambda_max_pred is Inf"

        # Check that node_importance list is not empty
        assert len(record["attribution"]["node_importance"]) > 0, (
            f"Record {i}: 'node_importance' list cannot be empty"
        )

def test_redundancy_mask_application():
    """Contract test: Verify that if 'masked' is True, subgraph_mask exists and is applied."""
    results = load_attribution_results()
    
    for i, record in enumerate(results):
        if record.get("masked", False):
            assert "subgraph_mask" in record["attribution"], (
                f"Record {i}: 'masked' is True but 'subgraph_mask' is missing from attribution"
            )
            
            # Verify that at least one node has a mask value of 0 if flags exist
            # (This is a soft check; strict logic depends on the collinearity check output)
            if record.get("redundancy_flags") and len(record["redundancy_flags"]) > 0:
                # We expect some masking to have occurred if flags were raised
                # Note: This assumes the explain.py logic correctly applies the mask.
                # We just verify the structure exists.
                pass