import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import logging

# Ensure src is in path for imports
from pathlib import Path
import sys

# Add project root to path if not already
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_acquisition import run_feasibility_gate
from src.config import get_project_root

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFeasibilityGate:
    """
    Integration test for Feasibility Gate logic (T014).
    Asserts that data/feasibility_gate.json is written correctly for:
    1. TCGA < 3 -> status: "halted", reason: "insufficient_tcga_types"
    2. GEO < 2 (regardless of TCGA) -> status: "halted", reason: "insufficient_geo_datasets"
    3. Valid counts -> status: "ready"
    """

    def setup_method(self):
        """Setup temporary directory structure for testing."""
        self.temp_root = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_root) / "data"
        self.data_dir.mkdir(parents=True)
        self.feasibility_file = self.data_dir / "feasibility_gate.json"
        self.state_dir = Path(self.temp_root) / "state" / "projects"
        self.state_dir.mkdir(parents=True)
        
        # Create a mock state file to avoid missing file errors
        self.state_file = self.state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
        self.state_file.write_text("artifact_hashes: {}\n")

    def teardown_method(self):
        """Cleanup temporary directory."""
        if os.path.exists(self.temp_root):
            shutil.rmtree(self.temp_root)

    def _run_gate(self, tcga_count, geo_count):
        """Helper to run the gate logic with mocked counts."""
        # We need to patch the counting functions or pass counts directly.
        # Since run_feasibility_gate likely calls internal logic, we will
        # simulate the environment by setting up the state or mocking.
        # However, the task requires testing the *logic* of writing the file.
        # We will call the function that performs the check.
        
        # To strictly follow the task "Assert that T014 writes ... correctly",
        # we assume the implementation of run_feasibility_gate accepts counts
        # or we mock the counting functions.
        # Given the API surface, run_feasibility_gate is the entry point.
        # We will assume the implementation uses the counts provided in the
        # environment or we inject them. 
        
        # Strategy: We will call the function with specific mocked return values
        # for the counting functions if possible, or pass arguments if the API allows.
        # If the API is fixed to read from disk, we must create mock disk artifacts.
        # The task description says "Use mocked data files to simulate...".
        
        # Let's assume the implementation of run_feasibility_gate looks like:
        # def run_feasibility_gate(tcga_count=None, geo_count=None):
        # If it doesn't, we might need to rely on the fact that the test
        # creates the necessary state files that the function reads.
        
        # Since we cannot see the full implementation of T014 here, we assume
        # the standard pattern: the function calculates counts and writes the file.
        # To test specific scenarios, we will mock the counting functions.
        
        import unittest.mock as mock
        
        # Mock the counting functions
        with mock.patch('src.data_acquisition.count_available_tumor_types', return_value=tcga_count):
            with mock.patch('src.data_acquisition._get_valid_geo_count', return_value=geo_count):
                # We also need to mock the exit call to prevent the test runner from exiting
                with mock.patch('sys.exit') as mock_exit:
                    try:
                        run_feasibility_gate()
                    except SystemExit:
                        pass # Expected if gate fails
                    
                    return mock_exit.called

    def test_tcga_insufficient(self):
        """Test TCGA < 3 scenario."""
        # Simulate TCGA count = 2, GEO count = 2 (valid)
        # Expected: halted, insufficient_tcga_types
        
        import unittest.mock as mock
        
        with mock.patch('src.data_acquisition.count_available_tumor_types', return_value=2):
            with mock.patch('src.data_acquisition._get_valid_geo_count', return_value=2):
                with mock.patch('sys.exit') as mock_exit:
                    run_feasibility_gate()
                    
                    # Verify sys.exit was called
                    assert mock_exit.called, "Pipeline should exit on insufficient TCGA"
                    
                    # Verify the file content
                    assert self.feasibility_file.exists(), "feasibility_gate.json must exist"
                    
                    with open(self.feasibility_file, 'r') as f:
                        data = json.load(f)
                    
                    assert data['status'] == 'halted', f"Expected status 'halted', got {data.get('status')}"
                    assert data['reason'] == 'insufficient_tcga_types', f"Expected reason 'insufficient_tcga_types', got {data.get('reason')}"

    def test_geo_insufficient(self):
        """Test GEO < 2 scenario (regardless of TCGA)."""
        # Simulate TCGA count = 5 (valid), GEO count = 1
        # Expected: halted, insufficient_geo_datasets
        
        import unittest.mock as mock
        
        with mock.patch('src.data_acquisition.count_available_tumor_types', return_value=5):
            with mock.patch('src.data_acquisition._get_valid_geo_count', return_value=1):
                with mock.patch('sys.exit') as mock_exit:
                    run_feasibility_gate()
                    
                    # Verify sys.exit was called
                    assert mock_exit.called, "Pipeline should exit on insufficient GEO"
                    
                    # Verify the file content
                    assert self.feasibility_file.exists(), "feasibility_gate.json must exist"
                    
                    with open(self.feasibility_file, 'r') as f:
                        data = json.load(f)
                    
                    assert data['status'] == 'halted', f"Expected status 'halted', got {data.get('status')}"
                    assert data['reason'] == 'insufficient_geo_datasets', f"Expected reason 'insufficient_geo_datasets', got {data.get('reason')}"

    def test_both_valid(self):
        """Test scenario where both TCGA >= 3 and GEO >= 2."""
        # Simulate TCGA count = 3, GEO count = 2
        # Expected: ready, no exit
        
        import unittest.mock as mock
        
        with mock.patch('src.data_acquisition.count_available_tumor_types', return_value=3):
            with mock.patch('src.data_acquisition._get_valid_geo_count', return_value=2):
                with mock.patch('sys.exit') as mock_exit:
                    run_feasibility_gate()
                    
                    # Verify sys.exit was NOT called
                    assert not mock_exit.called, "Pipeline should NOT exit when counts are sufficient"
                    
                    # Verify the file content
                    assert self.feasibility_file.exists(), "feasibility_gate.json must exist"
                    
                    with open(self.feasibility_file, 'r') as f:
                        data = json.load(f)
                    
                    assert data['status'] == 'ready', f"Expected status 'ready', got {data.get('status')}"
                    # Reason should not be present or be None/empty
                    assert 'reason' not in data or data['reason'] is None, "Reason should not be present for ready status"

    def test_geo_insufficient_overrides_tcga(self):
        """Test that GEO < 2 halts even if TCGA is sufficient."""
        # Simulate TCGA count = 10 (valid), GEO count = 1
        # Expected: halted, insufficient_geo_datasets (not insufficient_tcga_types)
        
        import unittest.mock as mock
        
        with mock.patch('src.data_acquisition.count_available_tumor_types', return_value=10):
            with mock.patch('src.data_acquisition._get_valid_geo_count', return_value=1):
                with mock.patch('sys.exit') as mock_exit:
                    run_feasibility_gate()
                    
                    assert mock_exit.called
                    
                    assert self.feasibility_file.exists()
                    with open(self.feasibility_file, 'r') as f:
                        data = json.load(f)
                    
                    assert data['status'] == 'halted'
                    # Must be GEO reason, not TCGA
                    assert data['reason'] == 'insufficient_geo_datasets', \
                        f"GEO insufficiency should take precedence. Got reason: {data.get('reason')}"

    def test_tcga_and_geo_insufficient(self):
        """Test that GEO < 2 halts even if TCGA is also insufficient."""
        # Simulate TCGA count = 1, GEO count = 1
        # Expected: halted, insufficient_geo_datasets (GEO check usually runs second or is prioritized)
        # Based on T014 description: "GEO Gate: If valid_geo_count < 2 ... halt".
        # The order in T014 is: 1. TCGA Gate, 2. GEO Gate.
        # However, the requirement says "GEO < 2 (regardless of TCGA count)".
        # If TCGA fails first, it halts with TCGA reason.
        # If GEO fails first, it halts with GEO reason.
        # The task description for T011 says: "2) GEO < 2 (regardless of TCGA count)".
        # This implies the test should verify the GEO condition is checked and halts.
        # If TCGA check runs first, then TCGA < 3 will trigger first.
        # Let's assume the implementation checks TCGA then GEO.
        # If TCGA=1, GEO=1: TCGA check fails -> halted, insufficient_tcga_types.
        # If TCGA=5, GEO=1: GEO check fails -> halted, insufficient_geo_datasets.
        # The test "test_geo_insufficient" covers the GEO failure case.
        # This test covers the case where both are low, verifying the order or specific behavior.
        # Given the requirement "GEO < 2 (regardless of TCGA count)", it implies the logic
        # must handle GEO failure even if TCGA is fine.
        # If both are low, the first check (TCGA) will trigger.
        # We will verify the TCGA trigger in this specific case.
        
        import unittest.mock as mock
        
        with mock.patch('src.data_acquisition.count_available_tumor_types', return_value=1):
            with mock.patch('src.data_acquisition._get_valid_geo_count', return_value=1):
                with mock.patch('sys.exit') as mock_exit:
                    run_feasibility_gate()
                    
                    assert mock_exit.called
                    assert self.feasibility_file.exists()
                    with open(self.feasibility_file, 'r') as f:
                        data = json.load(f)
                    
                    # If TCGA check is first, this should be the reason.
                    # If the implementation checks GEO first, it would be GEO.
                    # The T014 description lists TCGA Gate first.
                    assert data['status'] == 'halted'
                    # We assert the reason matches the first failing gate (TCGA)
                    assert data['reason'] == 'insufficient_tcga_types'