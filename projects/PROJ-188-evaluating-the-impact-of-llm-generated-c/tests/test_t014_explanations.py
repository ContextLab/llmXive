import json
import os
import pytest
from pathlib import Path

# Test for T014: LLM Explanation Generation
# Note: These tests verify the structure and constraints of the output,
# assuming the generation script has been run successfully.

@pytest.fixture
def explanations_file():
    return Path("data/intermediate/explanations.json")

@pytest.fixture
def explanations_data(explanations_file):
    if not explanations_file.exists():
        pytest.skip("explanations.json not found. Run code/01_data_curation.py first.")
    with open(explanations_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_explanations_file_exists(explanations_file):
    """Test that the explanations file was created."""
    assert explanations_file.exists(), "explanations.json must exist"

def test_minimum_snippets(explanations_data):
    """Test that at least 20 snippets were processed (as per T016 requirement)."""
    assert len(explanations_data) >= 20, f"Expected >= 20 snippets, got {len(explanations_data)}"

def test_required_fields(explanations_data):
    """Test that all required fields are present in each record."""
    required_fields = [
        "snippet_id", "code", "complexity", "complexity_score",
        "explanation", "token_count", "model_used", "status"
    ]
    
    for i, record in enumerate(explanations_data):
        for field in required_fields:
            assert field in record, f"Record {i} missing field: {field}"

def test_no_null_explanations(explanations_data):
    """Test that no explanations are null or empty for successful records."""
    for i, record in enumerate(explanations_data):
        if record["status"] == "success":
            assert record["explanation"] is not None, f"Record {i} has null explanation"
            assert len(record["explanation"].strip()) > 0, f"Record {i} has empty explanation"

def test_token_limit(explanations_data):
    """Test that token counts do not exceed 200."""
    for i, record in enumerate(explanations_data):
        if record["status"] == "success":
            assert record["token_count"] <= 200, \
                f"Record {i} exceeds token limit: {record['token_count']} > 200"

def test_valid_complexity_labels(explanations_data):
    """Test that complexity labels are valid."""
    valid_labels = {"low", "medium", "high"}
    for i, record in enumerate(explanations_data):
        assert record["complexity"] in valid_labels, \
            f"Record {i} has invalid complexity label: {record['complexity']}"

def test_model_used_consistency(explanations_data):
    """Test that model_used is set for successful records."""
    for i, record in enumerate(explanations_data):
        if record["status"] == "success":
            assert record["model_used"] != "", \
                f"Record {i} has empty model_used for successful generation"
            assert record["model_used"] in [
                "CodeLlama-7B-Instruct-hf", 
                "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            ], f"Record {i} has unexpected model: {record['model_used']}"

def test_status_values(explanations_data):
    """Test that status values are valid."""
    valid_statuses = {"success", "skipped"}
    for i, record in enumerate(explanations_data):
        assert record["status"] in valid_statuses, \
            f"Record {i} has invalid status: {record['status']}"
