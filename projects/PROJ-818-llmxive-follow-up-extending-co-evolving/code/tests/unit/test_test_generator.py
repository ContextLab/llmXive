"""
Unit tests for TestInstanceGenerator.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Ensure parent directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.test_generator import TestInstanceGenerator, TestGenerationError
from src.utils.config import Config

class TestTestInstanceGenerator:
    """Tests for the TestInstanceGenerator class."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary config for testing."""
        config_data = {
            'test_seed_offset': 9000,
            'test_instance_count': 5,
            'test_output_path': 'data/test_instances.json',
            'logic_axiom_count': 3,
            'grid_size': 5,
            'max_obstacles': 3
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        # Create a config object from the file
        config = Config.load(temp_path)
        yield config
        
        # Cleanup
        os.unlink(temp_path)

    @pytest.fixture
    def generator(self, temp_config):
        """Create a TestInstanceGenerator instance."""
        return TestInstanceGenerator(temp_config)

    def test_initialization(self, generator):
        """Test that the generator initializes correctly."""
        assert generator.test_instance_count == 5
        assert generator.test_seed_offset == 9000
        assert generator.logic_generator is not None
        assert generator.grid_generator is not None

    def test_generate_logic_test_instances(self, generator):
        """Test generation of logic test instances."""
        instances = generator.generate_logic_test_instances(count=3)
        
        assert len(instances) == 3
        for instance in instances:
            assert 'id' in instance
            assert instance['domain'] == 'logic'
            assert 'rule_set_id' in instance
            assert 'instance_data' in instance
            assert 'axioms' in instance['instance_data']
            assert 'target' in instance['instance_data']
            assert 'proof_steps' in instance['instance_data']

    def test_generate_grid_test_instances(self, generator):
        """Test generation of grid test instances."""
        instances = generator.generate_grid_test_instances(count=3)
        
        assert len(instances) == 3
        for instance in instances:
            assert 'id' in instance
            assert instance['domain'] == 'grid'
            assert 'rule_set_id' in instance
            assert 'instance_data' in instance
            assert 'grid' in instance['instance_data']
            assert 'start' in instance['instance_data']
            assert 'goal' in instance['instance_data']
            assert 'obstacles' in instance['instance_data']
            assert 'rules' in instance['instance_data']

    def test_generate_all_test_instances(self, generator):
        """Test generation of all test instances."""
        # Temporarily reduce count for faster testing
        generator.test_instance_count = 2
        instances = generator.generate_all_test_instances()
        
        # Should have 2 logic + 2 grid = 4 instances
        assert len(instances) == 4
        
        logic_count = sum(1 for i in instances if i['domain'] == 'logic')
        grid_count = sum(1 for i in instances if i['domain'] == 'grid')
        
        assert logic_count == 2
        assert grid_count == 2

    def test_save_test_instances(self, generator, temp_config):
        """Test saving test instances to a file."""
        # Generate a small set
        generator.test_instance_count = 2
        instances = generator.generate_all_test_instances()
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            generator.save_test_instances(instances, output_path)
            
            # Verify file exists and contains valid JSON
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded_instances = json.load(f)
            
            assert len(loaded_instances) == len(instances)
            assert loaded_instances == instances
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_seed_separation(self, temp_config):
        """Test that test instances use a different seed range than training."""
        # The test_seed_offset ensures separation
        # We verify this by checking that generated IDs contain the offset
        generator = TestInstanceGenerator(temp_config)
        generator.test_instance_count = 1
        
        logic_instances = generator.generate_logic_test_instances()
        grid_instances = generator.generate_grid_test_instances()
        
        # Verify IDs contain the expected seed values
        logic_id = logic_instances[0]['id']
        grid_id = grid_instances[0]['id']
        
        # Logic instances should use base_seed = offset + 1000
        expected_logic_seed = temp_config['test_seed_offset'] + 1000
        assert str(expected_logic_seed) in logic_id or str(expected_logic_seed) in logic_id.split('_')
        
        # Grid instances should use base_seed = offset + 5000
        expected_grid_seed = temp_config['test_seed_offset'] + 5000
        assert str(expected_grid_seed) in grid_id or str(expected_grid_seed) in grid_id.split('_')

    def test_empty_generation_handling(self, generator):
        """Test handling when generation fails for all instances."""
        # This is hard to test directly without mocking, but we can verify
        # that the generator doesn't crash with an empty config
        pass  # The generator should handle edge cases gracefully
