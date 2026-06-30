"""
Contract tests for visualization module.

This test suite verifies that the required plotting functions exist
and are importable from the code.viz.plots module, as required by
User Story 2 (Diagnostic Visualisations).
"""

import pytest

# Verify the module exists and can be imported
from code.viz import plots

# Verify the required functions exist in the module namespace
def test_plot_functions_exist():
    """
    Contract test: Ensure all required plotting functions exist.
    
    Per US2 specification, the following functions must be present
    in code/viz/plots.py:
    - plot_flexibility_vs_creativity
    - plot_residuals
    """
    
    # Check for the primary scatter plot function
    assert hasattr(plots, 'plot_flexibility_vs_creativity'), \
        "Missing required function: plot_flexibility_vs_creativity"
    
    # Check that it is callable
    assert callable(plots.plot_flexibility_vs_creativity), \
        "plot_flexibility_vs_creativity must be callable"
    
    # Check for the residual diagnostic plot function
    assert hasattr(plots, 'plot_residuals'), \
        "Missing required function: plot_residuals"
    
    # Check that it is callable
    assert callable(plots.plot_residuals), \
        "plot_residuals must be callable"

def test_plot_function_signatures():
    """
    Contract test: Verify basic function signatures exist.
    
    We don't execute the functions here (that would require real data),
    but we verify they accept the expected argument types via introspection.
    """
    import inspect
    
    # Verify plot_flexibility_vs_creativity signature
    sig = inspect.signature(plots.plot_flexibility_vs_creativity)
    params = list(sig.parameters.keys())
    # Expected: flexibility, creativity, output_path
    assert 'flexibility' in params, "Missing 'flexibility' parameter"
    assert 'creativity' in params, "Missing 'creativity' parameter"
    assert 'output_path' in params, "Missing 'output_path' parameter"
    
    # Verify plot_residuals signature
    sig = inspect.signature(plots.plot_residuals)
    params = list(sig.parameters.keys())
    # Expected: model, residuals_path, qq_path
    assert 'model' in params, "Missing 'model' parameter"
    assert 'residuals_path' in params, "Missing 'residuals_path' parameter"
    assert 'qq_path' in params, "Missing 'qq_path' parameter"