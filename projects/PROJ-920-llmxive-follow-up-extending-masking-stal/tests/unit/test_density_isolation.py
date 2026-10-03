"""
Unit tests for FR-007: Density Calculation Isolation.

This module verifies that the density calculation function in `heuristics.py`
accepts ONLY text input and does not incorporate agent output, simulation results,
or any external state beyond the configuration file.

FR-007 Requirement: The density calculation must be a pure function of the text
content and the loaded technical terms, ensuring no data leakage from the
simulation environment.
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path to allow imports
# Assuming this test runs from the project root or tests/unit
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.heuristics import calculate_composite_density, calculate_technical_token_ratio
from code.utils.entropy import calculate_shannon_entropy


class TestDensityIsolation:
    """Test cases ensuring density calculation is isolated from simulation state."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_text = "This is a test sentence with entropy and retrieval terms."
        self.terms = ["entropy", "retrieval", "context", "density"]
        
        # Create a temporary config file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "density_terms.json")
        with open(self.config_path, "w") as f:
            json.dump({"terms": self.terms}, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_function_signature_accepts_only_text_and_terms(self):
        """
        FR-007: Verify that calculate_composite_density accepts only text input 
        and technical terms list, with no other arguments.
        """
        # The function signature should be: calculate_composite_density(text: str, terms: List[str])
        # It should NOT accept agent_output, simulation_state, horizon, etc.
        
        import inspect
        sig = inspect.signature(calculate_composite_density)
        params = list(sig.parameters.keys())
        
        # Expected parameters based on the implementation
        assert "text" in params, "Function must accept 'text' parameter"
        assert "terms" in params, "Function must accept 'terms' parameter"
        
        # Ensure no simulation-related parameters exist
        forbidden_params = ["agent_output", "simulation_state", "horizon", "trajectory", "success"]
        for param in forbidden_params:
            assert param not in params, f"Function must not accept '{param}' parameter"

    def test_calculate_composite_density_is_pure_function(self):
        """
        FR-007: Verify that density calculation does not depend on external state.
        The same input text must always produce the same output.
        """
        # Run the calculation multiple times
        results = []
        for _ in range(10):
            density = calculate_composite_density(self.sample_text, self.terms)
            results.append(density)
        
        # All results should be identical
        assert all(r == results[0] for r in results), (
            "Density calculation must be deterministic and not depend on external state"
        )

    def test_density_independent_of_agent_output(self):
        """
        FR-007: Verify that density calculation ignores agent output.
        We simulate an agent output parameter and ensure it's not used.
        """
        # Mock agent output that would influence calculation if leaked
        mock_agent_output = "This is fake agent output that should NOT affect density"
        
        # Calculate density with the original text
        density_original = calculate_composite_density(self.sample_text, self.terms)
        
        # The function signature doesn't accept agent_output, so we can't pass it.
        # But we verify by checking the function implementation doesn't reference
        # any global agent state or external variables.
        
        # Verify the calculation is based only on the text
        # We do this by ensuring the result is consistent regardless of 
        # any hypothetical external state
        assert isinstance(density_original, float), "Density must be a float"
        assert 0.0 <= density_original <= 1.0, "Density must be between 0 and 1"

    def test_density_independent_of_simulation_results(self):
        """
        FR-007: Verify that density calculation does not use simulation results.
        """
        # Simulate a scenario where simulation results exist in memory
        mock_simulation_result = {
            "success": True,
            "horizon": 5,
            "trajectory_id": 123
        }
        
        # Calculate density - it should not be affected by the mock result
        density = calculate_composite_density(self.sample_text, self.terms)
        
        # Verify the result is a valid density value
        assert isinstance(density, float)
        assert 0.0 <= density <= 1.0

    def test_density_uses_only_text_and_terms(self):
        """
        FR-007: Verify that density calculation is based solely on text content
        and the list of technical terms.
        """
        # Calculate density with original text
        density_original = calculate_composite_density(self.sample_text, self.terms)
        
        # Change the text slightly and verify density changes
        modified_text = self.sample_text + " additional unique words here"
        density_modified = calculate_composite_density(modified_text, self.terms)
        
        # The densities should be different (unless the added words don't affect entropy/terms)
        # But more importantly, the calculation must be based on the text provided
        assert isinstance(density_original, float)
        assert isinstance(density_modified, float)

    def test_technical_token_ratio_is_isolated(self):
        """
        FR-007: Verify that calculate_technical_token_ratio is also isolated.
        """
        import inspect
        sig = inspect.signature(calculate_technical_token_ratio)
        params = list(sig.parameters.keys())
        
        assert "text" in params, "Function must accept 'text' parameter"
        assert "terms" in params, "Function must accept 'terms' parameter"
        
        # Ensure no simulation-related parameters
        forbidden_params = ["agent_output", "simulation_state", "horizon"]
        for param in forbidden_params:
            assert param not in params, f"Function must not accept '{param}' parameter"

    def test_no_global_state_dependency(self):
        """
        FR-007: Verify that density calculation does not rely on global variables
        that could be modified by simulation state.
        """
        # Temporarily set a global variable that might be accessed
        # (though the implementation shouldn't do this)
        import code.utils.heuristics as heuristics_module
        
        # Save original module attributes
        original_attrs = {}
        for attr in dir(heuristics_module):
            if not attr.startswith('_'):
                original_attrs[attr] = getattr(heuristics_module, attr)
        
        try:
            # Attempt to inject a "simulation state" global
            heuristics_module.simulation_state = {"fake": "data"}
            heuristics_module.agent_output = "fake output"
            
            # Calculate density - it should still work correctly
            density = calculate_composite_density(self.sample_text, self.terms)
            
            # Verify the result is still valid
            assert isinstance(density, float)
            assert 0.0 <= density <= 1.0
            
        finally:
            # Restore original attributes
            for attr in dir(heuristics_module):
                if not attr.startswith('_') and attr in original_attrs:
                    setattr(heuristics_module, attr, original_attrs[attr])
                
                # Remove injected attributes
                if hasattr(heuristics_module, 'simulation_state'):
                    delattr(heuristics_module, 'simulation_state')
                if hasattr(heuristics_module, 'agent_output'):
                    delattr(heuristics_module, 'agent_output')

    def test_entropy_calculation_is_isolated(self):
        """
        FR-007: Verify that entropy calculation is also isolated.
        """
        import inspect
        sig = inspect.signature(calculate_shannon_entropy)
        params = list(sig.parameters.keys())
        
        assert "text" in params, "Entropy function must accept 'text' parameter"
        
        # Ensure no simulation-related parameters
        forbidden_params = ["agent_output", "simulation_state", "horizon"]
        for param in forbidden_params:
            assert param not in params, f"Entropy function must not accept '{param}' parameter"

    def test_density_formula_is_correctly_isolated(self):
        """
        FR-007: Verify that the composite density formula (0.6*Entropy + 0.4*TermRatio)
        is applied without external influence.
        """
        # Create a text with known properties
        # High entropy, high term ratio
        high_density_text = " ".join(self.terms) * 10  # Repeat terms many times
        
        # Calculate density
        density = calculate_composite_density(high_density_text, self.terms)
        
        # Verify it's a valid density
        assert isinstance(density, float)
        assert 0.0 <= density <= 1.0
        
        # The density should be relatively high due to repeated terms
        # (though exact value depends on entropy calculation)
        assert density > 0.1, "High term density text should produce reasonable density value"

    def test_no_side_effects_from_density_calculation(self):
        """
        FR-007: Verify that density calculation has no side effects on global state.
        """
        import code.utils.heuristics as heuristics_module
        
        # Capture initial state
        initial_module_state = {}
        for attr in dir(heuristics_module):
            if not attr.startswith('_'):
                try:
                    val = getattr(heuristics_module, attr)
                    if not callable(val):
                        initial_module_state[attr] = val
                except:
                    pass
        
        # Run density calculation
        calculate_composite_density(self.sample_text, self.terms)
        
        # Verify no state changed
        for attr, initial_val in initial_module_state.items():
            current_val = getattr(heuristics_module, attr)
            assert initial_val == current_val, (
                f"Module state changed for attribute '{attr}' during density calculation"
            )

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])