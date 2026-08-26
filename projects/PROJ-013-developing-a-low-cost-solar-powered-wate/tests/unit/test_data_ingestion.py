import pytest
from code.data_ingestion import calculate_cost, MaterialProfile, GeometryConfig

def test_calculate_cost_signature():
    """Verify calculate_cost exists with correct signature."""
    materials = [
        MaterialProfile("test", "Test", 1.0, 1.0, 1.0, 1.0)
    ]
    geometry = GeometryConfig("g1", "flat", 0.0, 1.0, 0.01)
    prices = {"test": 10.0}
    
    result = calculate_cost(materials, geometry, prices)
    assert isinstance(result, float)
    assert result > 0.0

def test_calculate_cost_zero_price_exclusion():
    """Verify cost calculation excludes materials with no price."""
    materials = [
        MaterialProfile("a", "A", 1.0, 1.0, 1.0, 1.0),
        MaterialProfile("b", "B", 1.0, 1.0, 1.0, 1.0)
    ]
    geometry = GeometryConfig("g1", "flat", 0.0, 1.0, 0.01)
    prices = {"a": 10.0} # "b" is missing
    
    result = calculate_cost(materials, geometry, prices)
    # Should only calculate for 'a'
    expected = (1.0 * 1.0 * 0.01 * 1.0) * 10.0
    assert result == expected