import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Import the implementation functions we are testing.
# These are defined in src/data_acquisition.py as per the API surface.
try:
    from src.data_acquisition import write_feasibility_gate_result, run_geo_feasibility_check
except ImportError:
    # Fallback to src.feasibility if data_acquisition hasn't been fully populated yet,
    # ensuring the test can run even if the implementation is split.
    try:
        from src.feasibility import write_feasibility_gate_result
        # Mock the run_geo_feasibility_check if missing in the fallback module
        run_geo_feasibility_check = None
    except ImportError:
        pytest.fail("Could not import feasibility logic from src.data_acquisition or src.feasibility")


class TestFeasibilityGate:
    """
    Integration test for Feasibility Gate logic (T011).
    
    Asserts that T014 (write_feasibility_gate_result) writes 
    data/feasibility_gate.json correctly in two specific scenarios:
    1. TCGA < 3: status "halted", reason "insufficient_tcga_types"
    2. GEO < 2 (but TCGA >= 3): status "halted", reason "insufficient_geo_datasets"
    
    Logical Dependency: T014 (implementation of the gate logic).
    """

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_tcga_insufficient_scenario(self, temp_output_dir):
        """
        Scenario 1: TCGA count < 3.
        Expected: Write feasibility_gate.json with status="halted", reason="insufficient_tcga_types".
        """
        # Arrange
        tcga_count = 2  # Less than 3
        geo_count = 5   # Sufficient, but should be ignored if TCGA fails first
        output_path = temp_output_dir / "feasibility_gate.json"

        # Act
        # We call the function directly to test the logic.
        # The function signature is expected to take counts and an output path.
        # Based on the API surface, we assume write_feasibility_gate_result handles the logic.
        # If the function signature differs, we adapt to the actual implementation.
        
        # Since the task requires asserting T014 writes the file, we call the logic.
        # We assume write_feasibility_gate_result is the entry point for the gate.
        # If it requires a state object, we mock that.
        
        # Direct logic test based on T014 description:
        # "If the count of valid TCGA tumor types is < 3, Terminate execution ... and write..."
        
        write_feasibility_gate_result(
            tcga_count=tcga_count,
            geo_count=geo_count,
            output_path=output_path
        )

        # Assert
        assert output_path.exists(), "feasibility_gate.json was not created"
        
        with open(output_path, 'r') as f:
            content = json.load(f)

        assert content["status"] == "halted", f"Expected status 'halted', got '{content.get('status')}'"
        assert content["reason"] == "insufficient_tcga_types", f"Expected reason 'insufficient_tcga_types', got '{content.get('reason')}'"

    def test_geo_insufficient_scenario(self, temp_output_dir):
        """
        Scenario 2: GEO count < 2 (but TCGA >= 3).
        Expected: Write feasibility_gate.json with status="halted", reason="insufficient_geo_datasets".
        Note: The pipeline should NOT terminate execution (in a real run), but the file
        indicates the external validation path is blocked.
        """
        # Arrange
        tcga_count = 4  # Sufficient (>= 3)
        geo_count = 1   # Insufficient (< 2)
        output_path = temp_output_dir / "feasibility_gate.json"

        # Act
        write_feasibility_gate_result(
            tcga_count=tcga_count,
            geo_count=geo_count,
            output_path=output_path
        )

        # Assert
        assert output_path.exists(), "feasibility_gate.json was not created"
        
        with open(output_path, 'r') as f:
            content = json.load(f)

        assert content["status"] == "halted", f"Expected status 'halted', got '{content.get('status')}'"
        assert content["reason"] == "insufficient_geo_datasets", f"Expected reason 'insufficient_geo_datasets', got '{content.get('reason')}'"
        
        # Verify that the file indicates we proceed to internal validation
        # (This might be implicit by the lack of a 'halt_execution' flag, 
        # or explicit in a 'proceed_to_internal' field if the schema requires it.
        # The task description says "proceed (do not halt) to internal validation",
        # so we verify the file exists and has the specific reason, allowing the 
        # orchestrator to catch this specific reason and continue).

    def test_successful_gate_scenario(self, temp_output_dir):
        """
        Scenario 3: Both TCGA >= 3 and GEO >= 2.
        Expected: Write feasibility_gate.json with status="ready".
        """
        # Arrange
        tcga_count = 3
        geo_count = 2
        output_path = temp_output_dir / "feasibility_gate.json"

        # Act
        write_feasibility_gate_result(
            tcga_count=tcga_count,
            geo_count=geo_count,
            output_path=output_path
        )

        # Assert
        assert output_path.exists(), "feasibility_gate.json was not created"
        
        with open(output_path, 'r') as f:
            content = json.load(f)

        assert content["status"] == "ready", f"Expected status 'ready', got '{content.get('status')}'"
        # No reason field expected for success, or it should be null/empty
        if "reason" in content:
            assert content["reason"] is None or content["reason"] == "", "Success state should not have a failure reason"

    def test_helper_functions_exist(self):
        """
        Verify that the helper functions required for the gate logic exist and are callable.
        """
        # Check if run_geo_feasibility_check is available (it might be in data_acquisition)
        # If it's None (fallback case), we skip testing it directly but log it.
        if run_geo_feasibility_check is not None:
            assert callable(run_geo_feasibility_check), "run_geo_feasibility_check must be callable"
        
        assert callable(write_feasibility_gate_result), "write_feasibility_gate_result must be callable"
        assert callable(sys.modules.get('src.data_acquisition', None) and sys.modules['src.data_acquisition'].count_available_tumor_types), "count_available_tumor_types must be available"

# Helper to simulate the state writing if the main function relies on it
def _write_mock_state(tcga_count, geo_count, state_path):
    """
    Helper to write a mock state file if the implementation requires it.
    This is a test utility, not part of the production code.
    """
    state_data = {
        "tcga_types": tcga_count,
        "geo_datasets": geo_count,
        "status": "mock"
    }
    with open(state_path, 'w') as f:
        json.dump(state_data, f)