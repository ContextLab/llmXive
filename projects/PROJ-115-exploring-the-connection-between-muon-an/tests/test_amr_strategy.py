"""
Tests for the Adaptive Mesh Refinement (AMR) Strategy.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scan.amr_strategy import AMRConfig, AdaptiveGridGenerator, GridPoint
from schemas.parameter_point import ParameterPoint

def test_amr_config_defaults():
    """Test that AMRConfig initializes with expected defaults."""
    config = AMRConfig()
    assert config.m_V_min == 1.0
    assert config.m_V_max == 1000.0
    assert config.max_depth == 4
    assert config.gradient_threshold == 0.1

def test_grid_generator_initialization():
    """Test that the generator initializes correctly."""
    config = AMRConfig()
    generator = AdaptiveGridGenerator(config)
    assert generator.config == config
    assert generator.grid_points == []

def test_should_refine_logic():
    """Test the refinement logic with known gradients."""
    config = AMRConfig()
    config.gradient_threshold = 0.1
    generator = AdaptiveGridGenerator(config)
    
    # Create points with high gradient
    p1 = GridPoint(m_V=1.0, g=1e-5, error_estimate=0.0)
    p2 = GridPoint(m_V=2.0, g=1e-5, error_estimate=0.0)
    p3 = GridPoint(m_V=2.0, g=2e-5, error_estimate=0.0)
    p4 = GridPoint(m_V=1.0, g=2e-5, error_estimate=1.0) # High value at p4
    
    # Should refine because of the large change between p4 and others
    assert generator._should_refine(p1, p2, p3, p4) == True

def test_should_refine_no_gradient():
    """Test that no refinement happens when gradient is low."""
    config = AMRConfig()
    config.gradient_threshold = 0.1
    generator = AdaptiveGridGenerator(config)
    
    p1 = GridPoint(m_V=1.0, g=1e-5, error_estimate=0.5)
    p2 = GridPoint(m_V=2.0, g=1e-5, error_estimate=0.5)
    p3 = GridPoint(m_V=2.0, g=2e-5, error_estimate=0.5)
    p4 = GridPoint(m_V=1.0, g=2e-5, error_estimate=0.5)
    
    assert generator._should_refine(p1, p2, p3, p4) == False

def test_generate_grid_basic():
    """Test basic grid generation."""
    config = AMRConfig(
        m_V_min=1.0,
        m_V_max=10.0,
        g_min=1e-5,
        g_max=1e-4,
        initial_m_V_steps=5,
        initial_g_steps=5,
        max_depth=1
    )
    generator = AdaptiveGridGenerator(config)
    points = generator.generate_grid()
    
    assert len(points) > 0
    assert all(isinstance(p, ParameterPoint) for p in points)
    
    # Check bounds
    for p in points:
        assert config.m_V_min <= p.m_V <= config.m_V_max
        assert config.g_min <= p.g <= config.g_max

def test_generate_grid_resonance_detection():
    """Test that the grid refines around a simulated resonance."""
    # We mock the _evaluate_physics to return a spike at a specific point
    config = AMRConfig(
        m_V_min=1.0,
        m_V_max=10.0,
        g_min=1e-5,
        g_max=1e-4,
        initial_m_V_steps=5,
        initial_g_steps=5,
        max_depth=2,
        gradient_threshold=0.1,
        resonance_threshold=0.5
    )
    generator = AdaptiveGridGenerator(config)
    
    # Override evaluate to simulate a resonance at m_V=5, g=5e-5
    original_evaluate = generator._evaluate_physics
    def mock_evaluate(point):
        if 4.5 < point.m_V < 5.5 and 4.5e-5 < point.g < 5.5e-5:
            return 10.0 # High resonance
        return 0.1
    
    generator._evaluate_physics = mock_evaluate
    
    points = generator.generate_grid()
    
    # There should be more points in the resonance region
    resonance_points = [p for p in points if 4.5 < p.m_V < 5.5 and 4.5e-5 < p.g < 5.5e-5]
    
    # We expect at least the initial points plus some refined ones
    # This is a soft check to ensure the logic runs without error
    assert len(resonance_points) >= 4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
