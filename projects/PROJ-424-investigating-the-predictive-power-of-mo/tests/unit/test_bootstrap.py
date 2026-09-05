import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from analysis.bootstrap import (
    perform_bootstrap,
    run_bootstrap_analysis,
    load_mae_distribution,
    BootstrapIterationResult
)
from data_models.bootstrap_stats import BootstrapStats

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory with mock MAE distributions."""
    data_dir = tmp_path / "processed"
    data_dir.mkdir()
    
    # Create mock MAE distribution files
    solvents = ['water', 'ethanol', 'acetone']
    timescales = ['1ns', '5ns', '10ns']
    
    for solvent in solvents:
        for timescale in timescales:
            mae_values = np.random.normal(loc=0.5, scale=0.1, size=1000).tolist()
            file_path = data_dir / f"{solvent}_{timescale}_mae_distribution.json"
            with open(file_path, 'w') as f:
                json.dump({'mae_values': mae_values}, f)
    
    return data_dir

def test_perform_bootstrap_basic():
    """Test basic bootstrap functionality with known input."""
    mae_values = [0.5, 0.6, 0.4, 0.7, 0.3]
    n_iterations = 1000
    
    mean, std, ci_lower, ci_upper = perform_bootstrap(mae_values, n_iterations)
    
    # Check that outputs are reasonable
    assert isinstance(mean, float)
    assert isinstance(std, float)
    assert isinstance(ci_lower, float)
    assert isinstance(ci_upper, float)
    
    # Mean should be close to the sample mean
    expected_mean = np.mean(mae_values)
    assert abs(mean - expected_mean) < 0.05  # Tolerance for randomness
    
    # CI should be ordered
    assert ci_lower <= mean <= ci_upper

def test_perform_bootstrap_empty_list():
    """Test that empty list raises ValueError."""
    with pytest.raises(ValueError, match="MAE values list is empty"):
        perform_bootstrap([], 1000)

def test_load_mae_distribution_success(temp_data_dir):
    """Test loading an existing MAE distribution file."""
    solvent = 'water'
    timescale = '1ns'
    
    mae_values = load_mae_distribution(temp_data_dir, solvent, timescale)
    
    assert isinstance(mae_values, list)
    assert len(mae_values) == 1000
    assert all(isinstance(v, float) for v in mae_values)

def test_load_mae_distribution_not_found(temp_data_dir):
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="MAE distribution file not found"):
        load_mae_distribution(temp_data_dir, 'nonexistent', '1ns')

def test_load_mae_distribution_invalid_format(temp_data_dir):
    """Test that invalid JSON format raises ValueError."""
    solvent = 'water'
    timescale = '5ns'
    
    # Create an invalid file
    file_path = temp_data_dir / f"{solvent}_{timescale}_mae_distribution.json"
    with open(file_path, 'w') as f:
        json.dump({'wrong_key': [1, 2, 3]}, f)
    
    with pytest.raises(ValueError, match="Invalid MAE distribution file"):
        load_mae_distribution(temp_data_dir, solvent, timescale)

def test_run_bootstrap_analysis_success(temp_data_dir):
    """Test successful bootstrap analysis for a single combination."""
    solvent = 'water'
    timescale = '1ns'
    
    result = run_bootstrap_analysis(
        solvent=solvent,
        timescale=timescale,
        data_dir=temp_data_dir,
        max_iterations=100,
        fallback_iterations=100,
        timeout_seconds=3600  # 1 hour, plenty for 100 iterations
    )
    
    assert isinstance(result, BootstrapIterationResult)
    assert result.solvent == solvent
    assert result.timescale == timescale
    assert result.iterations_used == 100
    assert not result.fallback_triggered  # Should not trigger fallback with 100 iterations
    assert result.mean_mae > 0
    assert result.ci_lower <= result.mean_mae <= result.ci_upper

def test_run_bootstrap_analysis_file_not_found(temp_data_dir):
    """Test that missing MAE distribution raises error."""
    with pytest.raises(FileNotFoundError):
        run_bootstrap_analysis(
            solvent='nonexistent',
            timescale='1ns',
            data_dir=temp_data_dir,
            max_iterations=100
        )

def test_bootstrap_stats_dataclass():
    """Test the BootstrapStats dataclass structure."""
    from datetime import datetime
    
    stats = BootstrapStats(
        solvent='water',
        timescale='1ns',
        mean_mae=0.5,
        std_mae=0.1,
        ci_lower=0.4,
        ci_upper=0.6,
        iterations_used=1000,
        fallback_triggered=False,
        timestamp=datetime.utcnow().isoformat()
    )
    
    assert stats.solvent == 'water'
    assert stats.mean_mae == 0.5
    assert stats.iterations_used == 1000
    assert not stats.fallback_triggered