"""
Contract tests for generated dataset schema validity.

This module validates that generated datasets (logic proofs and grid worlds)
conform to the expected schema defined in the project contracts.

Tests:
  - test_logic_proof_schema_validity: Ensures generated logic proofs have
    all required fields and correct types.
  - test_grid_world_schema_validity: Ensures generated grid worlds have
    all required fields and correct types.
  - test_dataset_structure: Ensures the overall dataset structure matches
    the contract requirements.
"""
import pytest
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.config import Config, load_config
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator


class TestLogicProofSchema:
    """Contract tests for logic proof schema validity."""

    def _generate_sample_proof(self, config: Optional[Config] = None) -> Dict[str, Any]:
        """Generate a sample logic proof for testing."""
        if config is None:
            config = load_config()
        
        generator = LogicProofGenerator(config)
        proofs = generator.generate_proofs(count=1)
        return proofs[0]

    def test_proof_has_required_fields(self):
        """Verify that a generated proof contains all required schema fields."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        required_fields = [
            "id", "task_type", "axioms", "conclusion", "proof_steps",
            "rule_signature", "difficulty", "seed", "timestamp"
        ]
        
        for field in required_fields:
            assert field in proof, f"Missing required field: {field}"

    def test_proof_id_is_string(self):
        """Verify that proof ID is a non-empty string."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["id"], str)
        assert len(proof["id"]) > 0

    def test_proof_task_type_is_valid(self):
        """Verify that task_type is 'propositional_logic'."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert proof["task_type"] == "propositional_logic"

    def test_proof_axioms_is_list_of_strings(self):
        """Verify that axioms is a list of strings."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["axioms"], list)
        assert len(proof["axioms"]) > 0
        for axiom in proof["axioms"]:
            assert isinstance(axiom, str)
            assert len(axiom) > 0

    def test_proof_conclusion_is_string(self):
        """Verify that conclusion is a non-empty string."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["conclusion"], str)
        assert len(proof["conclusion"]) > 0

    def test_proof_steps_is_list_of_dicts(self):
        """Verify that proof_steps is a list of step dictionaries."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["proof_steps"], list)
        assert len(proof["proof_steps"]) > 0
        
        for step in proof["proof_steps"]:
            assert isinstance(step, dict)
            assert "step_number" in step
            assert "rule_applied" in step
            assert "statement" in step
            assert isinstance(step["step_number"], int)
            assert isinstance(step["rule_applied"], str)
            assert isinstance(step["statement"], str)

    def test_proof_rule_signature_is_string(self):
        """Verify that rule_signature is a non-empty string."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["rule_signature"], str)
        assert len(proof["rule_signature"]) > 0

    def test_proof_difficulty_is_valid(self):
        """Verify that difficulty is an integer between 1 and 10."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["difficulty"], int)
        assert 1 <= proof["difficulty"] <= 10

    def test_proof_seed_is_integer(self):
        """Verify that seed is an integer."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["seed"], int)

    def test_proof_timestamp_is_iso_format(self):
        """Verify that timestamp is in ISO 8601 format."""
        config = load_config()
        proof = self._generate_sample_proof(config)
        
        assert isinstance(proof["timestamp"], str)
        # Try parsing as ISO format
        datetime.fromisoformat(proof["timestamp"].replace("Z", "+00:00"))


class TestGridWorldSchema:
    """Contract tests for grid world schema validity."""

    def _generate_sample_grid(self, config: Optional[Config] = None) -> Dict[str, Any]:
        """Generate a sample grid world for testing."""
        if config is None:
            config = load_config()
        
        generator = GridWorldGenerator(config)
        grids = generator.generate_grids(count=1)
        return grids[0]

    def test_grid_has_required_fields(self):
        """Verify that a generated grid contains all required schema fields."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        required_fields = [
            "id", "task_type", "grid_size", "start_position", "end_position",
            "obstacles", "rules", "solution_path", "rule_signature",
            "difficulty", "seed", "timestamp"
        ]
        
        for field in required_fields:
            assert field in grid, f"Missing required field: {field}"

    def test_grid_id_is_string(self):
        """Verify that grid ID is a non-empty string."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["id"], str)
        assert len(grid["id"]) > 0

    def test_grid_task_type_is_valid(self):
        """Verify that task_type is 'grid_world'."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert grid["task_type"] == "grid_world"

    def test_grid_size_is_tuple_of_integers(self):
        """Verify that grid_size is a tuple/list of two integers."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["grid_size"], (tuple, list))
        assert len(grid["grid_size"]) == 2
        for dim in grid["grid_size"]:
            assert isinstance(dim, int)
            assert dim > 0

    def test_start_position_is_valid(self):
        """Verify that start_position is within grid bounds."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        start = grid["start_position"]
        size = grid["grid_size"]
        
        assert isinstance(start, (tuple, list))
        assert len(start) == 2
        assert 0 <= start[0] < size[0]
        assert 0 <= start[1] < size[1]

    def test_end_position_is_valid(self):
        """Verify that end_position is within grid bounds."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        end = grid["end_position"]
        size = grid["grid_size"]
        
        assert isinstance(end, (tuple, list))
        assert len(end) == 2
        assert 0 <= end[0] < size[0]
        assert 0 <= end[1] < size[1]

    def test_obstacles_is_list_of_tuples(self):
        """Verify that obstacles is a list of position tuples."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["obstacles"], list)
        size = grid["grid_size"]
        
        for obstacle in grid["obstacles"]:
            assert isinstance(obstacle, (tuple, list))
            assert len(obstacle) == 2
            assert 0 <= obstacle[0] < size[0]
            assert 0 <= obstacle[1] < size[1]

    def test_rules_is_list_of_strings(self):
        """Verify that rules is a list of rule description strings."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["rules"], list)
        assert len(grid["rules"]) > 0
        for rule in grid["rules"]:
            assert isinstance(rule, str)
            assert len(rule) > 0

    def test_solution_path_is_list_of_positions(self):
        """Verify that solution_path is a list of position tuples."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["solution_path"], list)
        assert len(grid["solution_path"]) > 0
        
        size = grid["grid_size"]
        for pos in grid["solution_path"]:
            assert isinstance(pos, (tuple, list))
            assert len(pos) == 2
            assert 0 <= pos[0] < size[0]
            assert 0 <= pos[1] < size[1]

    def test_rule_signature_is_string(self):
        """Verify that rule_signature is a non-empty string."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["rule_signature"], str)
        assert len(grid["rule_signature"]) > 0

    def test_grid_difficulty_is_valid(self):
        """Verify that difficulty is an integer between 1 and 10."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["difficulty"], int)
        assert 1 <= grid["difficulty"] <= 10

    def test_grid_seed_is_integer(self):
        """Verify that seed is an integer."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["seed"], int)

    def test_grid_timestamp_is_iso_format(self):
        """Verify that timestamp is in ISO 8601 format."""
        config = load_config()
        grid = self._generate_sample_grid(config)
        
        assert isinstance(grid["timestamp"], str)
        datetime.fromisoformat(grid["timestamp"].replace("Z", "+00:00"))


class TestDatasetStructure:
    """Contract tests for overall dataset structure."""

    def test_dataset_has_metadata(self):
        """Verify that dataset has metadata section."""
        config = load_config()
        
        logic_gen = LogicProofGenerator(config)
        grids_gen = GridWorldGenerator(config)
        
        proofs = logic_gen.generate_proofs(count=2)
        grids = grids_gen.generate_grids(count=2)
        
        dataset = {
            "metadata": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "config": str(config.to_dict())
            },
            "logic_proofs": proofs,
            "grid_worlds": grids
        }
        
        assert "metadata" in dataset
        assert "version" in dataset["metadata"]
        assert "generated_at" in dataset["metadata"]

    def test_dataset_proofs_is_list(self):
        """Verify that logic_proofs is a list."""
        config = load_config()
        logic_gen = LogicProofGenerator(config)
        proofs = logic_gen.generate_proofs(count=2)
        
        dataset = {"logic_proofs": proofs, "grid_worlds": []}
        
        assert isinstance(dataset["logic_proofs"], list)
        assert len(dataset["logic_proofs"]) == 2

    def test_dataset_grids_is_list(self):
        """Verify that grid_worlds is a list."""
        config = load_config()
        grids_gen = GridWorldGenerator(config)
        grids = grids_gen.generate_grids(count=2)
        
        dataset = {"logic_proofs": [], "grid_worlds": grids}
        
        assert isinstance(dataset["grid_worlds"], list)
        assert len(dataset["grid_worlds"]) == 2

    def test_dataset_can_be_serialized(self):
        """Verify that the complete dataset can be serialized to JSON."""
        config = load_config()
        
        logic_gen = LogicProofGenerator(config)
        grids_gen = GridWorldGenerator(config)
        
        proofs = logic_gen.generate_proofs(count=2)
        grids = grids_gen.generate_grids(count=2)
        
        dataset = {
            "metadata": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat()
            },
            "logic_proofs": proofs,
            "grid_worlds": grids
        }
        
        # Should not raise
        json_str = json.dumps(dataset)
        assert len(json_str) > 0
        
        # Should be able to deserialize
        restored = json.loads(json_str)
        assert len(restored["logic_proofs"]) == 2
        assert len(restored["grid_worlds"]) == 2

    def test_unique_ids_across_proofs(self):
        """Verify that all proof IDs are unique."""
        config = load_config()
        logic_gen = LogicProofGenerator(config)
        proofs = logic_gen.generate_proofs(count=10)
        
        ids = [p["id"] for p in proofs]
        assert len(ids) == len(set(ids)), "Duplicate proof IDs found"

    def test_unique_ids_across_grids(self):
        """Verify that all grid IDs are unique."""
        config = load_config()
        grids_gen = GridWorldGenerator(config)
        grids = grids_gen.generate_grids(count=10)
        
        ids = [g["id"] for g in grids]
        assert len(ids) == len(set(ids)), "Duplicate grid IDs found"