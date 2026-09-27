import pytest
from typing import List
from code.data_ingestion import MaterialProfile, GeometryConfig, calculate_cost

def test_calculate_cost_signature():
    """Verify calculate_cost exists with correct signature."""
    # This is a smoke test to ensure the function exists and is callable
    assert callable(calculate_cost)

def test_calculate_cost_returns_positive():
    """Verify calculate_cost returns a float > 0 for valid inputs."""
    materials = [
        MaterialProfile(
            material_id="test_mat",
            name="Test Material",
            thermal_conductivity=100.0,
            emissivity=0.5,
            specific_heat=500.0,
            density=2000.0,
            unit="W/m·K",
            source="test"
        )
    ]
    geometry = GeometryConfig(
        geometry_id="test_geo",
        inclination_angle=45.0,
        surface_area=2.0,
        thickness=0.01
    )
    
    cost = calculate_cost(materials, geometry)
    
    assert isinstance(cost, float)
    assert cost > 0

def test_calculate_cost_empty_materials():
    """Verify calculate_cost returns 0 for empty materials list."""
    materials = []
    geometry = GeometryConfig(
        geometry_id="test_geo",
        inclination_angle=45.0,
        surface_area=2.0,
        thickness=0.01
    )
    
    cost = calculate_cost(materials, geometry)
    
    assert cost == 0.0
