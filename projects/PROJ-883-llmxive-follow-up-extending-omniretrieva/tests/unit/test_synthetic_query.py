"""
Unit tests for SyntheticQueryGenerator (T006).

Verifies that:
1. Queries are generated with integer complexity_level (1, 2, 3, 4).
2. ground_truth_plan is assigned via ReferenceEngine.
3. Output structure matches requirements.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path

# Add code directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generators.synthetic_query import SyntheticQueryGenerator
from generators.reference_engine import ReferenceEngine


class TestSyntheticQueryGenerator:
    """Tests for the SyntheticQueryGenerator class."""

    def test_initialization(self):
        """Test generator initializes correctly."""
        gen = SyntheticQueryGenerator(seed=42)
        assert gen.seed == 42
        assert gen.complexity_levels == [1, 2, 3, 4]
        assert isinstance(gen.engine, ReferenceEngine)

    def test_generate_structure_depth_1(self):
        """Test structure generation for complexity level 1."""
        gen = SyntheticQueryGenerator(seed=42)
        structure = gen._generate_query_structure(1)
        
        assert structure["target_depth"] == 1
        assert "filter" in structure["operations"]
        assert len(structure["nodes"]) > 0
        assert len(structure["edges"]) > 0

    def test_generate_structure_depth_4(self):
        """Test structure generation for complexity level 4."""
        gen = SyntheticQueryGenerator(seed=42)
        structure = gen._generate_query_structure(4)
        
        assert structure["target_depth"] == 4
        assert "recursive_lookup" in structure["operations"]

    def test_generate_queries_complexity_levels(self):
        """Test that generated queries have correct integer complexity_level."""
        gen = SyntheticQueryGenerator(seed=42)
        queries = gen.generate_queries(count=20)
        
        assert len(queries) == 20
        
        levels_found = set()
        for q in queries:
            assert "complexity_level" in q
            assert isinstance(q["complexity_level"], int)
            assert q["complexity_level"] in [1, 2, 3, 4]
            levels_found.add(q["complexity_level"])
            
            # Verify ground_truth_plan exists and is a dict
            assert "ground_truth_plan" in q
            assert isinstance(q["ground_truth_plan"], dict)
            assert "steps" in q["ground_truth_plan"]
            assert "estimated_depth" in q["ground_truth_plan"]

        # Ensure we have at least one of each level (with count=20, likely all)
        # Note: With 20 queries and 4 levels, we expect 5 per level
        assert levels_found == {1, 2, 3, 4}

    def test_save_queries_creates_file(self):
        """Test that save_queries creates a valid JSON file."""
        gen = SyntheticQueryGenerator(seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_queries.json")
            gen.save_queries(output_path, count=10)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 10
            assert all("complexity_level" in q for q in data)
            assert all("ground_truth_plan" in q for q in data)

    def test_ground_truth_plan_determinism(self):
        """Test that same seed produces same ground truth plans."""
        gen1 = SyntheticQueryGenerator(seed=999)
        gen2 = SyntheticQueryGenerator(seed=999)
        
        q1 = gen1.generate_queries(count=5)[0]
        q2 = gen2.generate_queries(count=5)[0]
        
        # Plan IDs might be randomized in the engine if not seeded perfectly,
        # but the structure of the plan (steps, depth) should be deterministic
        # given the same input structure and engine seed.
        assert q1["complexity_level"] == q2["complexity_level"]
        assert len(q1["ground_truth_plan"]["steps"]) == len(q2["ground_truth_plan"]["steps"])
        assert q1["ground_truth_plan"]["estimated_depth"] == q2["ground_truth_plan"]["estimated_depth"]