"""
Integration test suite for the full thermal conductivity simulation pipeline.
Covers all user stories:
- US1: Generate Topology-Specific Nanowire Networks
- US2: Quantify Scaling Between Topology and Conductivity
- US3: Perform Sensitivity & Robustness Checks
"""

import os
import sys
import csv
import tempfile
import shutil
import logging
from pathlib import Path

import pytest
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from config import SimulationConfig, load_config
from generate_networks import generate_nanowire_network, calculate_average_degree
from thermal_solver import calculate_effective_conductivity, solve_kirchhoff_heat_flow
from regression_analysis import run_ols_regression, detect_percolation_threshold
from sensitivity_analysis import run_sensitivity_sweep, calculate_deviation_report
from material_db import get_material_conductivity
from main import run_simulation, append_results_to_csv, load_existing_results

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config():
    """Create a minimal valid simulation config."""
    return SimulationConfig(
        N=50,
        p=0.15,
        d=50e-9,  # 50nm diameter
        l=1e-6,   # 1um length
        material="Si",
        seed=42,
        target_degree=4.0
    )

class TestUS1_NetworkGeneration:
    """Tests for User Story 1: Network Generation and Thermal Solving"""

    def test_network_generation_and_degree_accuracy(self, sample_config):
        """Verify graph generation produces correct average degree within tolerance."""
        graph = generate_nanowire_network(
            N=sample_config.N,
            p=sample_config.p,
            seed=sample_config.seed,
            target_degree=sample_config.target_degree
        )
        
        actual_degree = calculate_average_degree(graph)
        target = sample_config.target_degree
        
        # Check within ±5% tolerance
        tolerance = 0.05 * target
        assert abs(actual_degree - target) <= tolerance, \
            f"Degree {actual_degree:.2f} outside tolerance of {target:.2f} ± {tolerance:.2f}"

    def test_thermal_conductivity_computation(self, sample_config, temp_output_dir):
        """Verify effective conductivity is computed and is a real number."""
        graph = generate_nanowire_network(
            N=sample_config.N,
            p=sample_config.p,
            seed=sample_config.seed,
            target_degree=sample_config.target_degree
        )
        
        conductivity = calculate_effective_conductivity(
            graph,
            material=sample_config.material,
            diameter=sample_config.d,
            length=sample_config.l
        )
        
        assert isinstance(conductivity, (int, float, np.number)), \
            "Conductivity must be numeric"
        assert conductivity >= 0.0, "Conductivity must be non-negative"

    def test_disconnected_graph_handling(self, temp_output_dir):
        """Verify disconnected graphs return zero conductivity."""
        # Create a disconnected graph manually
        import networkx as nx
        graph = nx.Graph()
        graph.add_nodes_from([1, 2, 3, 4, 5])
        graph.add_edges_from([(1, 2), (2, 3)])  # Only one component
        graph.add_node(4)  # Isolated node
        graph.add_node(5)  # Isolated node
        
        conductivity = calculate_effective_conductivity(
            graph,
            material="Si",
            diameter=50e-9,
            length=1e-6
        )
        
        assert conductivity == 0.0, "Disconnected graph should return 0.0 conductivity"

