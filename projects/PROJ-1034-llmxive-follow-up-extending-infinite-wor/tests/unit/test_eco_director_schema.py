import pytest
import tempfile
import os
import yaml
import numpy as np
from src.sim.eco_director import validate_config, load_config

class TestEcoDirectorSchemaValidation:
    """
    Unit tests for parameter schema validation in src/sim/eco_director.py.
    These tests verify that the validate_config function correctly enforces
    the schema constraints required by the Eco-Director simulation.
    """

    def _create_temp_config(self, data: dict) -> str:
        """Helper to create a temporary YAML config file."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        try:
            with os.fdopen(fd, 'w') as f:
                yaml.dump(data, f)
            return path
        except Exception:
            os.close(fd)
            raise

    def test_validate_config_valid_full_schema(self):
        """Test that a valid, complete configuration passes validation."""
        config_data = {
            "simulation": {
                "steps": 1000,
                "seed": 42,
                "population_size": 100,
                "mutation_rate": 0.05,
                "crossover_rate": 0.8,
                "grid_size": [50, 50],
                "max_memory_mb": 2048,
                "time_limit_seconds": 3600
            },
            "metrics": {
                "track_coherence": True,
                "track_diversity": True,
                "track_physics_violations": True
            },
            "physics_oracle": {
                "enabled": True,
                "tolerance_energy": 1e-6,
                "tolerance_mass": 1e-6
            }
        }
        assert validate_config(config_data) is True

    def test_validate_config_missing_required_section(self):
        """Test validation fails if a required top-level section is missing."""
        config_data = {
            "simulation": {
                "steps": 1000,
                "seed": 42
            }
        }
        # Missing 'metrics' and 'physics_oracle' sections
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_data)
        assert "required" in str(exc_info.value).lower()

    def test_validate_config_invalid_step_type(self):
        """Test validation fails if steps is not an integer."""
        config_data = {
            "simulation": {
                "steps": "one_thousand",  # Invalid type
                "seed": 42,
                "population_size": 100,
                "mutation_rate": 0.05,
                "crossover_rate": 0.8,
                "grid_size": [50, 50],
                "max_memory_mb": 2048,
                "time_limit_seconds": 3600
            },
            "metrics": {
                "track_coherence": True,
                "track_diversity": True,
                "track_physics_violations": True
            },
            "physics_oracle": {
                "enabled": True,
                "tolerance_energy": 1e-6,
                "tolerance_mass": 1e-6
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_data)
        assert "steps" in str(exc_info.value)

    def test_validate_config_negative_steps(self):
        """Test validation fails if steps is negative."""
        config_data = {
            "simulation": {
                "steps": -100,
                "seed": 42,
                "population_size": 100,
                "mutation_rate": 0.05,
                "crossover_rate": 0.8,
                "grid_size": [50, 50],
                "max_memory_mb": 2048,
                "time_limit_seconds": 3600
            },
            "metrics": {
                "track_coherence": True,
                "track_diversity": True,
                "track_physics_violations": True
            },
            "physics_oracle": {
                "enabled": True,
                "tolerance_energy": 1e-6,
                "tolerance_mass": 1e-6
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_data)
        assert "positive" in str(exc_info.value).lower()

    def test_validate_config_invalid_rate_range(self):
        """Test validation fails if mutation_rate is outside [0, 1]."""
        config_data = {
            "simulation": {
                "steps": 1000,
                "seed": 42,
                "population_size": 100,
                "mutation_rate": 1.5,  # Invalid: > 1.0
                "crossover_rate": 0.8,
                "grid_size": [50, 50],
                "max_memory_mb": 2048,
                "time_limit_seconds": 3600
            },
            "metrics": {
                "track_coherence": True,
                "track_diversity": True,
                "track_physics_violations": True
            },
            "physics_oracle": {
                "enabled": True,
                "tolerance_energy": 1e-6,
                "tolerance_mass": 1e-6
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_data)
        assert "mutation_rate" in str(exc_info.value)

    def test_validate_config_invalid_grid_dimensions(self):
        """Test validation fails if grid_size has wrong number of dimensions."""
        config_data = {
            "simulation": {
                "steps": 1000,
                "seed": 42,
                "population_size": 100,
                "mutation_rate": 0.05,
                "crossover_rate": 0.8,
                "grid_size": [50],  # Invalid: 1D instead of 2D
                "max_memory_mb": 2048,
                "time_limit_seconds": 3600
            },
            "metrics": {
                "track_coherence": True,
                "track_diversity": True,
                "track_physics_violations": True
            },
            "physics_oracle": {
                "enabled": True,
                "tolerance_energy": 1e-6,
                "tolerance_mass": 1e-6
            }
        }
        with pytest.raises(ValueError) as exc_info:
            validate_config(config_data)
        assert "grid_size" in str(exc_info.value)

    def test_validate_config_load_and_validate_integration(self):
        """Test that load_config correctly validates a real file."""
        config_data = {
            "simulation": {
                "steps": 500,
                "seed": 123,
                "population_size": 50,
                "mutation_rate": 0.02,
                "crossover_rate": 0.9,
                "grid_size": [20, 20],
                "max_memory_mb": 1024,
                "time_limit_seconds": 1800
            },
            "metrics": {
                "track_coherence": True,
                "track_diversity": True,
                "track_physics_violations": True
            },
            "physics_oracle": {
                "enabled": True,
                "tolerance_energy": 1e-5,
                "tolerance_mass": 1e-5
            }
        }
        config_path = self._create_temp_config(config_data)
        try:
            loaded_config = load_config(config_path)
            assert loaded_config == config_data
            assert validate_config(loaded_config) is True
        finally:
            os.unlink(config_path)

    def test_validate_config_load_invalid_file(self):
        """Test that load_config raises error for invalid schema in file."""
        config_data = {
            "simulation": {
                "steps": "invalid",
                "seed": 123
            }
        }
        config_path = self._create_temp_config(config_data)
        try:
            with pytest.raises(ValueError):
                load_config(config_path)
        finally:
            os.unlink(config_path)