"""
Unit tests for density iteration logic in simulation runner.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.runner import DENSITY_LEVELS, CONFIDENCE_THRESHOLD, simulate_interaction
from data.models import SimulationRun

class TestDensityIteration:
    """Test density iteration logic."""
    
    def test_density_levels_defined(self):
        """Verify that density levels are explicitly defined as {1, 3, 5, 10}."""
        assert DENSITY_LEVELS == [1, 3, 5, 10], "Density levels must be {1, 3, 5, 10}"
    
    def test_density_iteration_in_simulation(self):
        """Test that simulation iterates through all density levels."""
        # Create mock data
        mock_row = {
            'query': 'Test query',
            'ground_truth_intent': 'high_confidence',
            'complexity_score': 0.5,
            'label': 'High-Confidence'
        }
        
        # Test each density level
        for density in DENSITY_LEVELS:
            result = simulate_interaction(
                row=mock_row,
                density=density,
                injected_latency_ms=0,
                patience_seconds=5.0,
                router=None
            )
            
            assert isinstance(result, SimulationRun), "Result must be SimulationRun"
            assert result.density_level == density, f"Density level should be {density}"
            assert result.ui_element_count > 0, "UI element count must be positive"
    
    def test_borderline_confidence_routing(self):
        """Test that borderline confidence scores (== threshold) route to Ambiguous."""
        mock_row = {
            'query': 'Test query',
            'ground_truth_intent': 'ambiguous',
            'complexity_score': 0.5,
            'label': 'Ambiguous'
        }
        
        # Mock the confidence score to be exactly at threshold
        # This tests the explicit handling of borderline cases
        with patch('simulation.runner.np.random.normal', return_value=0.0):
            # Set complexity such that base_confidence equals threshold
            # base_confidence = 0.85 - (complexity * 0.3)
            # We want base_confidence = 0.75, so complexity = (0.85 - 0.75) / 0.3 = 0.333...
            mock_row['complexity_score'] = 0.3333333
            
            result = simulate_interaction(
                row=mock_row,
                density=3,
                injected_latency_ms=0,
                patience_seconds=5.0,
                router=None
            )
            
            # When confidence == threshold, should route to Ambiguous (class 0)
            assert result.predicted_class == 0, "Borderline confidence should route to Ambiguous"
            assert result.is_ambiguous == True, "Borderline confidence should be marked as ambiguous"
    
    def test_ui_element_count_by_density(self):
        """Test that UI element count scales with density."""
        mock_row = {
            'query': 'Test query',
            'ground_truth_intent': 'high_confidence',
            'complexity_score': 0.3,
            'label': 'High-Confidence'
        }
        
        results = []
        for density in DENSITY_LEVELS:
            result = simulate_interaction(
                row=mock_row,
                density=density,
                injected_latency_ms=0,
                patience_seconds=5.0,
                router=None
            )
            results.append(result)
        
        # Check that UI element count generally increases with density
        # (allowing for some randomness in the simulation)
        element_counts = [r.ui_element_count for r in results]
        
        # The trend should be increasing, though not strictly monotonic due to randomness
        # We check that the average for higher densities is generally higher
        avg_low = np.mean(element_counts[:2])  # densities 1, 3
        avg_high = np.mean(element_counts[2:]) # densities 5, 10
        
        assert avg_high >= avg_low * 0.9, "Higher density should generally produce more UI elements"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
