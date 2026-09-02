import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.aggregate import (
    find_batch_files,
    load_batch_file,
    consolidate_batches,
    verify_structure,
    save_results,
    main
)

def test_consolidate_batches_preserves_ast_params():
    """
    Integration test to verify that consolidation preserves 'ast_params'
    and correctly merges multiple batch files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create mock batch files
        batch1_data = [
            {
                "method_name": "func1",
                "repo_name": "repo1",
                "human_docstring": "Human doc",
                "generated_docstring": "LLM doc",
                "ast_params": ["a", "b"]
            },
            {
                "method_name": "func2",
                "repo_name": "repo1",
                "human_docstring": None,
                "generated_docstring": "LLM doc 2",
                "ast_params": ["c"]
            }
        ]
        
        batch2_data = [
            {
                "method_name": "func3",
                "repo_name": "repo2",
                "human_docstring": "Human doc 3",
                "generated_docstring": "LLM doc 3",
                "ast_params": ["x", "y", "z"]
            }
        ]

        batch1_path = tmppath / "generation_batch_repo1.json"
        batch2_path = tmppath / "generation_batch_repo2.json"

        with open(batch1_path, 'w') as f:
            json.dump(batch1_data, f)
        
        with open(batch2_path, 'w') as f:
            json.dump(batch2_data, f)

        # Run consolidation
        files = find_batch_files(tmppath)
        assert len(files) == 2
        
        consolidated = consolidate_batches(files)
        assert len(consolidated) == 3
        
        # Verify ast_params preservation
        assert consolidated[0]['ast_params'] == ["a", "b"]
        assert consolidated[1]['ast_params'] == ["c"]
        assert consolidated[2]['ast_params'] == ["x", "y", "z"]

def test_verify_structure_fails_on_missing_keys():
    """
    Verify that structure validation fails if required keys are missing.
    """
    bad_records = [
        {"method_name": "test"}, # missing repo_name, etc.
        {"repo_name": "test", "method_name": "test"} # missing docstrings
    ]
    
    assert not verify_structure(bad_records)

def test_verify_structure_passes_on_valid_records():
    """
    Verify that structure validation passes for valid records.
    """
    valid_records = [
        {
            "method_name": "test",
            "repo_name": "repo",
            "human_docstring": "Doc",
            "generated_docstring": "Doc",
            "ast_params": ["arg"]
        }
    ]
    
    assert verify_structure(valid_records)

def test_save_and_load_results(tmp_path):
    """
    Test saving and loading the final results file.
    """
    data = [
        {
            "method_name": "m1",
            "repo_name": "r1",
            "human_docstring": "h",
            "generated_docstring": "g",
            "ast_params": ["p"]
        }
    ]
    output_file = tmp_path / "results.json"
    
    save_results(data, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded) == 1
    assert loaded[0]['method_name'] == 'm1'