import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import shutil

# Add project root to path to import src modules
# Assuming tests are in code/tests/integration, project root is code/
# We need to import from src.feasibility which is in code/src
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.feasibility import (
    count_available_tumor_types,
    get_valid_geo_count,
    write_feasibility_gate_result
)
from src.config import get_project_root, ensure_directories


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure."""
    temp_dir = tempfile.mkdtemp()
    # Create necessary subdirectories
    (Path(temp_dir) / "data").mkdir(parents=True)
    (Path(temp_dir) / "data" / "raw").mkdir(parents=True)
    (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
    (Path(temp_dir) / "results").mkdir(parents=True)
    (Path(temp_dir) / "state" / "projects").mkdir(parents=True)
    
    # Mock TCGA samples (3 types)
    tcga_samples = [
        {"sample_id": "TCGA-001", "tumor_type": "BRCA", "response_label": "Responder", "expression_vector": [1.0, 2.0]},
        {"sample_id": "TCGA-002", "tumor_type": "BRCA", "response_label": "NonResponder", "expression_vector": [3.0, 4.0]},
        {"sample_id": "TCGA-003", "tumor_type": "LUAD", "response_label": "Responder", "expression_vector": [5.0, 6.0]},
        {"sample_id": "TCGA-004", "tumor_type": "LUAD", "response_label": "NonResponder", "expression_vector": [7.0, 8.0]},
        {"sample_id": "TCGA-005", "tumor_type": "PRAD", "response_label": "Responder", "expression_vector": [9.0, 10.0]},
    ]
    with open(Path(temp_dir) / "data" / "processed" / "tcga_samples.json", "w") as f:
        json.dump(tcga_samples, f)
    
    # Mock GEO samples (2 valid datasets)
    geo_samples = [
        {"sample_id": "GEO-001", "tumor_type": "BRCA", "response_label": "Responder", "expression_vector": [1.0, 2.0]},
        {"sample_id": "GEO-002", "tumor_type": "BRCA", "response_label": "NonResponder", "expression_vector": [3.0, 4.0]},
        {"sample_id": "GEO-003", "tumor_type": "LUAD", "response_label": "Responder", "expression_vector": [5.0, 6.0]},
        {"sample_id": "GEO-004", "tumor_type": "LUAD", "response_label": "NonResponder", "expression_vector": [7.0, 8.0]},
    ]
    with open(Path(temp_dir) / "data" / "processed" / "geo_samples.json", "w") as f:
        json.dump(geo_samples, f)
    
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_project_dir_insufficient_tcga():
    """Create a temporary project with < 3 TCGA types."""
    temp_dir = tempfile.mkdtemp()
    (Path(temp_dir) / "data").mkdir(parents=True)
    (Path(temp_dir) / "data" / "raw").mkdir(parents=True)
    (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
    (Path(temp_dir) / "results").mkdir(parents=True)
    (Path(temp_dir) / "state" / "projects").mkdir(parents=True)
    
    # Mock TCGA samples (only 2 types)
    tcga_samples = [
        {"sample_id": "TCGA-001", "tumor_type": "BRCA", "response_label": "Responder", "expression_vector": [1.0, 2.0]},
        {"sample_id": "TCGA-002", "tumor_type": "BRCA", "response_label": "NonResponder", "expression_vector": [3.0, 4.0]},
        {"sample_id": "TCGA-003", "tumor_type": "LUAD", "response_label": "Responder", "expression_vector": [5.0, 6.0]},
    ]
    with open(Path(temp_dir) / "data" / "processed" / "tcga_samples.json", "w") as f:
        json.dump(tcga_samples, f)
    
    # Mock GEO samples (2 valid datasets)
    geo_samples = [
        {"sample_id": "GEO-001", "tumor_type": "BRCA", "response_label": "Responder", "expression_vector": [1.0, 2.0]},
        {"sample_id": "GEO-002", "tumor_type": "BRCA", "response_label": "NonResponder", "expression_vector": [3.0, 4.0]},
    ]
    with open(Path(temp_dir) / "data" / "processed" / "geo_samples.json", "w") as f:
        json.dump(geo_samples, f)
    
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_project_dir_insufficient_geo():
    """Create a temporary project with < 2 valid GEO datasets."""
    temp_dir = tempfile.mkdtemp()
    (Path(temp_dir) / "data").mkdir(parents=True)
    (Path(temp_dir) / "data" / "raw").mkdir(parents=True)
    (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
    (Path(temp_dir) / "results").mkdir(parents=True)
    (Path(temp_dir) / "state" / "projects").mkdir(parents=True)
    
    # Mock TCGA samples (3 types)
    tcga_samples = [
        {"sample_id": "TCGA-001", "tumor_type": "BRCA", "response_label": "Responder", "expression_vector": [1.0, 2.0]},
        {"sample_id": "TCGA-002", "tumor_type": "BRCA", "response_label": "NonResponder", "expression_vector": [3.0, 4.0]},
        {"sample_id": "TCGA-003", "tumor_type": "LUAD", "response_label": "Responder", "expression_vector": [5.0, 6.0]},
        {"sample_id": "TCGA-004", "tumor_type": "LUAD", "response_label": "NonResponder", "expression_vector": [7.0, 8.0]},
        {"sample_id": "TCGA-005", "tumor_type": "PRAD", "response_label": "Responder", "expression_vector": [9.0, 10.0]},
    ]
    with open(Path(temp_dir) / "data" / "processed" / "tcga_samples.json", "w") as f:
        json.dump(tcga_samples, f)
    
    # Mock GEO samples (only 1 valid dataset)
    geo_samples = [
        {"sample_id": "GEO-001", "tumor_type": "BRCA", "response_label": "Responder", "expression_vector": [1.0, 2.0]},
        {"sample_id": "GEO-002", "tumor_type": "BRCA", "response_label": "NonResponder", "expression_vector": [3.0, 4.0]},
    ]
    with open(Path(temp_dir) / "data" / "processed" / "geo_samples.json", "w") as f:
        json.dump(geo_samples, f)
    
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_project_dir_missing_files():
    """Create a temporary project with missing data files."""
    temp_dir = tempfile.mkdtemp()
    (Path(temp_dir) / "data").mkdir(parents=True)
    (Path(temp_dir) / "data" / "raw").mkdir(parents=True)
    (Path(temp_dir) / "data" / "processed").mkdir(parents=True)
    (Path(temp_dir) / "results").mkdir(parents=True)
    (Path(temp_dir) / "state" / "projects").mkdir(parents=True)
    
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_feasibility_gate_ready(temp_project_dir):
    """Test that feasibility gate passes when requirements are met."""
    os.chdir(temp_project_dir)
    
    tcga_count = count_available_tumor_types()
    geo_count = get_valid_geo_count()
    
    assert tcga_count >= 3, f"Expected >= 3 TCGA types, got {tcga_count}"
    assert geo_count >= 2, f"Expected >= 2 GEO datasets, got {geo_count}"
    
    result = write_feasibility_gate_result(temp_project_dir)
    
    gate_file = Path(temp_project_dir) / "data" / "feasibility_gate.json"
    assert gate_file.exists(), "Feasibility gate file should be created"
    
    with open(gate_file) as f:
        gate_data = json.load(f)
    
    assert gate_data["status"] == "ready", f"Expected status 'ready', got '{gate_data['status']}'"
    assert gate_data["tcga_count"] >= 3
    assert gate_data["geo_count"] >= 2


def test_feasibility_gate_halted_tcga(temp_project_dir_insufficient_tcga):
    """Test that feasibility gate halts when TCGA types < 3."""
    os.chdir(temp_project_dir_insufficient_tcga)
    
    tcga_count = count_available_tumor_types()
    geo_count = get_valid_geo_count()
    
    assert tcga_count < 3, f"Expected < 3 TCGA types for this test, got {tcga_count}"
    assert geo_count >= 2, f"Expected >= 2 GEO datasets for this test, got {geo_count}"
    
    # This should write a halted status
    result = write_feasibility_gate_result(temp_project_dir_insufficient_tcga)
    
    gate_file = Path(temp_project_dir_insufficient_tcga) / "data" / "feasibility_gate.json"
    assert gate_file.exists(), "Feasibility gate file should be created"
    
    with open(gate_file) as f:
        gate_data = json.load(f)
    
    assert gate_data["status"] == "halted", f"Expected status 'halted', got '{gate_data['status']}'"
    assert gate_data["reason"] == "insufficient_tcga_types", f"Expected reason 'insufficient_tcga_types', got '{gate_data['reason']}'"
    assert gate_data["tcga_count"] < 3


def test_feasibility_gate_halted_geo(temp_project_dir_insufficient_geo):
    """Test that feasibility gate halts when GEO datasets < 2 (regardless of TCGA count)."""
    os.chdir(temp_project_dir_insufficient_geo)
    
    tcga_count = count_available_tumor_types()
    geo_count = get_valid_geo_count()
    
    assert tcga_count >= 3, f"Expected >= 3 TCGA types for this test, got {tcga_count}"
    assert geo_count < 2, f"Expected < 2 GEO datasets for this test, got {geo_count}"
    
    # This should write a halted status
    result = write_feasibility_gate_result(temp_project_dir_insufficient_geo)
    
    gate_file = Path(temp_project_dir_insufficient_geo) / "data" / "feasibility_gate.json"
    assert gate_file.exists(), "Feasibility gate file should be created"
    
    with open(gate_file) as f:
        gate_data = json.load(f)
    
    assert gate_data["status"] == "halted", f"Expected status 'halted', got '{gate_data['status']}'"
    assert gate_data["reason"] == "insufficient_geo_datasets", f"Expected reason 'insufficient_geo_datasets', got '{gate_data['reason']}'"
    assert gate_data["geo_count"] < 2


def test_feasibility_gate_test_mode(temp_project_dir_insufficient_tcga):
    """Test that feasibility gate passes in TEST_MODE even with insufficient data."""
    os.environ["TEST_MODE"] = "True"
    try:
        os.chdir(temp_project_dir_insufficient_tcga)
        
        tcga_count = count_available_tumor_types()
        geo_count = get_valid_geo_count()
        
        assert tcga_count < 3, f"Expected < 3 TCGA types for this test, got {tcga_count}"
        
        # In TEST_MODE, should still write 'ready'
        result = write_feasibility_gate_result(temp_project_dir_insufficient_tcga)
        
        gate_file = Path(temp_project_dir_insufficient_tcga) / "data" / "feasibility_gate.json"
        assert gate_file.exists(), "Feasibility gate file should be created"
        
        with open(gate_file) as f:
            gate_data = json.load(f)
        
        assert gate_data["status"] == "ready", f"Expected status 'ready' in TEST_MODE, got '{gate_data['status']}'"
        assert gate_data.get("test_mode", False) is True
    finally:
        os.environ.pop("TEST_MODE", None)


def test_feasibility_gate_missing_files(temp_project_dir_missing_files):
    """Test that feasibility gate handles missing data files gracefully."""
    os.chdir(temp_project_dir_missing_files)
    
    tcga_count = count_available_tumor_types()
    geo_count = get_valid_geo_count()
    
    assert tcga_count == 0, f"Expected 0 TCGA types, got {tcga_count}"
    assert geo_count == 0, f"Expected 0 GEO datasets, got {geo_count}"
    
    # This should write a halted status
    result = write_feasibility_gate_result(temp_project_dir_missing_files)
    
    gate_file = Path(temp_project_dir_missing_files) / "data" / "feasibility_gate.json"
    assert gate_file.exists(), "Feasibility gate file should be created"
    
    with open(gate_file) as f:
        gate_data = json.load(f)
    
    assert gate_data["status"] == "halted", f"Expected status 'halted', got '{gate_data['status']}'"
    assert gate_data["reason"] in ["insufficient_tcga_types", "insufficient_geo_datasets"]