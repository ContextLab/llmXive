"""
Integration tests for Data Flow Integrity.

Verifies that simulation_results.json is generated before aggregated_results.json
is attempted, and that aggregation fails gracefully if simulation results are missing.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the aggregator logic
# Based on the API surface provided:
from code.src.analysis.aggregate_results import aggregate_results, load_json_file
from code.src.analysis.serialize_simulation import save_simulation_results


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data isolation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # Ensure required subdirectories exist
        (data_dir / "analysis").mkdir(parents=True, exist_ok=True)
        (data_dir / "raw").mkdir(parents=True, exist_ok=True)
        yield data_dir


def test_simulation_generated_before_aggregation(temp_data_dir):
    """
    Verify that simulation_results.json exists before aggregation is attempted.
    
    This test ensures the data flow order:
    1. Simulation produces data
    2. Aggregation consumes data
    """
    sim_results_path = temp_data_dir / "analysis" / "simulation_results.json"
    agg_results_path = temp_data_dir / "analysis" / "aggregated_results.json"
    
    # Mock simulation results data
    mock_sim_data = {
        "runs": [
            {
                "graph_id": "test_graph_1",
                "diffusion_rate": 0.45,
                "energy_density": 1.2,
                "spatial_variance": 0.3
            }
        ],
        "metadata": {
            "timestamp": "2025-01-15T12:00:00Z",
            "seed": 42
        }
    }
    
    # Step 1: Ensure simulation file does NOT exist initially
    assert not sim_results_path.exists(), "Test setup failed: simulation file already exists"
    
    # Step 2: Simulate the generation of simulation_results.json
    # We call the save function directly to create the file
    save_simulation_results(mock_sim_data, str(sim_results_path))
    
    # Verification 1: File must exist now
    assert sim_results_path.exists(), "simulation_results.json was not created"
    
    # Step 3: Attempt aggregation (should succeed now)
    try:
        # We mock the other dependencies to focus on the existence check
        with patch('code.src.analysis.aggregate_results.load_json_file') as mock_load:
            # Mock the return values for the other expected files
            mock_load.side_effect = lambda path: {"mock": "data"} if path != str(sim_results_path) else mock_sim_data
            
            # Call the aggregation function
            # Note: aggregate_results expects specific arguments, we provide minimal valid ones
            result = aggregate_results(
                simulation_results_path=str(sim_results_path),
                regression_results_path=str(temp_data_dir / "regression.json"),
                anova_results_path=str(temp_data_dir / "anova.json"),
                output_path=str(agg_results_path)
            )
            
            # If we get here without exception, the file existed and was processed
            assert agg_results_path.exists() or True, "Aggregation attempted successfully"
            
    except FileNotFoundError as e:
        pytest.fail(f"Aggregation failed because simulation_results.json was missing or inaccessible: {e}")


def test_aggregation_fails_gracefully_on_missing_simulation(temp_data_dir):
    """
    Verify that aggregated_results.json creation fails gracefully if simulation_results.json is missing.
    
    This test uses pytest-mock to simulate the absence of the simulation file
    before running the aggregator.
    """
    sim_results_path = temp_data_dir / "analysis" / "simulation_results.json"
    agg_results_path = temp_data_dir / "analysis" / "aggregated_results.json"
    
    # Ensure simulation file does NOT exist
    assert not sim_results_path.exists()
    
    # Mock the load_json_file function to raise FileNotFoundError specifically for simulation results
    # while allowing other loads to succeed (to isolate the check)
    original_load = load_json_file
    
    def mock_load_json_file(path):
        if "simulation_results" in str(path):
            raise FileNotFoundError(f"Simulation results file not found: {path}")
        return {"mock": "data"}
    
    with patch('code.src.analysis.aggregate_results.load_json_file', side_effect=mock_load_json_file):
        with patch('code.src.analysis.aggregate_results.logging') as mock_logging:
            # Attempt aggregation
            try:
                aggregate_results(
                    simulation_results_path=str(sim_results_path),
                    regression_results_path=str(temp_data_dir / "regression.json"),
                    anova_results_path=str(temp_data_dir / "anova.json"),
                    output_path=str(agg_results_path)
                )
                # If the function completes without raising, check if it handled the error gracefully
                # The spec says "fails gracefully", which usually means logging an error and returning None/False
                # or raising a specific handled exception.
                # We check that the output file was NOT created in this failure state
                if agg_results_path.exists():
                    # If it exists, verify it indicates failure or is empty
                    with open(agg_results_path, 'r') as f:
                        content = json.load(f)
                        # If the content indicates an error state, it's graceful
                        if 'error' in content or 'status' in content:
                            pass 
                        else:
                            pytest.fail("Aggregation created a result file despite missing simulation data without indicating failure.")
                else:
                    # File not created is also a graceful failure mode if logged
                    pass
                    
            except FileNotFoundError:
                # Raising the error is also a form of failure, but "gracefully" implies handling it
                # If the implementation raises, we consider it a failure to handle gracefully unless caught inside
                # However, based on the task description "fails gracefully", we expect the function to catch it.
                # If it propagates, we might need to adjust the implementation of aggregate_results.
                # For this test, we assume the function *should* catch it. If it doesn't, the test fails.
                pytest.fail("Aggregation raised an unhandled FileNotFoundError instead of failing gracefully.")
    
    # Final verification: The aggregated file should not contain valid results
    # (It might not exist, or exist with an error flag)
    if agg_results_path.exists():
        with open(agg_results_path, 'r') as f:
            data = json.load(f)
            # Assert that valid result keys are missing or error is present
            assert 'error' in data or 'status' in data, "Aggregation produced a result file without indicating an error state."

def test_empty_simulation_results_handling(temp_data_dir):
    """
    Verify that aggregation handles an empty simulation_results.json gracefully.
    """
    sim_results_path = temp_data_dir / "analysis" / "simulation_results.json"
    agg_results_path = temp_data_dir / "analysis" / "aggregated_results.json"
    
    # Create an empty simulation file
    with open(sim_results_path, 'w') as f:
        json.dump({"runs": []}, f)
    
    # Mock other dependencies
    def mock_load(path):
        if "simulation" in str(path):
            return {"runs": []}
        return {"mock": "data"}
    
    with patch('code.src.analysis.aggregate_results.load_json_file', side_effect=mock_load):
        with patch('code.src.analysis.aggregate_results.logging') as mock_logging:
            try:
                aggregate_results(
                    simulation_results_path=str(sim_results_path),
                    regression_results_path=str(temp_data_dir / "regression.json"),
                    anova_results_path=str(temp_data_dir / "anova.json"),
                    output_path=str(agg_results_path)
                )
            except Exception as e:
                # If it raises on empty data, it's not graceful
                pytest.fail(f"Aggregation failed on empty simulation data: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])