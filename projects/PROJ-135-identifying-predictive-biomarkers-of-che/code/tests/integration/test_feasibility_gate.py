"""
Integration test for Data Feasibility Gate logic (T014).
Verifies that data/feasibility_gate.json is written correctly in specific scenarios.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_acquisition import run_data_feasibility_gate, write_feasibility_gate_result, get_project_root

class TestFeasibilityGate:
    """Tests for the Data Feasibility Gate logic."""

    def setup_method(self):
        """Set up temporary directories and files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary directories
        data_dir = Path(self.temp_dir) / "data"
        data_dir.mkdir()
        state_dir = Path(self.temp_dir) / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        # Create a mock state file
        state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
        with open(state_file, 'w') as f:
            f.write("artifact_hashes: {}\n")

    def teardown_method(self):
        """Clean up temporary directories."""
        os.chdir(self.original_cwd)
        # Note: We don't remove temp_dir to allow inspection of outputs if needed
        # But for clean tests, we could use shutil.rmtree(self.temp_dir)

    def _get_gate_file_path(self):
        """Helper to get the path to the feasibility gate JSON."""
        return Path(self.temp_dir) / "data" / "feasibility_gate.json"

    def test_tcga_insufficient_halts(self):
        """
        Test Case 1: TCGA < 3.
        Expected: write status='halted', reason='insufficient_tcga_types' and return False.
        """
        # Run gate with TCGA=2, GEO=5 (GEO is enough, but TCGA fails)
        result = run_data_feasibility_gate(tcga_count=2, geo_count=5)
        
        # Assert return value
        assert result is False, "Pipeline should halt if TCGA < 3"
        
        # Assert file content
        gate_file = self._get_gate_file_path()
        assert gate_file.exists(), "feasibility_gate.json should be created"
        
        with open(gate_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "halted", f"Expected status 'halted', got {data['status']}"
        assert data["reason"] == "insufficient_tcga_types", f"Expected reason 'insufficient_tcga_types', got {data['reason']}"

    def test_geo_insufficient_proceeds(self):
        """
        Test Case 2: TCGA >= 3 AND GEO < 2.
        Expected: write status='halted', reason='insufficient_geo_datasets' and return True (proceed).
        """
        # Run gate with TCGA=3, GEO=1
        result = run_data_feasibility_gate(tcga_count=3, geo_count=1)
        
        # Assert return value
        assert result is True, "Pipeline should proceed if TCGA >= 3 even if GEO < 2"
        
        # Assert file content
        gate_file = self._get_gate_file_path()
        assert gate_file.exists(), "feasibility_gate.json should be created"
        
        with open(gate_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "halted", f"Expected status 'halted', got {data['status']}"
        assert data["reason"] == "insufficient_geo_datasets", f"Expected reason 'insufficient_geo_datasets', got {data['reason']}"

    def test_both_sufficient_proceeds(self):
        """
        Test Case 3: TCGA >= 3 AND GEO >= 2.
        Expected: write status='ready' and return True.
        """
        # Run gate with TCGA=4, GEO=3
        result = run_data_feasibility_gate(tcga_count=4, geo_count=3)
        
        # Assert return value
        assert result is True, "Pipeline should proceed if both counts are sufficient"
        
        # Assert file content
        gate_file = self._get_gate_file_path()
        assert gate_file.exists(), "feasibility_gate.json should be created"
        
        with open(gate_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "ready", f"Expected status 'ready', got {data['status']}"
        assert "reason" in data, "Reason should be present"
        assert data["reason"] == "sufficient_data", f"Expected reason 'sufficient_data', got {data['reason']}"

    def test_boundary_tcga_exact_min(self):
        """
        Test Case 4: TCGA exactly equal to MIN_TCGA_TYPES (3).
        Expected: Proceed if GEO is sufficient.
        """
        result = run_data_feasibility_gate(tcga_count=3, geo_count=2)
        assert result is True
        
        gate_file = self._get_gate_file_path()
        with open(gate_file, 'r') as f:
            data = json.load(f)
        assert data["status"] == "ready"

    def test_boundary_geo_exact_min(self):
        """
        Test Case 5: GEO exactly equal to MIN_GEO_DATASETS (2).
        Expected: Proceed if TCGA is sufficient.
        """
        result = run_data_feasibility_gate(tcga_count=3, geo_count=2)
        assert result is True
        
        gate_file = self._get_gate_file_path()
        with open(gate_file, 'r') as f:
            data = json.load(f)
        assert data["status"] == "ready"