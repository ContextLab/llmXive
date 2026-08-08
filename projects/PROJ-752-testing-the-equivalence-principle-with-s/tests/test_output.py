import os
import json
import tempfile
import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys
import pathlib

# Add code directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from data.output import (
    compute_sha256,
    save_orbit_solution,
    save_eotvos_metrics,
    run_output_pipeline,
    record_checksum
)
from models.estimator import OrbitSolution
from analysis.eotvos import EotvosResult
from utils.logging import AnalysisError

@pytest.fixture
def mock_solution():
    """Create a mock OrbitSolution for testing."""
    solution = Mock(spec=OrbitSolution)
    solution.converged = True
    solution.residuals_norm = 1.2e-5
    solution.iterations = 15
    solution.satellites = ["LAGEOS-1", "LAGEOS-2"]
    
    # Mock extract_joint_parameters behavior
    # We'll patch the function in the module
    return solution

@pytest.fixture
def mock_eotvos_result():
    """Create a mock EotvosResult for testing."""
    result = Mock(spec=EotvosResult)
    result.eta = 1.5e-14
    result.eta_std = 0.3e-14
    result.ci_95_lower = 0.9e-14
    result.ci_95_upper = 2.1e-14
    result.ac = 1.5e-13
    result.g = 9.8
    result.solution = None  # Will be set if needed
    return result

def test_compute_sha256():
    """Test SHA256 computation on a temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_sha256(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_save_orbit_solution(tmp_path):
    """Test saving OrbitSolution to JSON."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output_path = output_dir / "orbit_solutions.json"
    
    # Create a mock solution with extractable parameters
    solution = Mock(spec=OrbitSolution)
    solution.converged = True
    solution.residuals_norm = 1.2e-5
    solution.iterations = 15
    solution.satellites = ["LAGEOS-1", "LAGEOS-2"]
    
    # Mock the extract_joint_parameters to return known values
    mock_params = {
        'ac': 1.5e-13,
        'g': 9.8,
        'covariance': np.array([[1e-26, 0], [0, 1e-2]])
    }
    
    with patch('data.output.extract_joint_parameters', return_value=mock_params):
        save_orbit_solution(solution, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['ac'] == 1.5e-13
    assert data['g'] == 9.8
    assert data['converged'] is True
    assert 'covariance' in data
    assert 'timestamp' in data

def test_save_eotvos_metrics(tmp_path):
    """Test saving EotvosResult to JSON."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output_path = output_dir / "eotvos_metrics.json"
    
    eotvos_result = Mock(spec=EotvosResult)
    eotvos_result.eta = 1.5e-14
    eotvos_result.eta_std = 0.3e-14
    eotvos_result.ci_95_lower = 0.9e-14
    eotvos_result.ci_95_upper = 2.1e-14
    eotvos_result.ac = 1.5e-13
    eotvos_result.g = 9.8
    eotvos_result.solution = None
    
    save_eotvos_metrics(eotvos_result, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['eta'] == 1.5e-14
    assert data['eta_std'] == 0.3e-14
    assert data['ci_95_lower'] == 0.9e-14
    assert data['ci_95_upper'] == 2.1e-14
    assert data['ac'] == 1.5e-13
    assert data['g'] == 9.8
    assert 'timestamp' in data

def test_save_eotvos_metrics_fails_without_eta(tmp_path):
    """Test that saving EotvosResult fails when eta is None and no solution."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output_path = output_dir / "eotvos_metrics.json"
    
    eotvos_result = Mock(spec=EotvosResult)
    eotvos_result.eta = None
    eotvos_result.eta_std = None
    eotvos_result.ci_95_lower = None
    eotvos_result.ci_95_upper = None
    eotvos_result.ac = None
    eotvos_result.g = None
    eotvos_result.solution = None  # No solution available
    
    with pytest.raises(AnalysisError, match="Cannot save EotvosResult"):
        save_eotvos_metrics(eotvos_result, str(output_path))

def test_run_output_pipeline(tmp_path):
    """Test the full output pipeline."""
    output_dir = tmp_path / "results"
    
    solution = Mock(spec=OrbitSolution)
    solution.converged = True
    solution.residuals_norm = 1.2e-5
    solution.iterations = 15
    solution.satellites = ["LAGEOS-1", "LAGEOS-2"]
    
    mock_params = {
        'ac': 1.5e-13,
        'g': 9.8,
        'covariance': np.array([[1e-26, 0], [0, 1e-2]])
    }
    
    eotvos_result = Mock(spec=EotvosResult)
    eotvos_result.eta = 1.5e-14
    eotvos_result.eta_std = 0.3e-14
    eotvos_result.ci_95_lower = 0.9e-14
    eotvos_result.ci_95_upper = 2.1e-14
    eotvos_result.ac = 1.5e-13
    eotvos_result.g = 9.8
    eotvos_result.solution = None
    
    with patch('data.output.extract_joint_parameters', return_value=mock_params):
        results = run_output_pipeline(
            solution=solution,
            eotvos_result=eotvos_result,
            output_dir=str(output_dir)
        )
    
    assert 'orbit_solutions' in results
    assert 'eotvos_metrics' in results
    assert os.path.exists(results['orbit_solutions'])
    assert os.path.exists(results['eotvos_metrics'])
    
    # Check checksums file was created
    checksums_path = output_dir / ".checksums.json"
    assert checksums_path.exists()
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    assert 'orbit_solutions.json' in checksums
    assert 'eotvos_metrics.json' in checksums

def test_record_checksum(tmp_path):
    """Test checksum recording."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    checksums_path = tmp_path / ".checksums.json"
    
    record_checksum(str(test_file), str(checksums_path))
    
    assert checksums_path.exists()
    
    with open(checksums_path, 'r') as f:
        data = json.load(f)
    
    assert 'test.txt' in data
    assert data['test.txt']['sha256'] == compute_sha256(str(test_file))