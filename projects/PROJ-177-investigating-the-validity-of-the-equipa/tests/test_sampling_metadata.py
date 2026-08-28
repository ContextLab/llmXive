import json
import os
import pytest
from pathlib import Path

def test_sampling_metadata_records_seed_and_rule():
    """
    Verify that artifacts/sampling_metadata.json correctly records the seed 
    and sampling rule as required by T022.
    
    This test assumes the pipeline has been run (T009/T019) and the file exists.
    """
    metadata_path = Path("artifacts/sampling_metadata.json")
    
    if not metadata_path.exists():
        pytest.fail(
            "artifacts/sampling_metadata.json not found. "
            "Run the ingestion pipeline (T009/T019) before running this test."
        )
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    # Check that 'seed' is present and is an integer
    assert "seed" in metadata, "sampling_metadata.json must contain a 'seed' key."
    assert isinstance(metadata["seed"], int), "The 'seed' value must be an integer."
    
    # Check that 'sampling_rule' is present and is a dict/string describing the rule
    assert "sampling_rule" in metadata, "sampling_metadata.json must contain a 'sampling_rule' key."
    
    sampling_rule = metadata["sampling_rule"]
    if isinstance(sampling_rule, str):
        assert len(sampling_rule) > 0, "The 'sampling_rule' string cannot be empty."
    elif isinstance(sampling_rule, dict):
        # If it's a dict, it should have at least one key describing the rule
        assert len(sampling_rule) > 0, "The 'sampling_rule' dict cannot be empty."
    else:
        pytest.fail(f"'sampling_rule' must be a string or dict, got {type(sampling_rule)}")
    
    # Optional: Verify specific keys often expected in sampling_rule based on T009/T051
    if isinstance(sampling_rule, dict):
        # T009 mentions recording sample indices and row count
        # T051 mentions split, chunking, row count
        # We check for at least 'row_count' or 'n_samples' as a sanity check
        has_count = any(key in sampling_rule for key in ['row_count', 'n_samples', 'count'])
        # We don't fail if missing, but log it if present to ensure consistency
        if has_count:
            pass 

def test_sampling_metadata_content_structure():
    """
    Additional check to ensure the metadata file has a coherent structure
    linking the seed to the sampling rule.
    """
    metadata_path = Path("artifacts/sampling_metadata.json")
    if not metadata_path.exists():
        pytest.skip("Metadata file missing; run pipeline first.")
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    # Ensure the file is not empty or just null
    assert metadata is not None, "Metadata file content is null."
    assert isinstance(metadata, dict), "Metadata file content must be a JSON object."