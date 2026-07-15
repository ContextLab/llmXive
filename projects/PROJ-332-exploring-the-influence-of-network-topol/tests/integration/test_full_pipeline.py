"""
Integration test suite for the full pipeline (T039).
Covers all user stories: US1, US2, and US3.
"""
import os
import sys
import tempfile
import csv
import yaml
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generate_networks import generate_nanowire_network, calculate_average_degree
from thermal_solver import solve_kirchhoff_heat_flow, calculate_effective_conductivity
from regression_analysis import run_ols_regression, detect_percolation_threshold
from sensitivity_analysis import run_sensitivity_sweep
from update_state import update_state, calculate_sha256

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_us1_generate_network_and_solve(temp_output_dir):
    """
    US1 Integration: Generate a network, solve thermal conductivity,
    and verify the result is non-negative and finite.
    """
    # Generate a small network
    N = 50
    p = 0.1
    seed = 42
    graph = generate_nanowire_network(N, p, seed=seed)
    
    assert graph is not None
    assert len(graph.nodes()) == N
    
    # Calculate degree
    avg_degree = calculate_average_degree(graph)
    assert avg_degree > 0
    
    # Solve thermal conductivity
    # Mock material properties for testing
    material = "Si"
    d = 50e-9  # 50nm diameter
    l = 1e-6   # 1 micron length
    
    conductivity = calculate_effective_conductivity(
        graph, material, d, l, seed=seed
    )
    
    # Verify result is valid
    assert conductivity is not None
    assert conductivity >= 0
    assert not (conductivity != conductivity)  # Not NaN

def test_us2_regression_analysis(temp_output_dir):
    """
    US2 Integration: Run regression analysis on simulated data.
    """
    # Generate synthetic data for regression testing
    # In real scenario, this would come from simulation_results.csv
    data = {
        "avg_degree": [2.0, 3.0, 4.0, 5.0, 6.0],
        "conductivity": [50.0, 120.0, 180.0, 240.0, 300.0]
    }
    
    # Run regression
    results = run_ols_regression(data["avg_degree"], data["conductivity"])
    
    assert results is not None
    assert "exponent" in results
    assert "p_value" in results
    assert "r_squared" in results
    
    # Verify p-value is reasonable
    assert results["p_value"] < 1.0

def test_us3_sensitivity_analysis(temp_output_dir):
    """
    US3 Integration: Run sensitivity sweep and verify deviation report.
    """
    # Run sensitivity sweep with mock data
    base_conductivity = 150.0
    sweep_results = run_sensitivity_sweep(base_conductivity, factor_range=[0.8, 1.2], steps=5)
    
    assert sweep_results is not None
    assert "deviations" in sweep_results
    assert len(sweep_results["deviations"]) > 0
    
    # Verify deviations are calculated
    for deviation in sweep_results["deviations"]:
        assert "factor" in deviation
        assert "deviation_pct" in deviation

def test_full_pipeline_state_update(temp_output_dir):
    """
    Integration: Run a mini-pipeline and update state with result hash.
    """
    # 1. Generate network
    graph = generate_nanowire_network(30, 0.15, seed=123)
    
    # 2. Solve conductivity
    conductivity = calculate_effective_conductivity(graph, "Si", 50e-9, 1e-6, seed=123)
    
    # 3. Create a temporary results file
    results_file = temp_output_dir / "test_results.csv"
    with open(results_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "N", "p", "avg_degree", "conductivity", "percolation_flag", "scaling_factor"])
        writer.writerow([123, 30, 0.15, calculate_average_degree(graph), conductivity, 1, 1.0])
    
    # 4. Update state (using temp file path)
    state = update_state(
        artifact_name="test_results.csv",
        artifact_path=str(results_file),
        task_id="T039"
    )
    
    # 5. Verify state was updated
    assert "artifact_hashes" in state
    assert "test_results.csv" in state["artifact_hashes"]
    
    hash_info = state["artifact_hashes"]["test_results.csv"]
    assert "hash" in hash_info
    assert len(hash_info["hash"]) == 64  # SHA-256 length
    
    # Verify hash matches
    expected_hash = calculate_sha256(str(results_file))
    assert hash_info["hash"] == expected_hash

def test_percolation_threshold_detection():
    """
    Integration: Test percolation threshold detection logic.
    """
    # Simulate connectivity data
    connectivity_data = [
        {"avg_degree": 1.5, "connected_fraction": 0.3},
        {"avg_degree": 2.0, "connected_fraction": 0.5},
        {"avg_degree": 2.5, "connected_fraction": 0.7},
        {"avg_degree": 3.0, "connected_fraction": 0.85},
        {"avg_degree": 3.5, "connected_fraction": 0.95},
    ]
    
    threshold = detect_percolation_threshold(connectivity_data, threshold=0.8)
    
    assert threshold is not None
    assert threshold == 3.0  # First point where connected_fraction >= 0.8
