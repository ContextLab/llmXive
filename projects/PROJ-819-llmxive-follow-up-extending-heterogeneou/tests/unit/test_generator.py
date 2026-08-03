import json
import os
import pytest
from pathlib import Path
import sys

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.generator import (
    generate_random_float,
    generate_random_int,
    generate_query,
    generate_dataset,
    DOMAINS
)

class TestGeneratorFunctions:
    """Tests for the generator module functions."""

    def test_generate_random_float(self):
        """Test that random float generation works correctly."""
        value = generate_random_float(0.0, 1.0, 4)
        assert 0.0 <= value <= 1.0
        assert len(str(value).split('.')[-1]) <= 4

    def test_generate_random_int(self):
        """Test that random int generation works correctly."""
        value = generate_random_int(1, 100)
        assert 1 <= value <= 100
        assert isinstance(value, int)

    def test_generate_query_structure(self):
        """Test that generated query has the correct structure."""
        query = generate_query("physics", 12345)
        
        assert "id" in query
        assert "prompt" in query
        assert "ground_truth" in query
        assert "steps" in query
        assert "seed" in query
        assert "domain" in query
        
        assert isinstance(query["id"], str)
        assert isinstance(query["prompt"], str)
        assert isinstance(query["ground_truth"], str)
        assert isinstance(query["steps"], list)
        assert isinstance(query["seed"], int)
        assert query["domain"] == "physics"

    def test_generate_query_domain_coverage(self):
        """Test that queries are generated for different domains."""
        for domain in DOMAINS:
            query = generate_query(domain, 99999)
            assert query["domain"] == domain
            assert domain in query["ground_truth"].lower() or domain in query["prompt"].lower()

    def test_generate_dataset_creates_file(self, tmp_path):
        """Test that generate_dataset creates the output file."""
        output_file = tmp_path / "test_queries.json"
        
        generate_dataset(
            num_queries=10,
            output_path=str(output_file),
            dataset_type="test"
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 10
        assert all("prompt" in q for q in data)
        assert all("ground_truth" in q for q in data)

    def test_warmup_set_generation(self, tmp_path):
        """Test warmup set generation specifically for T005a."""
        output_file = tmp_path / "synthetic_queries_warmup.json"
        
        generate_dataset(
            num_queries=100,
            output_path=str(output_file),
            dataset_type="warmup"
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 100
        
        # Verify schema matches test set requirements
        required_keys = {"prompt", "ground_truth", "steps", "seed", "domain"}
        for query in data:
            assert set(query.keys()) == required_keys, f"Query missing keys: {set(query.keys()) - required_keys}"
        
        # Verify all queries have valid domains
        domains_in_data = set(q["domain"] for q in data)
        assert domains_in_data.issubset(set(DOMAINS))

    def test_reproducibility(self):
        """Test that the same seed produces the same query."""
        query1 = generate_query("biology", 54321)
        query2 = generate_query("biology", 54321)
        
        assert query1["id"] == query2["id"]
        assert query1["prompt"] == query2["prompt"]
        assert query1["ground_truth"] == query2["ground_truth"]

    def test_ground_truth_structure(self):
        """Test that ground truth contains expected structure."""
        query = generate_query("chemistry", 11111)
        
        # Ground truth should be a string
        assert isinstance(query["ground_truth"], str)
        assert len(query["ground_truth"]) > 0
        
        # Steps should be a list of strings
        assert isinstance(query["steps"], list)
        assert len(query["steps"]) > 0
        assert all(isinstance(step, str) for step in query["steps"])
        
        # Steps should contain domain references
        domain = query["domain"]
        steps_text = " ".join(query["steps"])
        assert domain in steps_text.lower() or any(domain in step for step in query["steps"])
