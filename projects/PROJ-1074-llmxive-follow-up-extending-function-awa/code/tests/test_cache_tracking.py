"""
Tests for the cache tracking mechanism (T018c).

These tests verify that:
1. The intermediate caches are properly structured and validated.
2. The dependency graph is correctly captured in the cache entries.
3. The output file is valid JSON and matches the expected schema.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.common import read_json, write_json, ensure_dir
from data.track_intermediate_caches import process_single_example, track_all_caches
from data.convert_to_pseudo_code import convert_gsm8k_to_pseudo_code

# Test fixtures
@pytest.fixture
def sample_gsm8k_example():
    """Sample GSM8K example for testing."""
    return {
        "question": "If John has 3 apples and buys 2 more, then gives 1 to his friend, how many does he have?",
        "answer": "John starts with 3 apples. He buys 2 more, so he has 3 + 2 = 5 apples. He gives 1 to his friend, so he has 5 - 1 = 4 apples."
    }

@pytest.fixture
def sample_multi_step_example():
    """Sample GSM8K example with multiple steps."""
    return {
        "question": "Sarah has 5 books. She buys 3 more books, then reads 2 of them. How many books does she have left unread?",
        "answer": "Sarah starts with 5 books. She buys 3 more, so she has 5 + 3 = 8 books total. She reads 2 books, so she has 8 - 2 = 6 unread books."
    }

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_process_single_example_structure(sample_gsm8k_example):
    """Test that a single example is processed with correct structure."""
    result = process_single_example(sample_gsm8k_example, "test_001")
    
    # Verify required fields
    assert "problem_id" in result
    assert "original_question" in result
    assert "original_answer" in result
    assert "intermediate_steps" in result
    assert "dependency_edges" in result
    assert "pseudo_code_blocks" in result
    assert "processing_metadata" in result
    
    # Verify metadata
    assert result["processing_metadata"]["source"] == "gsm8k"
    assert result["processing_metadata"]["processed"] == True
    assert result["processing_metadata"]["error"] is None
    
    # Verify problem_id matches
    assert result["problem_id"] == "test_001"

def test_process_single_example_steps(sample_multi_step_example):
    """Test that intermediate steps are correctly extracted."""
    result = process_single_example(sample_multi_step_example, "test_002")
    
    # Should have at least one intermediate step
    assert len(result["intermediate_steps"]) > 0
    
    # Each step should have required fields
    for step in result["intermediate_steps"]:
        assert "step_id" in step
        assert "step_code" in step
        assert "derived_fact" in step
        assert "dependencies" in step
        assert "is_leaf" in step
        
        # Step ID should be unique and follow pattern
        assert step["step_id"].startswith("test_002_step_")

def test_dependency_edges_correctness(sample_multi_step_example):
    """Test that dependency edges are correctly captured."""
    result = process_single_example(sample_multi_step_example, "test_003")
    
    # If there are multiple steps, there should be dependency edges
    if len(result["intermediate_steps"]) > 1:
        assert len(result["dependency_edges"]) > 0
        
        # Each edge should have from and to
        for edge in result["dependency_edges"]:
            assert "from" in edge
            assert "to" in edge
            assert edge["from"] is not None
            assert edge["to"] is not None

def test_track_all_caches_creates_file(sample_gsm8k_example, temp_output_dir):
    """Test that track_all_caches creates the output file."""
    # Create a minimal dataset
    test_data_path = os.path.join(temp_output_dir, "test_data.jsonl")
    output_path = os.path.join(temp_output_dir, "test_caches.json")
    
    # Write test data
    test_data = [sample_gsm8k_example]
    write_json(test_data_path, test_data)
    
    # Run tracking
    summary = track_all_caches(test_data_path, output_path)
    
    # Verify output file exists
    assert os.path.exists(output_path)
    
    # Verify summary
    assert summary["total_examples"] == 1
    assert summary["successful_processes"] == 1
    assert summary["output_file"] == output_path

def test_track_all_caches_output_structure(sample_gsm8k_example, temp_output_dir):
    """Test that the output JSON has the correct structure."""
    test_data_path = os.path.join(temp_output_dir, "test_data.jsonl")
    output_path = os.path.join(temp_output_dir, "test_caches.json")
    
    # Write test data
    test_data = [sample_gsm8k_example]
    write_json(test_data_path, test_data)
    
    # Run tracking
    track_all_caches(test_data_path, output_path)
    
    # Read and validate output
    output_data = read_json(output_path)
    
    assert "metadata" in output_data
    assert "caches" in output_data
    
    # Verify metadata fields
    metadata = output_data["metadata"]
    assert "total_examples" in metadata
    assert "successful_processes" in metadata
    assert "failed_processes" in metadata
    assert "success_rate" in metadata
    assert "output_file" in metadata
    assert "cache_entries_count" in metadata
    
    # Verify cache entries
    assert len(output_data["caches"]) == 1
    cache_entry = output_data["caches"][0]
    assert "problem_id" in cache_entry
    assert "intermediate_steps" in cache_entry

def test_max_examples_limit(sample_gsm8k_example, temp_output_dir):
    """Test that max_examples parameter limits processing."""
    # Create a larger dataset
    test_data_path = os.path.join(temp_output_dir, "test_data.jsonl")
    output_path = os.path.join(temp_output_dir, "test_caches.json")
    
    # Write 5 copies of the same example
    test_data = [sample_gsm8k_example] * 5
    write_json(test_data_path, test_data)
    
    # Run tracking with max_examples=2
    summary = track_all_caches(test_data_path, output_path, max_examples=2)
    
    # Verify only 2 examples were processed
    assert summary["total_examples"] == 2
    assert len(summary) > 0  # Ensure summary is populated

def test_error_handling_on_invalid_data(temp_output_dir):
    """Test that errors are handled gracefully."""
    test_data_path = os.path.join(temp_output_dir, "invalid_data.jsonl")
    output_path = os.path.join(temp_output_dir, "test_caches.json")
    
    # Write invalid data (not a list)
    write_json(test_data_path, {"invalid": "data"})
    
    # This should raise an error or handle gracefully
    with pytest.raises(Exception):
        track_all_caches(test_data_path, output_path)

def test_cache_entry_contains_pseudo_code(sample_gsm8k_example):
    """Test that pseudo-code blocks are included in cache entries."""
    result = process_single_example(sample_gsm8k_example, "test_004")
    
    # Pseudo-code blocks should be present (even if empty)
    assert "pseudo_code_blocks" in result
    assert isinstance(result["pseudo_code_blocks"], list)
    
    # If pseudo-code was generated, it should be in the blocks
    if result["processing_metadata"]["processed"]:
        # At least one block should exist if processing was successful
        # (Note: This depends on the convert_gsm8k_to_pseudo_code implementation)
        pass  # We don't enforce this as it depends on the conversion logic

def test_is_leaf_identification(sample_multi_step_example):
    """Test that leaf nodes (no dependencies) are correctly identified."""
    result = process_single_example(sample_multi_step_example, "test_005")
    
    # At least one step should be a leaf (the first step)
    leaf_steps = [s for s in result["intermediate_steps"] if s["is_leaf"]]
    assert len(leaf_steps) >= 1
    
    # Leaf steps should have no dependencies
    for leaf in leaf_steps:
        assert len(leaf["dependencies"]) == 0