"""
Integration tests for T022: Data ingestion pipeline.
"""
import json
import os
import tempfile
import shutil
import csv
from pathlib import Path
import pytest
import numpy as np

# Import the module under test
from code.run_tests import main, _load_seed_map, _load_params, _generate_data_for_params
from code.utils.exceptions import HighDimensionalInstabilityError

@pytest.fixture
def mock_data_environment():
    """
    Creates a temporary directory structure with mock seed_map.json and params.csv
    to test the ingestion pipeline without relying on previous tasks' outputs.
    """
    temp_dir = tempfile.mkdtemp()
    sweep_dir = Path(temp_dir) / "data" / "sweep"
    sweep_dir.mkdir(parents=True)
    results_dir = Path(temp_dir) / "data" / "results"
    results_dir.mkdir(parents=True)

    # Create a minimal seed map
    seed_map = {
        "n=100,p=500,rho=0.0,dist=normal": [42, 43],
        "n=50,p=200,rho=0.5,dist=t": [100]
    }
    with open(sweep_dir / "seed_map.json", "w") as f:
        json.dump(seed_map, f)

    # Create a minimal params.csv
    params_data = [
        {"seed": 42, "n": 100, "p": 500, "rho": 0.0, "distribution_type": "normal", "iteration": 1},
        {"seed": 43, "n": 100, "p": 500, "rho": 0.0, "distribution_type": "normal", "iteration": 2},
        {"seed": 100, "n": 50, "p": 200, "rho": 0.5, "distribution_type": "t", "iteration": 1}
    ]
    
    params_file = sweep_dir / "params.csv"
    with open(params_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=params_data[0].keys())
        writer.writeheader()
        writer.writerows(params_data)

    return temp_dir

def test_load_seed_map_valid(mock_data_environment):
    """Test loading a valid seed map."""
    os.chdir(mock_data_environment)
    seed_map = _load_seed_map()
    assert isinstance(seed_map, dict)
    assert len(seed_map) == 2

def test_load_params_valid(mock_data_environment):
    """Test loading a valid params CSV."""
    os.chdir(mock_data_environment)
    params = _load_params()
    assert isinstance(params, list)
    assert len(params) == 3
    assert params[0]['seed'] == 42
    assert params[0]['n'] == 100

def test_pipeline_execution(mock_data_environment):
    """
    Test that the main pipeline runs, generates data, runs tests,
    and writes output files for valid inputs.
    """
    os.chdir(mock_data_environment)
    
    # Run the main function
    # We expect it to succeed for the mock data
    try:
        main()
    except Exception as e:
        # If it fails, it should be due to data generation logic, not file IO
        # For this integration test, we assume generate_correlated_data works
        # If it fails, we catch and assert the error is not a file missing error
        if "not found" in str(e).lower():
            pytest.fail(f"Pipeline failed due to missing files: {e}")
        # Otherwise, it might be a data generation issue, which is expected if 
        # generate_data.py is not fully mocked or if dependencies are missing.
        # However, the task is to implement the pipeline logic.
        # Let's check if output files were created before the crash.
        pass

    # Check that output files were created for the valid seeds
    results_dir = Path(mock_data_environment) / "data" / "results"
    
    # We expect files for seeds 42, 43, 100 if generation succeeded
    # Note: If generation fails for specific seeds (e.g. p/n > 10), those files won't exist.
    # In our mock, n=50, p=200 -> p/n = 4 < 10. So all should run.
    
    for seed in [42, 43, 100]:
        output_file = results_dir / f"pvalues_{seed}.csv"
        assert output_file.exists(), f"Output file for seed {seed} was not created."
        
        # Verify file content
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Check header
            assert "feature_index" in rows[0]
            assert "p_value" in rows[0]
            # Check row count (should be p)
            expected_p = 500 if seed in [42, 43] else 200
            assert len(rows) == expected_p, f"Expected {expected_p} rows for seed {seed}, got {len(rows)}"

def test_high_dimensional_instability_handling(mock_data_environment):
    """
    Test that the pipeline handles p/n > 10 gracefully (skips the iteration).
    """
    # Modify params.csv to include a case with p/n > 10
    sweep_dir = Path(mock_data_environment) / "data" / "sweep"
    params_file = sweep_dir / "params.csv"
    
    # Read existing params
    with open(params_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Add a bad row: n=10, p=200 -> p/n = 20 > 10
    bad_row = {
        "seed": 999,
        "n": 10,
        "p": 200,
        "rho": 0.0,
        "distribution_type": "normal",
        "iteration": 99
    }
    rows.append(bad_row)
    
    with open(params_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    os.chdir(mock_data_environment)
    
    # Run main
    main()
    
    # Check that the bad seed did NOT produce an output file
    results_dir = Path(mock_data_environment) / "data" / "results"
    bad_output = results_dir / "pvalues_999.csv"
    assert not bad_output.exists(), "Pipeline should not create output for unstable p/n ratio."
    
    # Check that good seeds still produced output
    assert (results_dir / "pvalues_42.csv").exists()