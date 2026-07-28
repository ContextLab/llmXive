"""
Unit tests for the TestInstanceGenerator.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.test_generator import TestInstanceGenerator, TestGenerationError
from src.utils.config import Config, get_default_config


class TestTestInstanceGenerator:
    """Tests for the TestInstanceGenerator class."""

    @pytest.fixture
    def config(self):
        """Create a minimal config for testing."""
        cfg = get_default_config()
        cfg.seed = 42
        cfg.test_logic_count = 5
        cfg.test_grid_count = 5
        cfg.test_output_path = "data/test_instances.json"
        return cfg

    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary file path for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_initialization(self, config):
        """Test that the generator initializes correctly."""
        generator = TestInstanceGenerator(config)
        assert generator.config == config
        assert generator.logic_generator is not None
        assert generator.grid_generator is not None
        assert generator.test_seed_base == config.seed + 10000

    def test_generate_logic_proofs(self, config):
        """Test generation of logic proofs."""
        generator = TestInstanceGenerator(config)
        proofs = generator.generate_logic_proofs(3)
        
        assert len(proofs) == 3
        for proof in proofs:
            assert "axioms" in proof
            assert "conclusion" in proof
            assert "proof_steps" in proof
            assert "valid" in proof

    def test_generate_grid_worlds(self, config):
        """Test generation of grid worlds."""
        generator = TestInstanceGenerator(config)
        grids = generator.generate_grid_worlds(3)
        
        assert len(grids) == 3
        for grid in grids:
            assert "grid" in grid
            assert "start" in grid
            assert "goal" in grid
            assert "rules" in grid

    def test_generate_all_test_instances(self, config, temp_output_path):
        """Test full generation and file writing."""
        config.test_output_path = temp_output_path
        generator = TestInstanceGenerator(config)
        result = generator.generate_all_test_instances()

        assert "metadata" in result
        assert "logic_proofs" in result
        assert "grid_worlds" in result
        assert result["metadata"]["logic_count"] == 5
        assert result["metadata"]["grid_count"] == 5

        # Verify file was written
        assert os.path.exists(temp_output_path)
        
        with open(temp_output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == result

    def test_distinct_seeds(self, config):
        """Test that test instances use distinct seeds from training."""
        generator = TestInstanceGenerator(config)
        
        # The test seed base should be offset from the config seed
        assert generator.test_seed_base == config.seed + 10000

    def test_invalid_generation_raises_error(self, config, monkeypatch):
        """Test that generation errors are propagated correctly."""
        generator = TestInstanceGenerator(config)
        
        # Mock the logic generator to raise an exception
        def mock_generate(*args, **kwargs):
            raise ValueError("Simulated generation failure")
        
        monkeypatch.setattr(generator.logic_generator, 'generate_single_proof', mock_generate)
        
        with pytest.raises(TestGenerationError):
            generator.generate_logic_proofs(1)