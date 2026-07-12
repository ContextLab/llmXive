"""
Unit tests for the synthetic query generator.
"""
import pytest
import json
import os
from pathlib import Path
from code.data.generator import generate_query, generate_dataset, TEST_SET_PATH, WARMUP_SET_PATH

def test_generate_query_structure():
    """Test that generated query has all required keys."""
    seed = 12345
    domain = "physics"
    query = generate_query(seed, domain)
    
    required_keys = {"prompt", "ground_truth", "steps", "seed", "domain"}
    assert set(query.keys()) == required_keys, f"Missing keys: {required_keys - set(query.keys())}"
    
    assert isinstance(query["prompt"], str) and len(query["prompt"]) > 0
    assert isinstance(query["ground_truth"], str) and len(query["ground_truth"]) > 0
    assert isinstance(query["steps"], list) and len(query["steps"]) > 0
    assert query["seed"] == seed
    assert query["domain"] == domain

def test_generate_query_reproducibility():
    """Test that same seed produces same query."""
    seed = 99999
    domain = "chemistry"
    query1 = generate_query(seed, domain)
    query2 = generate_query(seed, domain)
    
    assert query1 == query2, "Same seed should produce identical queries"

def test_generate_dataset_creates_file(tmp_path):
    """Test that generate_dataset creates a valid JSON file."""
    test_output = tmp_path / "test_queries.json"
    num_queries = 10
    
    generate_dataset(num_queries, test_output, base_seed=500000)
    
    assert test_output.exists(), "Output file was not created"
    
    with open(test_output, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data) == num_queries, f"Expected {num_queries} queries, got {len(data)}"
    
    # Verify structure of each query
    for i, query in enumerate(data):
        required_keys = {"prompt", "ground_truth", "steps", "seed", "domain"}
        assert set(query.keys()) == required_keys, f"Query {i} missing keys"
        assert isinstance(query["steps"], list), f"Query {i} steps must be a list"

def test_test_set_generation():
    """Test that the test set is generated correctly."""
    # We don't actually run the full generation here to save time,
    # but we verify the function can be called
    assert TEST_SET_PATH.parent.exists() or TEST_SET_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate a small sample to test
    test_file = Path("data/derived/test_sample.json")
    generate_dataset(5, test_file, base_seed=888888)
    
    assert test_file.exists()
    with open(test_file, 'r') as f:
        data = json.load(f)
    assert len(data) == 5
    
    # Cleanup
    test_file.unlink()

def test_domain_coverage():
    """Test that all domains are represented in generation."""
    from code.data.generator import DOMAINS
    
    for domain in DOMAINS:
        query = generate_query(123, domain)
        assert query["domain"] == domain
        assert "Answer for" in query["ground_truth"]
        assert domain in query["ground_truth"]

def test_seed_independence():
    """Test that different seeds produce different queries."""
    domain = "biology"
    query1 = generate_query(100, domain)
    query2 = generate_query(200, domain)
    
    # They should be different (very high probability)
    assert query1 != query2, "Different seeds should produce different queries"
