import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
# Assuming the test is run from the project root or code directory
# We need to ensure 'src' is importable.
# In a real run, this would be handled by PYTHONPATH or setup.py
# For this test, we assume the environment is set up correctly.
try:
    from src.feasibility import main, write_feasibility_gate_result, count_available_tumor_types, get_valid_geo_count
except ImportError:
    # Fallback for direct execution in code/
    from feasibility import main, write_feasibility_gate_result, count_available_tumor_types, get_valid_geo_count

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create mock tcga_samples.json
    tcga_samples = {
        "samples": [
            {"sample_id": "TCGA-1", "tumor_type": "BRCA", "response_label": "CR", "expression_vector": []},
            {"sample_id": "TCGA-2", "tumor_type": "BRCA", "response_label": "PR", "expression_vector": []},
            {"sample_id": "TCGA-3", "tumor_type": "LUAD", "response_label": "SD", "expression_vector": []},
            {"sample_id": "TCGA-4", "tumor_type": "LUAD", "response_label": "PD", "expression_vector": []},
            {"sample_id": "TCGA-5", "tumor_type": "PRAD", "response_label": "CR", "expression_vector": []},
            {"sample_id": "TCGA-6", "tumor_type": "PRAD", "response_label": "PR", "expression_vector": []},
            {"sample_id": "TCGA-7", "tumor_type": "COAD", "response_label": "SD", "expression_vector": []}, # 4th type
        ]
    }
    tcga_path = data_dir / "tcga_samples.json"
    with open(tcga_path, 'w') as f:
        json.dump(tcga_samples, f)
    
    # Create mock geo_samples.json
    geo_samples = {
        "samples": [
            {"sample_id": "GSE1-1", "dataset_id": "GSE25055", "tumor_type": "BRCA", "response_label": "CR", "expression_vector": []},
            {"sample_id": "GSE1-2", "dataset_id": "GSE25055", "tumor_type": "BRCA", "response_label": "PR", "expression_vector": []},
            {"sample_id": "GSE2-1", "dataset_id": "GSE42752", "tumor_type": "BRCA", "response_label": "SD", "expression_vector": []},
            {"sample_id": "GSE2-2", "dataset_id": "GSE42752", "tumor_type": "BRCA", "response_label": "PD", "expression_vector": []},
        ]
    }
    geo_path = data_dir / "geo_samples.json"
    with open(geo_path, 'w') as f:
        json.dump(geo_samples, f)
    
    return tmp_path

@pytest.fixture
def temp_project_dir_insufficient_tcga(tmp_path):
    """Create a temporary project structure with insufficient TCGA types."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Only 2 types
    tcga_samples = {
        "samples": [
            {"sample_id": "TCGA-1", "tumor_type": "BRCA", "response_label": "CR", "expression_vector": []},
            {"sample_id": "TCGA-2", "tumor_type": "BRCA", "response_label": "PR", "expression_vector": []},
            {"sample_id": "TCGA-3", "tumor_type": "LUAD", "response_label": "SD", "expression_vector": []},
            {"sample_id": "TCGA-4", "tumor_type": "LUAD", "response_label": "PD", "expression_vector": []},
        ]
    }
    tcga_path = data_dir / "tcga_samples.json"
    with open(tcga_path, 'w') as f:
        json.dump(tcga_samples, f)
    
    # 2 valid GEO datasets
    geo_samples = {
        "samples": [
            {"sample_id": "GSE1-1", "dataset_id": "GSE25055", "tumor_type": "BRCA", "response_label": "CR", "expression_vector": []},
            {"sample_id": "GSE2-1", "dataset_id": "GSE42752", "tumor_type": "BRCA", "response_label": "SD", "expression_vector": []},
        ]
    }
    geo_path = data_dir / "geo_samples.json"
    with open(geo_path, 'w') as f:
        json.dump(geo_samples, f)
    
    return tmp_path

@pytest.fixture
def temp_project_dir_insufficient_geo(tmp_path):
    """Create a temporary project structure with sufficient TCGA but insufficient GEO."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # 4 types
    tcga_samples = {
        "samples": [
            {"sample_id": "TCGA-1", "tumor_type": "BRCA", "response_label": "CR", "expression_vector": []},
            {"sample_id": "TCGA-2", "tumor_type": "LUAD", "response_label": "PR", "expression_vector": []},
            {"sample_id": "TCGA-3", "tumor_type": "PRAD", "response_label": "SD", "expression_vector": []},
            {"sample_id": "TCGA-4", "tumor_type": "COAD", "response_label": "PD", "expression_vector": []},
        ]
    }
    tcga_path = data_dir / "tcga_samples.json"
    with open(tcga_path, 'w') as f:
        json.dump(tcga_samples, f)
    
    # Only 1 valid GEO dataset
    geo_samples = {
        "samples": [
            {"sample_id": "GSE1-1", "dataset_id": "GSE25055", "tumor_type": "BRCA", "response_label": "CR", "expression_vector": []},
            {"sample_id": "GSE1-2", "dataset_id": "GSE25055", "tumor_type": "BRCA", "response_label": "PR", "expression_vector": []},
        ]
    }
    geo_path = data_dir / "geo_samples.json"
    with open(geo_path, 'w') as f:
        json.dump(geo_samples, f)
    
    return tmp_path