class TestUS2_ScalingAnalysis:
    """Tests for User Story 2: Scaling Law Quantification"""

    def test_regression_outputs_format(self, temp_output_dir):
        """Verify regression analysis returns required statistical metrics."""
        # Generate sample data
        x_data = np.array([2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        y_data = np.array([1.2, 1.8, 2.5, 3.1, 3.8, 4.4, 5.1])
        
        results = run_ols_regression(x_data, y_data)
        
        assert "slope" in results, "Regression must include slope"
        assert "intercept" in results, "Regression must include intercept"
        assert "p_value" in results, "Regression must include p-value"
        assert "r_squared" in results, "Regression must include R-squared"
        assert "ci_lower" in results, "Regression must include CI lower bound"
        assert "ci_upper" in results, "Regression must include CI upper bound"
        
        # Verify numeric types
        assert isinstance(results["slope"], (int, float, np.number))
        assert isinstance(results["p_value"], (int, float, np.number))
        assert results["p_value"] >= 0.0 and results["p_value"] <= 1.0

    def test_percolation_threshold_detection(self, temp_output_dir):
        """Verify percolation threshold detection logic."""
        # Simulate connectivity data
        avg_degrees = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        connectivity_ratios = np.array([0.1, 0.3, 0.5, 0.75, 0.85, 0.95, 1.0])
        
        threshold = detect_percolation_threshold(avg_degrees, connectivity_ratios)
        
        assert threshold is not None, "Percolation threshold should be detected"
        assert threshold in avg_degrees, "Threshold should be one of the input degrees"
        # Verify it's the first degree where connectivity >= 80%
        expected_idx = np.where(connectivity_ratios >= 0.80)[0][0]
        expected_degree = avg_degrees[expected_idx]
        assert threshold == expected_degree, \
            f"Expected threshold {expected_degree}, got {threshold}"

    def test_csv_output_contains_regression_fields(self, temp_output_dir):
        """Verify CSV output includes regression analysis fields."""
        results_file = os.path.join(temp_output_dir, "test_results.csv")
        
        # Create sample result dict with regression data
        sample_result = {
            "seed": 42,
            "N": 50,
            "p": 0.15,
            "avg_degree": 4.5,
            "conductivity": 150.5,
            "percolation_flag": 1,
            "scaling_factor": 1.2,
            "regression_slope": 0.85,
            "regression_p_value": 0.03,
            "regression_r_squared": 0.92
        }
        
        append_results_to_csv([sample_result], results_file)
        
        # Verify file exists and contains expected columns
        assert os.path.exists(results_file), "Results CSV must be created"
        
        with open(results_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1, "Should have one result row"
        row = rows[0]
        
        assert "regression_slope" in row, "CSV must include regression_slope"
        assert "regression_p_value" in row, "CSV must include regression_p_value"
        assert "regression_r_squared" in row, "CSV must include regression_r_squared"

class TestUS3_SensitivityAnalysis:
    """Tests for User Story 3: Sensitivity and Robustness Checks"""

    def test_sensitivity_sweep_execution(self, sample_config, temp_output_dir):
        """Verify sensitivity sweep runs and produces results."""
        sensitivity_results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[40e-9, 50e-9, 60e-9],
            num_repeats=3
        )
        
        assert isinstance(sensitivity_results, dict), "Results must be a dict"
        assert "mean_conductivity" in sensitivity_results, "Must include mean conductivity"
        assert "std_conductivity" in sensitivity_results, "Must include std conductivity"
        assert "deviation_percent" in sensitivity_results, "Must include deviation percent"
        
        # Verify numeric values
        assert isinstance(sensitivity_results["mean_conductivity"], (int, float))
        assert isinstance(sensitivity_results["deviation_percent"], (int, float))

    def test_deviation_within_tolerance(self, sample_config, temp_output_dir):
        """Verify deviation calculations stay within ±10% for stable parameters."""
        # Run sweep with small variation
        sensitivity_results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="p",
            sweep_range=[0.14, 0.15, 0.16],
            num_repeats=3
        )
        
        deviation = sensitivity_results["deviation_percent"]
        assert abs(deviation) <= 10.0, \
            f"Deviation {deviation}% exceeds ±10% tolerance"

    def test_sensitivity_csv_integration(self, sample_config, temp_output_dir):
        """Verify sensitivity metrics are written to CSV."""
        results_file = os.path.join(temp_output_dir, "sensitivity_test.csv")
        
        # Create result with sensitivity data
        result = {
            "seed": 42,
            "N": 50,
            "p": 0.15,
            "avg_degree": 4.5,
            "conductivity": 150.5,
            "percolation_flag": 1,
            "scaling_factor": 1.2,
            "sensitivity_mean": 152.3,
            "sensitivity_std": 2.1,
            "sensitivity_deviation": 1.2
        }
        
        append_results_to_csv([result], results_file)
        
        assert os.path.exists(results_file), "CSV must be created"
        
        with open(results_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        row = rows[0]
        
        assert "sensitivity_mean" in row, "CSV must include sensitivity_mean"
        assert "sensitivity_std" in row, "CSV must include sensitivity_std"
        assert "sensitivity_deviation" in row, "CSV must include sensitivity_deviation"

class TestFullPipelineIntegration:
    """End-to-end integration test covering all user stories."""

    def test_full_pipeline_execution(self, sample_config, temp_output_dir):
        """Run complete pipeline: generation -> solving -> regression -> sensitivity."""
        # Setup paths
        results_file = os.path.join(temp_output_dir, "full_pipeline_results.csv")
        
        # Step 1: Generate network and compute conductivity (US1)
        graph = generate_nanowire_network(
            N=sample_config.N,
            p=sample_config.p,
            seed=sample_config.seed,
            target_degree=sample_config.target_degree
        )
        
        conductivity = calculate_effective_conductivity(
            graph,
            material=sample_config.material,
            diameter=sample_config.d,
            length=sample_config.l
        )
        
        avg_degree = calculate_average_degree(graph)
        
        # Step 2: Prepare data for regression (US2)
        # In real pipeline, this would aggregate multiple runs
        sample_regression_data = {
            "avg_degree": avg_degree,
            "conductivity": conductivity
        }
        
        # Step 3: Run sensitivity analysis (US3)
        sensitivity_results = run_sensitivity_sweep(
            base_config=sample_config,
            parameter="diameter",
            sweep_range=[sample_config.d * 0.9, sample_config.d, sample_config.d * 1.1],
            num_repeats=2
        )
        
        # Compile final result
        final_result = {
            "seed": sample_config.seed,
            "N": sample_config.N,
            "p": sample_config.p,
            "avg_degree": avg_degree,
            "conductivity": conductivity,
            "percolation_flag": 1 if len(list(nx.connected_components(graph))) == 1 else 0,
            "scaling_factor": sensitivity_results["mean_conductivity"] / conductivity if conductivity > 0 else 0,
            "regression_slope": 0.85,  # Placeholder for real regression
            "regression_p_value": 0.03,
            "regression_r_squared": 0.92,
            "sensitivity_mean": sensitivity_results["mean_conductivity"],
            "sensitivity_std": sensitivity_results["std_conductivity"],
            "sensitivity_deviation": sensitivity_results["deviation_percent"]
        }
        
        # Write to CSV
        append_results_to_csv([final_result], results_file)
        
        # Verify output
        assert os.path.exists(results_file), "Results file must exist"
        
        with open(results_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1, "Should have exactly one result"
        row = rows[0]
        
        # Verify all required columns are present
        required_columns = [
            "seed", "N", "p", "avg_degree", "conductivity",
            "percolation_flag", "scaling_factor",
            "regression_slope", "regression_p_value", "regression_r_squared",
            "sensitivity_mean", "sensitivity_std", "sensitivity_deviation"
        ]
        
        for col in required_columns:
            assert col in row, f"Missing required column: {col}"
            assert row[col] != "", f"Column {col} is empty"

    def test_material_db_integration(self):
        """Verify material database integration works correctly."""
        # Test standard material
        si_k = get_material_conductivity("Si")
        assert si_k == 149.0, f"Si conductivity should be 149, got {si_k}"
        
        # Test another standard material
        cnt_k = get_material_conductivity("CNT")
        assert cnt_k == 3500.0, f"CNT conductivity should be 3500, got {cnt_k}"

    def test_error_handling_integration(self, temp_output_dir):
        """Verify pipeline handles errors gracefully."""
        from material_db import get_material_conductivity
        
        # Test non-existent material raises error
        with pytest.raises(ValueError) as excinfo:
            get_material_conductivity("NonExistentMaterial")
        
        assert "not found in local store or NIST defaults" in str(excinfo.value)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
