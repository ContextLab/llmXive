import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data_acquisition import run_data_feasibility_gate, write_feasibility_gate_result, _finalize_checksums
from src.config import get_project_root

class TestFeasibilityGateLogic:
    """
    Integration test for T014: Data Feasibility Gate.
    Verifies the logic for TCGA and GEO counts and the resulting exit codes/file states.
    """

    def setup_method(self):
        """Setup temporary directories for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Mock get_project_root to return our temp directory
        self.mock_root_patcher = patch('src.data_acquisition.get_project_root', return_value=self.temp_path)
        self.mock_root = self.mock_root_patcher.start()

        # Ensure data directory exists in temp
        (self.temp_path / "data").mkdir(parents=True, exist_ok=True)
        (self.temp_path / "state" / "projects").mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup temporary directories."""
        self.mock_root_patcher.stop()
        self.temp_dir.cleanup()

    def test_tcga_insufficient_halts(self):
        """
        Test Case: TCGA count < 3.
        Expected: Returns False, writes 'halted' with reason 'insufficient_tcga_types', exits code 1.
        """
        # We test the logic function directly here, not sys.exit
        proceed, status = run_data_feasibility_gate(tcga_count=2, geo_count=5)
        
        assert proceed is False, "Should not proceed if TCGA < 3"
        assert status == "halted_insufficient_tcga"
        
        # Verify file content
        gate_file = self.temp_path / "data" / "feasibility_gate.json"
        assert gate_file.exists(), "Gate file should be created"
        
        with open(gate_file) as f:
            data = json.load(f)
        
        assert data["status"] == "halted"
        assert data["reason"] == "insufficient_tcga_types"
        assert data["tcga_tumor_types_count"] == 2

    def test_geo_insufficient_proceeds_internal_only(self):
        """
        Test Case: TCGA >= 3, GEO < 2.
        Expected: Returns True, writes 'halted' with reason 'insufficient_geo_datasets'.
        Caller (main.py) should interpret this as 'proceed internal only'.
        """
        proceed, status = run_data_feasibility_gate(tcga_count=4, geo_count=1)
        
        assert proceed is True, "Should proceed to internal validation"
        assert status == "proceed_internal_only"
        
        gate_file = self.temp_path / "data" / "feasibility_gate.json"
        assert gate_file.exists()
        
        with open(gate_file) as f:
            data = json.load(f)
        
        assert data["status"] == "halted" # Spec says 'halted' for geo too, but allows proceeding
        assert data["reason"] == "insufficient_geo_datasets"
        assert data["valid_geo_datasets_count"] == 1

    def test_both_sufficient_ready(self):
        """
        Test Case: TCGA >= 3, GEO >= 2.
        Expected: Returns True, status 'ready'.
        """
        proceed, status = run_data_feasibility_gate(tcga_count=5, geo_count=3)
        
        assert proceed is True
        assert status == "ready"
        
        gate_file = self.temp_path / "data" / "feasibility_gate.json"
        assert gate_file.exists()
        
        with open(gate_file) as f:
            data = json.load(f)
        
        assert data["status"] == "ready"
        assert data["reason"] == "all_requirements_met"

    def test_checksums_finalized_on_halt(self):
        """
        Test that checksums are written to state file even when gate halts.
        """
        # Inject a fake checksum
        from src.data_acquisition import _checksums
        _checksums.clear()
        _checksums.append({
            "path": "data/raw/fake_file.txt",
            "algorithm": "sha256",
            "hash": "abc123"
        })

        run_data_feasibility_gate(tcga_count=1, geo_count=5) # Force halt

        state_file = self.temp_path / "state" / "projects" / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
        assert state_file.exists(), "State file should be written even on halt"
        
        content = state_file.read_text()
        assert "artifact_hashes:" in content
        assert "abc123" in content
        
        # Cleanup global state
        _checksums.clear()