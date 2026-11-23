import pytest
import sys
import os
from typing import List, Dict, Any, Tuple, Set
from pathlib import Path

# Add project root to path to allow src imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.generators.grid_generator import GridWorldGenerator
from src.utils.config import Config, get_default_config
from src.generators.logic_generator import LogicProofGenerator
from src.analysis.validate_dataset import validate_grid_worlds, validate_logic_proofs


class TestGridSolvability:
    """Tests for grid-world solvability ensuring generated grids are navigable."""

    def test_generated_grid_is_solvable(self, tmp_path):
        """Verify that generated grid worlds are solvable by the agent."""
        config = get_default_config()
        config.grid_worlds_count = 5
        config.grid_size = 5
        config.max_attempts = 100

        generator = GridWorldGenerator(config)
        grids = generator.generate_grids()

        assert len(grids) == 5, "Should generate exactly 5 grids"

        for grid in grids:
            # Validate grid structure
            assert "grid" in grid
            assert "rules" in grid
            assert "start" in grid
            assert "end" in grid

            # Use the validation function to check solvability
            result = validate_grid_worlds([grid])
            assert result["valid_count"] == 1, f"Grid should be solvable: {grid.get('id')}"
            assert result["solvability_rate"] == 1.0

    def test_grid_with_obstacles_is_solvable(self, tmp_path):
        """Verify grids with obstacles can still be navigated."""
        config = get_default_config()
        config.grid_worlds_count = 3
        config.grid_size = 6
        config.obstacle_density = 0.3  # Higher obstacle density
        config.max_attempts = 150

        generator = GridWorldGenerator(config)
        grids = generator.generate_grids()

        for grid in grids:
            result = validate_grid_worlds([grid])
            assert result["valid_count"] == 1, f"Grid with obstacles should be solvable: {grid.get('id')}"


class TestRuleIsolation:
    """Tests for rule isolation ensuring different task domains have distinct rule sets."""

    def test_distinct_rule_sets_for_domains(self, tmp_path):
        """Verify that logic proofs and grid worlds have distinct, identifiable rule signatures."""
        config = get_default_config()
        config.logic_proofs_count = 10
        config.grid_worlds_count = 10
        config.max_attempts = 100

        # Generate logic proofs
        logic_gen = LogicProofGenerator(config)
        proofs = logic_gen.generate_proofs()

        # Generate grid worlds
        grid_gen = GridWorldGenerator(config)
        grids = grid_gen.generate_grids()

        # Extract rule signatures
        proof_rules = set()
        for proof in proofs:
            if "rule_signature" in proof:
                proof_rules.add(proof["rule_signature"])

        grid_rules = set()
        for grid in grids:
            if "rule_signature" in grid:
                grid_rules.add(grid["rule_signature"])

        # Verify distinct signatures (no overlap between domains)
        assert len(proof_rules) > 0, "Logic proofs should have rule signatures"
        assert len(grid_rules) > 0, "Grid worlds should have rule signatures"
        assert proof_rules.isdisjoint(grid_rules), "Rule signatures should be distinct between domains"

    def test_rule_isolation_within_domain(self, tmp_path):
        """Verify that within a domain, different rule sets are generated."""
        config = get_default_config()
        config.logic_proofs_count = 20
        config.max_attempts = 100

        logic_gen = LogicProofGenerator(config)
        proofs = logic_gen.generate_proofs()

        rule_signatures = set()
        for proof in proofs:
            if "rule_signature" in proof:
                rule_signatures.add(proof["rule_signature"])

        # Should have multiple distinct rule sets
        assert len(rule_signatures) >= 3, f"Should have at least 3 distinct rule sets, got {len(rule_signatures)}"


class TestGridGenerationConstraints:
    """Tests for grid generation constraints and retry logic."""

    def test_retry_logic_for_unsolvable_grids(self, tmp_path):
        """Verify retry logic works when generating grids."""
        config = get_default_config()
        config.grid_worlds_count = 2
        config.grid_size = 4
        config.max_attempts = 50

        generator = GridWorldGenerator(config)
        grids = generator.generate_grids()

        assert len(grids) == 2, "Should generate 2 grids despite retry attempts"
        for grid in grids:
            result = validate_grid_worlds([grid])
            assert result["valid_count"] == 1

    def test_grid_dimensions(self, tmp_path):
        """Verify generated grids have correct dimensions."""
        config = get_default_config()
        config.grid_worlds_count = 5
        config.grid_size = 7
        config.max_attempts = 100

        generator = GridWorldGenerator(config)
        grids = generator.generate_grids()

        for grid in grids:
            grid_data = grid["grid"]
            assert len(grid_data) == 7, "Grid should have 7 rows"
            assert all(len(row) == 7 for row in grid_data), "Each row should have 7 columns"


class TestLogicProofGeneration:
    """Tests for logic proof generation validity."""

    def test_generated_proofs_are_valid(self, tmp_path):
        """Verify that generated logic proofs are mathematically valid."""
        config = get_default_config()
        config.logic_proofs_count = 10
        config.max_attempts = 100

        generator = LogicProofGenerator(config)
        proofs = generator.generate_proofs()

        assert len(proofs) == 10, "Should generate 10 proofs"

        for proof in proofs:
            result = validate_logic_proofs([proof])
            assert result["valid_count"] == 1, f"Proof should be valid: {proof.get('id')}"
            assert result["validity_rate"] == 1.0

    def test_proof_complexity_variation(self, tmp_path):
        """Verify that generated proofs have varying complexity."""
        config = get_default_config()
        config.logic_proofs_count = 15
        config.max_attempts = 100

        generator = LogicProofGenerator(config)
        proofs = generator.generate_proofs()

        complexities = [p.get("complexity", 0) for p in proofs if "complexity" in p]

        assert len(complexities) > 0, "Should have complexity metrics"
        # Should have some variation
        assert max(complexities) != min(complexities), "Proofs should have varying complexity"


class TestIntegration:
    """Integration tests for the full generation pipeline."""

    def test_full_generation_and_validation(self, tmp_path):
        """Test the complete generation and validation flow."""
        config = get_default_config()
        config.logic_proofs_count = 5
        config.grid_worlds_count = 5
        config.max_attempts = 100

        # Generate both types of data
        logic_gen = LogicProofGenerator(config)
        proofs = logic_gen.generate_proofs()

        grid_gen = GridWorldGenerator(config)
        grids = grid_gen.generate_grids()

        # Validate all proofs
        proof_result = validate_logic_proofs(proofs)
        assert proof_result["validity_rate"] == 1.0
        assert proof_result["valid_count"] == len(proofs)

        # Validate all grids
        grid_result = validate_grid_worlds(grids)
        assert grid_result["solvability_rate"] == 1.0
        assert grid_result["valid_count"] == len(grids)

        # Verify rule isolation
        proof_rules = {p["rule_signature"] for p in proofs if "rule_signature" in p}
        grid_rules = {g["rule_signature"] for g in grids if "rule_signature" in g}
        assert proof_rules.isdisjoint(grid_rules), "Domains should have distinct rule signatures"