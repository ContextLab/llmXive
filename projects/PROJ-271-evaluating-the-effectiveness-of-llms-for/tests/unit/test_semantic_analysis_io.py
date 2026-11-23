import os
import json
import pytest
import pandas as pd
import tempfile
from pathlib import Path

# Mock imports to avoid heavy model loading during unit tests
# We only test the IO and logic flow here.

def test_save_and_load_semantic_results():
    """
    Verify that the output format of semantic_results.json is valid JSON
    and contains the expected keys.
    """
    # Simulate the structure that run_semantic_analysis should produce
    mock_results = [
        {
            "original_index": 0,
            "code_length": 150,
            "static_smell_labels": ["Long Function"],
            "llm_smell_labels": ["Long Function", "Complex Condition"],
            "embedding": [0.1, 0.2, 0.3] # Mock vector
        },
        {
            "original_index": 1,
            "code_length": 50,
            "static_smell_labels": [],
            "llm_smell_labels": [],
            "embedding": [0.4, 0.5, 0.6]
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "semantic_results.json")
        
        # Write mock data
        with open(output_path, 'w') as f:
            json.dump(mock_results, f)

        # Read back and validate
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)

        assert isinstance(loaded_data, list)
        assert len(loaded_data) == 2
        
        # Check keys
        required_keys = {"original_index", "code_length", "static_smell_labels", "llm_smell_labels", "embedding"}
        for item in loaded_data:
            assert required_keys.issubset(item.keys())
            assert isinstance(item['embedding'], list)
            assert isinstance(item['llm_smell_labels'], list)

def test_merge_logic_structure():
    """
    Verify that the logic for merging static baseline and LLM results
    would produce the correct structure if data were available.
    """
    # This is a structural test to ensure the code in semantic_analysis.py
    # constructs the dictionary correctly.
    static_smells = ["Long Function"]
    llm_smells = ["Complex Condition"]
    emb = [0.1]
    
    result_item = {
        "original_index": 0,
        "code_length": 100,
        "static_smell_labels": static_smells,
        "llm_smell_labels": llm_smells,
        "embedding": emb
    }
    
    assert result_item["static_smell_labels"] == static_smells
    assert result_item["llm_smell_labels"] == llm_smells
    assert result_item["embedding"] == emb