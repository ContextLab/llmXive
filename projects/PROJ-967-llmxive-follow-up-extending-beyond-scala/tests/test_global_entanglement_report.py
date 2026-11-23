import json
import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from global_entanglement_report import (
    setup_directories,
    load_dominant_eigenvalue,
    load_covariance_matrix,
    generate_entanglement_report,
    save_report
)

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        results_dir = base / "results"
        processed_dir = base / "data" / "processed"
        results_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        
        # Create dummy input files
        eigenvalue_data = {"dominant_eigenvalue": 12.345}
        with open(results_dir / "dominant_eigenvalue.json", 'w') as f:
            json.dump(eigenvalue_data, f)
        
        matrix_data = {"matrix": [[1.0, 0.5], [0.5, 1.0]], "dominant_eigenvalue": 12.345}
        with open(results_dir / "covariance_matrix.json", 'w') as f:
            json.dump(matrix_data, f)
        
        yield base
        # Cleanup is handled by TemporaryDirectory

def test_setup_directories(temp_project_dir):
    processed_dir, results_dir = setup_directories(temp_project_dir)
    assert processed_dir.exists()
    assert results_dir.exists()

def test_load_dominant_eigenvalue(temp_project_dir):
    results_dir = temp_project_dir / "results"
    data = load_dominant_eigenvalue(results_dir)
    assert "dominant_eigenvalue" in data
    assert data["dominant_eigenvalue"] == 12.345

def test_load_covariance_matrix(temp_project_dir):
    results_dir = temp_project_dir / "results"
    data = load_covariance_matrix(results_dir)
    assert "matrix" in data
    assert len(data["matrix"]) == 2

def test_generate_entanglement_report(temp_project_dir):
    results_dir = temp_project_dir / "results"
    eigenvalue_data = load_dominant_eigenvalue(results_dir)
    matrix_data = load_covariance_matrix(results_dir)
    
    dims = ["dim1", "dim2", "dim3", "dim4"]
    report = generate_entanglement_report(eigenvalue_data, matrix_data, dims)
    
    assert "covariance_matrix" in report
    assert "dominant_eigenvalue" in report
    assert report["computation_source"] == "filtered_data"
    assert "timestamp" in report
    assert report["dimension_list"] == dims
    assert isinstance(report["timestamp"], str)

def test_save_report(temp_project_dir):
    results_dir = temp_project_dir / "results"
    eigenvalue_data = load_dominant_eigenvalue(results_dir)
    matrix_data = load_covariance_matrix(results_dir)
    dims = ["dim1", "dim2", "dim3", "dim4"]
    
    report = generate_entanglement_report(eigenvalue_data, matrix_data, dims)
    processed_dir = temp_project_dir / "data" / "processed"
    
    save_report(report, processed_dir)
    
    output_path = processed_dir / "global_entanglement_report.json"
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report == report

def test_missing_files(temp_project_dir):
    results_dir = temp_project_dir / "results"
    # Remove eigenvalue file
    (results_dir / "dominant_eigenvalue.json").unlink()
    
    with pytest.raises(FileNotFoundError):
        load_dominant_eigenvalue(results_dir)