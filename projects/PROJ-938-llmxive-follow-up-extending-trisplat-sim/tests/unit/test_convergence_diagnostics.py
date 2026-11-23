import pytest
import numpy as np
from utils.stats import calculate_convergence_rate

def test_convergence_rate_calculation():
    """Test that convergence rate is calculated correctly."""
    metrics = [
        {"iteration": 0, "chamfer_distance": 1.0},
        {"iteration": 10, "chamfer_distance": 0.5},
        {"iteration": 20, "chamfer_distance": 0.25},
        {"iteration": 30, "chamfer_distance": 0.125}
    ]
    
    result = calculate_convergence_rate(metrics)
    
    assert result["initial_error"] == 1.0
    assert result["final_error"] == 0.125
    assert result["convergence_rate"] > 0
    assert result["is_converged"] == True
    assert "convergence_time" in result

def test_convergence_rate_insufficient_data():
    """Test behavior with insufficient data points."""
    metrics = [{"iteration": 0, "chamfer_distance": 1.0}]
    
    result = calculate_convergence_rate(metrics)
    
    assert result["is_converged"] == False
    assert "Insufficient data points" in result["diagnostics"]

def test_convergence_rate_non_converging():
    """Test behavior when model does not converge."""
    metrics = [
        {"iteration": 0, "chamfer_distance": 1.0},
        {"iteration": 10, "chamfer_distance": 1.1},
        {"iteration": 20, "chamfer_distance": 1.2}
    ]
    
    result = calculate_convergence_rate(metrics)
    
    assert result["convergence_rate"] < 0
    assert result["is_converged"] == False

def test_convergence_rate_stabilization_detection():
    """Test that stabilization point is detected correctly."""
    metrics = [
        {"iteration": 0, "chamfer_distance": 1.0},
        {"iteration": 10, "chamfer_distance": 0.5},
        {"iteration": 20, "chamfer_distance": 0.4999},  # Stabilized
        {"iteration": 30, "chamfer_distance": 0.4998}
    ]
    
    result = calculate_convergence_rate(metrics)
    
    # Should detect stabilization around iteration 20
    assert result["convergence_time"] < 30

def test_geometry_only_model_integration():
    """Test that geometry_only model returns convergence diagnostics."""
    from models.geometry_only import create_geometry_only_model, run_geometry_optimization
    import torch
    
    model = create_geometry_only_model(num_vertices=100, num_faces=200)
    
    # Create dummy views
    views = [torch.randn(1, 32, 32, 3) for _ in range(2)]
    intrinsics = [torch.eye(3) for _ in range(2)]
    
    result = run_geometry_optimization(model, views, intrinsics)
    
    assert "convergence_diagnostics" in result
    assert "initial_error" in result["convergence_diagnostics"]
    assert "final_error" in result["convergence_diagnostics"]
    assert "convergence_rate" in result["convergence_diagnostics"]
    assert "is_converged" in result["convergence_diagnostics"]