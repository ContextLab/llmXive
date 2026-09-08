"""
Unit tests for the TestInstanceGenerator module.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path if necessary
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.test_generator import TestInstanceGenerator, TestGenerationError
from src.utils.config import Config


class TestTestInstanceGenerator:
    """Unit tests for TestInstanceGenerator."""

    @pytest.fixture
    def test_config(self):
        """Create a minimal config for testing."""
        return Config(
            seed=42,
            num_training_instances=100,
            num_test_instances=10,
            num_test_logic_instances=5,
            num_test_grid_instances=5,
            data_dir=Path(tempfile.mkdtemp()),
            test_instances_path=Path(tempfile.mkdtemp()) / "test_instances.json",
            checksums_path=Path(tempfile.mkdtemp()) / "checksums.json"
        )

    def test_initialization(self, test_config):
        """Test that the generator initializes correctly."""
        generator = TestInstanceGenerator(test_config)
        assert generator.config == test_config
        assert generator.test_seed_start == 100
        assert generator.test_seed_end == 110

    def test_generate_logic_test_instances(self, test_config):
        """Test generation of logic test instances."""
        generator = TestInstanceGenerator(test_config)
        instances = generator.generate_logic_test_instances()
        
        assert isinstance(instances, list)
        assert len(instances) == test_config.num_test_logic_instances
        
        for instance in instances:
            assert '_metadata' in instance
            assert instance['_metadata']['set'] == 'held-out-test'
            assert 'valid' in instance
            assert instance['valid'] is True

    def test_generate_grid_test_instances(self, test_config):
        """Test generation of grid test instances."""
        generator = TestInstanceGenerator(test_config)
        instances = generator.generate_grid_test_instances()
        
        assert isinstance(instances, list)
        assert len(instances) == test_config.num_test_grid_instances
        
        for instance in instances:
            assert '_metadata' in instance
            assert instance['_metadata']['set'] == 'held-out-test'
            assert 'solvable' in instance
            assert instance['solvable'] is True

    def test_generate_all_test_instances(self, test_config):
        """Test generation of all test instances."""
        generator = TestInstanceGenerator(test_config)
        result = generator.generate_all_test_instances()
        
        assert 'metadata' in result
        assert 'logic_proofs' in result
        assert 'grid_worlds' in result
        
        assert len(result['logic_proofs']) == test_config.num_test_logic_instances
        assert len(result['grid_worlds']) == test_config.num_test_grid_instances
        
        # Verify metadata
        assert result['metadata']['separation_from_training'] is True
        assert result['metadata']['total_logic_instances'] == test_config.num_test_logic_instances
        assert result['metadata']['total_grid_instances'] == test_config.num_test_grid_instances

    def test_save_test_instances(self, test_config):
        """Test saving test instances to a file."""
        generator = TestInstanceGenerator(test_config)
        output_path = generator.save_test_instances()
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'logic_proofs' in data
        assert 'grid_worlds' in data
        
        # Verify checksum file was updated
        assert os.path.exists(test_config.checksums_path)
        with open(test_config.checksums_path, 'r') as f:
            checksums = json.load(f)
        
        assert 'test_instances' in checksums
        assert checksums['test_instances']['file'] == output_path

    def test_seed_separation(self, test_config):
        """Test that test seeds are distinct from training seeds."""
        generator = TestInstanceGenerator(test_config)
        
        # Training seeds: 0 to 99
        # Test seeds: 100 to 109
        logic_instances = generator.generate_logic_test_instances()
        
        for instance in logic_instances:
            seed = instance['_metadata']['seed']
            assert seed >= test_config.num_training_instances
            assert seed < test_config.num_training_instances + test_config.num_test_logic_instances

    def test_reproducibility(self, test_config):
        """Test that generation is reproducible with the same seed."""
        generator1 = TestInstanceGenerator(test_config)
        instances1 = generator1.generate_logic_test_instances()
        
        # Recreate generator with same config
        generator2 = TestInstanceGenerator(test_config)
        instances2 = generator2.generate_logic_test_instances()
        
        # Compare instances (excluding metadata which might have timestamps if added later)
        for i in range(len(instances1)):
            # Compare proof structure
            assert instances1[i]['axioms'] == instances2[i]['axioms']
            assert instances1[i]['conclusion'] == instances2[i]['conclusion']
            assert instances1[i]['proof_steps'] == instances2[i]['proof_steps']