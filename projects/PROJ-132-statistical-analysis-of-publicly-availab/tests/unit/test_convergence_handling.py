import pytest
import logging
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np

from src.models.gamm_fit import fit_species_year_gamm, run_gamm_pipeline

@pytest.fixture
def sample_gamm_data():
    """Generate a synthetic dataset that mimics the expected preprocessed schema."""
    n = 500
    data = {
        'species': np.random.choice(['Species_A', 'Species_B', 'Species_C'], n),
        'year': np.random.choice([2020, 2021, 2022], n),
        'phenology_metric': np.random.normal(100, 10, n),
        'mean_temperature': np.random.normal(15, 5, n),
        'total_precipitation': np.random.normal(50, 20, n),
        'extreme_weather_index': np.random.normal(0.5, 0.2, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_convergence_failure_logging(sample_gamm_data, temp_log_dir, caplog):
    """
    Verify that when a convergence failure occurs, the log message matches the required format:
    "Convergence failed for species {species}: {error}"
    
    We simulate a failure by passing data that will cause a singular matrix condition.
    """
    # Create data that causes singularity (constant values)
    singular_data = pd.DataFrame({
        'species': ['Bad_Species'] * 50,
        'phenology_metric': [10.0] * 50,
        'mean_temperature': [5.0] * 50, # Constant X
        'total_precipitation': [5.0] * 50, # Constant X
        'extreme_weather_index': [5.0] * 50 # Constant X
    })

    log_file = Path(temp_log_dir) / "test_modeling.log"
    
    # Configure logger to write to file and capture
    logger = logging.getLogger("src.models.gamm_fit")
    logger.setLevel(logging.ERROR)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Run the function
    result, converged = fit_species_year_gamm(singular_data, 'Bad_Species')

    # Assertions
    assert converged is False
    assert result == {}
    
    # Check file content
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    # Verify the specific log format required by T027
    assert "Convergence failed for species Bad_Species" in log_content
    assert "Matrix singularity" in log_content or "ill-conditioned" in log_content

def test_convergence_success_logging(sample_gamm_data, temp_log_dir, caplog):
    """
    Verify that successful fits do NOT produce convergence failure logs.
    """
    log_file = Path(temp_log_dir) / "test_modeling_success.log"
    
    logger = logging.getLogger("src.models.gamm_fit")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    result, converged = fit_species_year_gamm(sample_gamm_data, 'Species_A')

    assert converged is True
    assert result != {}
    
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    # Ensure no failure message
    assert "Convergence failed" not in log_content

def test_run_gamm_pipeline_handles_failures(sample_gamm_data, temp_log_dir):
    """
    Test that the full pipeline continues processing other species even if one fails.
    """
    # Inject a "bad" species that will fail
    bad_row = pd.DataFrame({
        'species': ['Fail_Species'] * 10,
        'phenology_metric': [1.0] * 10,
        'mean_temperature': [1.0] * 10,
        'total_precipitation': [1.0] * 10,
        'extreme_weather_index': [1.0] * 10
    })
    combined_data = pd.concat([sample_gamm_data, bad_row], ignore_index=True)
    
    input_path = Path(temp_log_dir) / "input.parquet"
    output_path = Path(temp_log_dir) / "output.json"
    log_path = Path(temp_log_dir) / "pipeline.log"
    
    combined_data.to_parquet(input_path)
    
    stats = run_gamm_pipeline(str(input_path), str(output_path), str(log_path))
    
    # Should have processed the good species
    assert stats['successful_fits'] > 0
    # Should have counted the failure
    assert stats['failed_fits'] > 0
    
    # Verify log contains the failure message
    with open(log_path, 'r') as f:
        log_content = f.read()
    assert "Convergence failed for species Fail_Species" in log_content
    
    # Verify output file exists and is valid JSON
    assert os.path.exists(output_path)
    import json
    with open(output_path, 'r') as f:
        results = json.load(f)
    # Fail_Species should not be in the results
    species_names = [r['species'] for r in results]
    assert 'Fail_Species' not in species_names