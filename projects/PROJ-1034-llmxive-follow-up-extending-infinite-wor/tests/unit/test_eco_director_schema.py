"""
Unit tests for parameter schema validation in src.sim.eco_director.

This module verifies that the EcoDirector class correctly validates
configuration parameters against its defined schema, ensuring type safety
and constraint adherence before simulation execution.
"""

import pytest
from src.sim.eco_director import EcoDirector
from src.data_models import SimulationConfig

class TestEcoDirectorSchemaValidation:
    """Test suite for parameter schema validation in EcoDirector."""

    def test_valid_config_initialization(self):
        """Test that a valid configuration initializes without error."""
        config = SimulationConfig(
            grid_size=100,
            neighborhood_radius=2,
            update_rule="majority",
            max_steps=1000,
            initial_density=0.5
        )
        director = EcoDirector(config=config)
        assert director is not None
        assert director.config.grid_size == 100

    def test_invalid_grid_size_type(self):
        """Test rejection of non-integer grid_size."""
        config_dict = {
            "grid_size": "invalid",
            "neighborhood_radius": 2,
            "update_rule": "majority",
            "max_steps": 1000,
            "initial_density": 0.5
        }
        with pytest.raises(ValueError):
            SimulationConfig(**config_dict)

    def test_invalid_grid_size_range(self):
        """Test rejection of grid_size outside valid range (1-10000)."""
        config = SimulationConfig(
            grid_size=0,  # Below minimum
            neighborhood_radius=2,
            update_rule="majority",
            max_steps=1000,
            initial_density=0.5
        )
        # The validation should catch this during config creation or director init
        # Depending on where validation is enforced, we test the constraint
        assert config.grid_size > 0  # This will fail if validation is in the model

    def test_invalid_neighborhood_radius(self):
        """Test rejection of invalid neighborhood_radius."""
        with pytest.raises(ValueError):
            SimulationConfig(
                grid_size=100,
                neighborhood_radius=-1,  # Must be positive
                update_rule="majority",
                max_steps=1000,
                initial_density=0.5
            )

    def test_invalid_update_rule(self):
        """Test rejection of unsupported update_rule."""
        with pytest.raises(ValueError):
            SimulationConfig(
                grid_size=100,
                neighborhood_radius=2,
                update_rule="non_existent_rule",
                max_steps=1000,
                initial_density=0.5
            )

    def test_invalid_max_steps_type(self):
        """Test rejection of non-integer max_steps."""
        with pytest.raises(ValueError):
            SimulationConfig(
                grid_size=100,
                neighborhood_radius=2,
                update_rule="majority",
                max_steps="fast",
                initial_density=0.5
            )

    def test_invalid_initial_density_range(self):
        """Test rejection of initial_density outside [0.0, 1.0]."""
        with pytest.raises(ValueError):
            SimulationConfig(
                grid_size=100,
                neighborhood_radius=2,
                update_rule="majority",
                max_steps=1000,
                initial_density=1.5  # > 1.0
            )

        with pytest.raises(ValueError):
            SimulationConfig(
                grid_size=100,
                neighborhood_radius=2,
                update_rule="majority",
                max_steps=1000,
                initial_density=-0.1  # < 0.0
            )

    def test_missing_required_field(self):
        """Test that missing required fields raise an error."""
        # SimulationConfig requires all fields, so missing one should fail
        with pytest.raises(TypeError):
            SimulationConfig(
                grid_size=100,
                # neighborhood_radius missing
                update_rule="majority",
                max_steps=1000,
                initial_density=0.5
            )

    def test_schema_enforcement_on_director_update(self):
        """Test that updating parameters on an existing director validates against schema."""
        config = SimulationConfig(
            grid_size=100,
            neighborhood_radius=2,
            update_rule="majority",
            max_steps=1000,
            initial_density=0.5
        )
        director = EcoDirector(config=config)

        # Attempt to update with invalid value
        with pytest.raises(ValueError):
            director.update_parameter("grid_size", "invalid")

        # Valid update should succeed
        director.update_parameter("max_steps", 2000)
        assert director.config.max_steps == 2000
    
    def test_boundary_values_acceptance(self):
        """Test that boundary values are accepted."""
        config = SimulationConfig(
            grid_size=1,  # Minimum
            neighborhood_radius=1,  # Minimum
            update_rule="majority",
            max_steps=10000000,  # Large but valid
            initial_density=0.0  # Minimum
        )
        director = EcoDirector(config=config)
        assert director is not None

        config_max = SimulationConfig(
            grid_size=10000,  # Maximum
            neighborhood_radius=50,  # Reasonable max for grid
            update_rule="majority",
            max_steps=10000000,
            initial_density=1.0  # Maximum
        )
        director_max = EcoDirector(config=config_max)
        assert director_max is not None