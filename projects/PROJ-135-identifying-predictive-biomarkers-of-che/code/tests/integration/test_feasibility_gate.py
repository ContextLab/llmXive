import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import shutil

# Import the functions we're testing
from src.data_acquisition import run_feasibility_gate, write_feasibility_gate_result
from src.config import get_project_root

class TestFeasibilityGate:
    """Integration tests for the Data Feasibility Gate logic."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create required subdirectories
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        
        # Create a mock state directory
        state_dir = temp_dir / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        # Create a mock state file
        state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
        with open(state_file, 'w') as f:
            json.dump({"artifact_hashes": {}}, f)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_tcga_insufficient_types(self, temp_project):
        """Test that pipeline halts when TCGA types < 3."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # Simulate insufficient TCGA types (2 types, need 3)
        success = run_feasibility_gate(tcga_types_count=2, geo_count=5, data_dir=data_dir)
        
        # Assert that the function returned False
        assert success is False
        
        # Assert that the feasibility gate JSON was written
        assert output_path.exists(), "feasibility_gate.json should be created"
        
        # Read and verify the content
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted", "Status should be 'halted'"
        assert result["reason"] == "insufficient_tcga_types", "Reason should be 'insufficient_tcga_types'"
    
    def test_geo_insufficient_datasets(self, temp_project):
        """Test that pipeline halts when GEO datasets < 2."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # Simulate sufficient TCGA types but insufficient GEO datasets
        success = run_feasibility_gate(tcga_types_count=5, geo_count=1, data_dir=data_dir)
        
        # Assert that the function returned False
        assert success is False
        
        # Assert that the feasibility gate JSON was written
        assert output_path.exists(), "feasibility_gate.json should be created"
        
        # Read and verify the content
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted", "Status should be 'halted'"
        assert result["reason"] == "insufficient_geo_datasets", "Reason should be 'insufficient_geo_datasets'"
    
    def test_geo_insufficient_with_sufficient_tcga(self, temp_project):
        """Test that GEO gate fails even when TCGA is sufficient."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # TCGA is sufficient (5 >= 3) but GEO is insufficient (0 < 2)
        success = run_feasibility_gate(tcga_types_count=5, geo_count=0, data_dir=data_dir)
        
        assert success is False
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted"
        assert result["reason"] == "insufficient_geo_datasets"
    
    def test_both_gates_pass(self, temp_project):
        """Test that pipeline proceeds when both gates pass."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # Both TCGA and GEO meet requirements
        success = run_feasibility_gate(tcga_types_count=4, geo_count=3, data_dir=data_dir)
        
        # Assert that the function returned True
        assert success is True
        
        # Assert that the feasibility gate JSON was written
        assert output_path.exists(), "feasibility_gate.json should be created"
        
        # Read and verify the content
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "ready", "Status should be 'ready'"
        assert result.get("reason") is None, "Reason should be None when ready"
    
    def test_boundary_tcga_exact_minimum(self, temp_project):
        """Test that exactly 3 TCGA types passes the gate."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # Exactly 3 TCGA types (minimum required)
        success = run_feasibility_gate(tcga_types_count=3, geo_count=2, data_dir=data_dir)
        
        assert success is True
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "ready"
    
    def test_boundary_geo_exact_minimum(self, temp_project):
        """Test that exactly 2 GEO datasets passes the gate."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # Exactly 2 GEO datasets (minimum required)
        success = run_feasibility_gate(tcga_types_count=3, geo_count=2, data_dir=data_dir)
        
        assert success is True
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "ready"
    
    def test_geo_fails_even_with_high_tcga(self, temp_project):
        """Test that GEO gate failure takes precedence even with high TCGA count."""
        data_dir = temp_project / "data"
        output_path = data_dir / "feasibility_gate.json"
        
        # Very high TCGA count but GEO is 0
        success = run_feasibility_gate(tcga_types_count=10, geo_count=0, data_dir=data_dir)
        
        assert success is False
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["status"] == "halted"
        assert result["reason"] == "insufficient_geo_datasets"