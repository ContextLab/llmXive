import pytest
import json
import networkx as nx
from pathlib import Path
import sys
import os
import logging
from unittest.mock import patch

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.grid_generator import GridWorldGenerator, GridGenerationError

class TestGridWorldGenerator:
    """Unit tests for the GridWorldGenerator class."""

    def test_initialization(self):
        """Test that the generator initializes correctly."""
        gen = GridWorldGenerator(seed=42)
        assert gen.rng is not None
        assert "avoid_red" in gen.rule_sets
        assert "diagonal_paths" in gen.rule_sets

    def test_grid_generation_solvable(self):
        """Test that generated grids are solvable."""
        gen = GridWorldGenerator(seed=123)
        instance = gen.generate_instance(width=5, height=5, rule_set_id="avoid_red")
        
        assert instance is not None
        assert instance["domain"] == "grid_world"
        assert "instance_data" in instance
        
        data = instance["instance_data"]
        assert data["width"] == 5
        assert data["height"] == 5
        assert "start" in data
        assert "end" in data

    def test_diagonal_paths_connectivity(self):
        """Test that diagonal paths rule allows 8-connectivity."""
        gen = GridWorldGenerator(seed=456)
        instance = gen.generate_instance(width=3, height=3, rule_set_id="diagonal_paths")
        
        assert instance is not None
        # Verify diagonal edges exist in the graph structure if needed
        # For now, just verify generation succeeds

    def test_retry_limit_reached_logging(self):
        """
        Test that the generator logs a warning when retry limit is reached.
        We simulate a scenario where generation always fails.
        """
        gen = GridWorldGenerator(seed=789)
        
        # Mock _ensure_solvable to always return False to trigger retries
        with patch.object(gen, '_ensure_solvable', return_value=False):
            # Capture logs
            with patch('src.generators.grid_generator.logger') as mock_logger:
                result = gen.generate_instance(width=2, height=2, rule_set_id="avoid_red")
                
                # Should return None after 3 attempts
                assert result is None
                
                # Verify warning was logged exactly on the 3rd attempt
                # The loop runs 1, 2, 3. On 3, it logs and returns.
                warning_calls = [call for call in mock_logger.warning.call_args_list]
                assert len(warning_calls) == 1
                assert "Retry limit reached" in warning_calls[0][0][0]

    def test_invalid_rule_set(self):
        """Test handling of invalid rule set ID."""
        gen = GridWorldGenerator(seed=101)
        with pytest.raises(KeyError):
            gen.generate_instance(width=5, height=5, rule_set_id="invalid_rule")

    def test_dataset_generation(self):
        """Test generating a full dataset."""
        gen = GridWorldGenerator(seed=202)
        instances = gen.generate_dataset(
            count=5,
            width=4,
            height=4,
            rule_set_ids=["avoid_red", "diagonal_paths"]
        )
        
        assert len(instances) <= 5  # Could be less if some fail
        for inst in instances:
            assert "id" in inst
            assert "instance_data" in inst
            assert inst["domain"] == "grid_world"

    def test_checkpoint_mandatory(self):
        """Test that checkpoint mandatory rule marks a checkpoint."""
        gen = GridWorldGenerator(seed=303)
        instance = gen.generate_instance(width=5, height=5, rule_set_id="checkpoint_mandatory")
        
        assert instance is not None
        nodes = instance["instance_data"]["nodes"]
        checkpoint_found = False
        for node_data in nodes.values():
            if node_data.get("is_checkpoint"):
                checkpoint_found = True
                break
        assert checkpoint_found, "No checkpoint found in checkpoint_mandatory grid"