"""
Unit test for parameter grid generation (T018).

This module tests the ParameterGrid class from src.data_models to ensure
it correctly initializes parameters, descriptions, and generates Cartesian
product configurations for simulation sweeps.
"""
import pytest
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_models import ParameterGrid

class TestParameterGridCreation:
    """Tests for basic ParameterGrid instantiation and attribute access."""

    def test_parameter_grid_creation(self):
        """Test that a grid is created with correct parameters."""
        grid = ParameterGrid(
            name="test_grid",
            parameters={"alpha": [0.1, 0.5, 1.0], "beta": [1, 2]}
        )
        assert grid.name == "test_grid"
        assert "alpha" in grid.parameters
        assert len(grid.parameters["alpha"]) == 3
        assert len(grid.parameters["beta"]) == 2

    def test_parameter_grid_description(self):
        """Test that description is stored correctly."""
        grid = ParameterGrid(
            name="desc_grid",
            parameters={"x": [1]},
            description="Test description for T018"
        )
        assert grid.description == "Test description for T018"

    def test_parameter_grid_defaults(self):
        """Test that optional fields default to None or empty."""
        grid = ParameterGrid(name="minimal", parameters={})
        assert grid.description is None
        assert grid.tags == []

class TestParameterGridGeneration:
    """Tests for the generate_configurations method."""

    def test_generate_single_param(self):
        """Test generation with a single parameter."""
        grid = ParameterGrid(
            name="single",
            parameters={"lr": [0.01, 0.1]}
        )
        configs = list(grid.generate_configurations())
        assert len(configs) == 2
        assert {"lr": 0.01} in configs
        assert {"lr": 0.1} in configs

    def test_generate_multi_param_cartesian(self):
        """Test Cartesian product generation for multiple parameters."""
        grid = ParameterGrid(
            name="multi",
            parameters={"alpha": [1, 2], "beta": [10, 20]}
        )
        configs = list(grid.generate_configurations())
        
        # Expect 2 * 2 = 4 configurations
        assert len(configs) == 4
        
        expected_combinations = [
            {"alpha": 1, "beta": 10},
            {"alpha": 1, "beta": 20},
            {"alpha": 2, "beta": 10},
            {"alpha": 2, "beta": 20}
        ]
        
        for expected in expected_combinations:
            assert expected in configs

    def test_generate_empty_params(self):
        """Test generation with no parameters returns one empty config."""
        grid = ParameterGrid(name="empty", parameters={})
        configs = list(grid.generate_configurations())
        assert len(configs) == 1
        assert configs[0] == {}

class TestParameterGridValidation:
    """Tests for input validation within ParameterGrid."""

    def test_validate_non_list_values(self):
        """Test that non-list parameter values raise an error."""
        with pytest.raises(ValueError, match="Parameter values must be a list"):
            ParameterGrid(
                name="invalid",
                parameters={"bad_key": "not_a_list"}
            )

    def test_validate_empty_list(self):
        """Test that empty parameter lists raise an error."""
        with pytest.raises(ValueError, match="Parameter list cannot be empty"):
            ParameterGrid(
                name="empty_list",
                parameters={"empty_key": []}
            )

    def test_validate_name_required(self):
        """Test that a name is required."""
        with pytest.raises(ValueError, match="Name is required"):
            ParameterGrid(name="", parameters={"a": [1]})