@pytest.fixture
def temp_project_dir_missing_files(tmp_path):
    """Create a temporary project structure with missing data files."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    # No files created
    return tmp_path

def test_feasibility_gate_ready(temp_project_dir, monkeypatch, tmp_path):
    """Test that the gate passes when requirements are met."""
    # Mock get_project_root to return tmp_path
    # We need to patch the function in the module where it's used
    import src.feasibility as feasibility_module
    
    original_get_project_root = feasibility_module.get_project_root
    feasibility_module.get_project_root = lambda: temp_project_dir
    
    try:
        # Run main
        exit_code = feasibility_module.main()
        
        # Check exit code
        assert exit_code == 0, "Expected exit code 0 for ready status"
        
        # Check file content
        gate_path = temp_project_dir / "data" / "feasibility_gate.json"
        assert gate_path.exists(), "feasibility_gate.json should exist"
        
        with open(gate_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "ready", f"Expected status 'ready', got '{result['status']}'"
        assert result["tcga_count"] >= 3, f"Expected tcga_count >= 3, got {result['tcga_count']}"
        assert result["geo_count"] >= 2, f"Expected geo_count >= 2, got {result['geo_count']}"
    finally:
        feasibility_module.get_project_root = original_get_project_root

def test_feasibility_gate_halted_tcga(temp_project_dir_insufficient_tcga, monkeypatch, tmp_path):
    """Test that the gate halts when TCGA types are insufficient."""
    import src.feasibility as feasibility_module
    
    original_get_project_root = feasibility_module.get_project_root
    feasibility_module.get_project_root = lambda: temp_project_dir_insufficient_tcga
    
    try:
        exit_code = feasibility_module.main()
        
        assert exit_code == 1, "Expected exit code 1 for halted status"
        
        gate_path = temp_project_dir_insufficient_tcga / "data" / "feasibility_gate.json"
        assert gate_path.exists(), "feasibility_gate.json should exist"
        
        with open(gate_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted", f"Expected status 'halted', got '{result['status']}'"
        assert result["reason"] == "insufficient_tcga_types", f"Expected reason 'insufficient_tcga_types', got '{result['reason']}'"
        assert result["tcga_count"] < 3, f"Expected tcga_count < 3, got {result['tcga_count']}"
    finally:
        feasibility_module.get_project_root = original_get_project_root

def test_feasibility_gate_halted_geo(temp_project_dir_insufficient_geo, monkeypatch, tmp_path):
    """Test that the gate halts when GEO datasets are insufficient."""
    import src.feasibility as feasibility_module
    
    original_get_project_root = feasibility_module.get_project_root
    feasibility_module.get_project_root = lambda: temp_project_dir_insufficient_geo
    
    try:
        exit_code = feasibility_module.main()
        
        assert exit_code == 1, "Expected exit code 1 for halted status"
        
        gate_path = temp_project_dir_insufficient_geo / "data" / "feasibility_gate.json"
        assert gate_path.exists(), "feasibility_gate.json should exist"
        
        with open(gate_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted", f"Expected status 'halted', got '{result['status']}'"
        assert result["reason"] == "insufficient_geo_datasets", f"Expected reason 'insufficient_geo_datasets', got '{result['reason']}'"
        assert result["geo_count"] < 2, f"Expected geo_count < 2, got {result['geo_count']}"
    finally:
        feasibility_module.get_project_root = original_get_project_root

def test_feasibility_gate_test_mode(temp_project_dir_insufficient_tcga, monkeypatch, tmp_path):
    """Test that the gate passes in TEST_MODE even with insufficient data."""
    import src.feasibility as feasibility_module
    
    original_get_project_root = feasibility_module.get_project_root
    feasibility_module.get_project_root = lambda: temp_project_dir_insufficient_tcga
    
    # Set TEST_MODE
    monkeypatch.setenv("TEST_MODE", "True")
    
    try:
        exit_code = feasibility_module.main()
        
        assert exit_code == 0, "Expected exit code 0 in TEST_MODE"
        
        gate_path = temp_project_dir_insufficient_tcga / "data" / "feasibility_gate.json"
        assert gate_path.exists(), "feasibility_gate.json should exist"
        
        with open(gate_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "ready", f"Expected status 'ready' in TEST_MODE, got '{result['status']}'"
    finally:
        feasibility_module.get_project_root = original_get_project_root
        # Clean up env
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]

def test_feasibility_gate_missing_files(temp_project_dir_missing_files, monkeypatch, tmp_path):
    """Test behavior when data files are missing."""
    import src.feasibility as feasibility_module
    
    original_get_project_root = feasibility_module.get_project_root
    feasibility_module.get_project_root = lambda: temp_project_dir_missing_files
    
    try:
        exit_code = feasibility_module.main()
        
        # Should halt because counts will be 0
        assert exit_code == 1, "Expected exit code 1 when files are missing"
        
        gate_path = temp_project_dir_missing_files / "data" / "feasibility_gate.json"
        assert gate_path.exists(), "feasibility_gate.json should exist"
        
        with open(gate_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted", f"Expected status 'halted', got '{result['status']}'"
        # Reason could be either, depending on which check runs first or combined
        assert result["reason"] in ["insufficient_tcga_types", "insufficient_geo_datasets", "insufficient_tcga_types_and_geo_datasets"]
    finally:
        feasibility_module.get_project_root = original_get_project_root