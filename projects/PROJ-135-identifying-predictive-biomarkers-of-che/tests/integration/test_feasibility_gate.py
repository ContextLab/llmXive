"""
Integration test for Feasibility Gate logic (T011b).

This test verifies the behavior of the feasibility gate in src/data_acquisition.py:
1. When TCGA types < 3, the pipeline MUST halt completely (exit code 1).
2. When TCGA types >= 3 but GEO datasets < 2, the pipeline MUST write a 'halted'
   gate with reason 'insufficient_geo_datasets' but proceed with internal validation
   (i.e., not exit with code 1, but signal the state).

It uses mocked data to simulate these conditions without requiring a full data download.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# Note: We are testing the logic in data_acquisition, specifically run_feasibility_gate
# and write_feasibility_gate_result.
# We assume the project structure is: code/code/...
# We need to add the code/code directory to sys.path to import src modules.
project_root = Path(__file__).parent.parent.parent
code_root = project_root / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data_acquisition import run_feasibility_gate, write_feasibility_gate_result
from src.config import get_project_root, ensure_directories


class TestFeasibilityGateLogic:
    """Integration tests for the Feasibility Gate logic."""

    def setup_method(self):
        """Set up temporary directories and files for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.state_dir = Path(self.temp_dir) / "state" / "projects"
        self.data_dir.mkdir(parents=True)
        self.state_dir.mkdir(parents=True)

        # Mock the project root to point to our temp directory for this test
        # We will patch get_project_root to return our temp dir
        self.original_get_project_root = None

    def teardown_method(self):
        """Clean up temporary directories."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _mock_config_paths(self):
        """Patch get_project_root to return our temp directory."""
        def mock_get_project_root():
            return Path(self.temp_dir)
        return patch('src.data_acquisition.get_project_root', mock_get_project_root)

    def test_tcga_types_less_than_3_halts_pipeline(self):
        """
        Verify that if TCGA types < 3, the pipeline halts completely.
        Expected: Exit code 1, feasibility_gate.json status: 'halted', reason: 'insufficient_tcga_types'.
        """
        # Mock the TCGA discovery to return only 2 types
        mock_tcga_types = ["TCGA-BRCA", "TCGA-LUAD"]
        mock_geo_datasets = [] # No GEO datasets needed for this check

        with self._mock_config_paths():
            # Patch the discovery function to return our mock data
            with patch('src.data_acquisition.discover_available_tcga_tumor_types', return_value=mock_tcga_types):
                # Patch the GEO check to return 0 valid datasets (or skip it)
                # The run_feasibility_gate logic should check TCGA first.
                with patch('src.data_acquisition.check_geo_datasets', return_value=(0, [])):
                    with patch('src.data_acquisition.sys.exit') as mock_exit:
                        # We also need to patch write_feasibility_gate_result to capture the call
                        with patch('src.data_acquisition.write_feasibility_gate_result') as mock_write:
                            # Run the gate
                            try:
                                run_feasibility_gate()
                            except SystemExit:
                                # Expected if sys.exit is called
                                pass

                            # Assertions
                            mock_exit.assert_called_once_with(1)
                            mock_write.assert_called_once()
                            call_args = mock_write.call_args
                            # call_args[0] contains positional args: (data_dir, status, reason)
                            assert call_args[0][1] == "halted"
                            assert call_args[0][2] == "insufficient_tcga_types"

    def test_tcga_types_ok_but_geo_less_than_2_proceeds(self):
        """
        Verify that if TCGA types >= 3 but GEO datasets < 2, the pipeline writes 'halted'
        with reason 'insufficient_geo_datasets' and DOES NOT exit with code 1.
        It should proceed (return normally or signal proceed).
        """
        mock_tcga_types = ["TCGA-BRCA", "TCGA-LUAD", "TCGA-COAD"] # 3 types
        mock_geo_datasets = [] # 0 valid datasets

        with self._mock_config_paths():
            with patch('src.data_acquisition.discover_available_tcga_tumor_types', return_value=mock_tcga_types):
                with patch('src.data_acquisition.check_geo_datasets', return_value=(0, [])):
                    with patch('src.data_acquisition.sys.exit') as mock_exit:
                        with patch('src.data_acquisition.write_feasibility_gate_result') as mock_write:
                            # Run the gate
                            result = run_feasibility_gate()

                            # Assertions
                            # sys.exit should NOT be called
                            mock_exit.assert_not_called()

                            # write_feasibility_gate_result should be called with 'halted' and specific reason
                            mock_write.assert_called_once()
                            call_args = mock_write.call_args
                            assert call_args[0][1] == "halted"
                            assert call_args[0][2] == "insufficient_geo_datasets"

                            # The function should return True (or some indicator of proceeding)
                            # Let's assume run_feasibility_gate returns True if it proceeds, False if it halts.
                            # If the implementation doesn't return, we check that it didn't exit.
                            # Based on the task description: "proceed with internal validation only".
                            # We assume the function returns True to indicate "proceed".
                            assert result is True

    def test_tcga_types_ok_and_geo_ok_proceeds(self):
        """
        Verify that if TCGA types >= 3 AND GEO datasets >= 2, the pipeline writes 'ready'.
        """
        mock_tcga_types = ["TCGA-BRCA", "TCGA-LUAD", "TCGA-COAD"]
        mock_geo_datasets = [{"id": "GEO1"}, {"id": "GEO2"}] # 2 valid datasets

        with self._mock_config_paths():
            with patch('src.data_acquisition.discover_available_tcga_tumor_types', return_value=mock_tcga_types):
                with patch('src.data_acquisition.check_geo_datasets', return_value=(2, mock_geo_datasets)):
                    with patch('src.data_acquisition.sys.exit') as mock_exit:
                        with patch('src.data_acquisition.write_feasibility_gate_result') as mock_write:
                            result = run_feasibility_gate()

                            # Assertions
                            mock_exit.assert_not_called()
                            mock_write.assert_called_once()
                            call_args = mock_write.call_args
                            assert call_args[0][1] == "ready"
                            assert call_args[0][2] is None # Or empty string, depending on implementation

                            assert result is True

    def test_write_feasibility_gate_result_creates_correct_file(self):
        """
        Verify that write_feasibility_gate_result correctly writes the JSON file.
        """
        gate_file = self.data_dir / "feasibility_gate.json"

        # Call the function directly
        write_feasibility_gate_result(self.data_dir, "halted", "test_reason")

        # Check file exists
        assert gate_file.exists()

        # Check content
        with open(gate_file, 'r') as f:
            data = json.load(f)

        assert data["status"] == "halted"
        assert data["reason"] == "test_reason"
        assert "timestamp" in data

# Note: The above tests assume that src/data_acquisition.py has the functions:
# - discover_available_tcga_tumor_types
# - check_geo_datasets
# - run_feasibility_gate
# - write_feasibility_gate_result
#
# If these functions are not yet implemented in src/data_acquisition.py,
# this test will fail with ImportError or AttributeError, which is expected
# until the implementation tasks (T012, T013, T014) are completed.
# However, T011b is a test task, and it is acceptable for it to fail if the
# implementation is missing, as long as the test logic itself is correct.
# The task description says: "Verify that the pipeline writes 'halted' gate..."
# This implies we are testing the *behavior* of the pipeline, which requires
# the pipeline code to exist. Since T014 is the implementation of the gate,
# T011b is logically dependent on T014 being implemented.
#
# However, the task list shows T011b as a test task to be implemented.
# In TDD, tests are written first. So we write the test assuming the interface.
# If the implementation is missing, the test will fail, which is the desired
# initial state ("ensure they FAIL before implementation").
#
# Since T014 is not yet marked as completed in the 'completed task ids',
# we expect this test to fail initially. But the test code itself must be correct.
#
# To make the test runnable even if T014 is not fully implemented, we could
# mock the dependencies heavily. The current implementation does that.
#
# One adjustment: The task T014 mentions writing to `data/feasibility_gate.json`.
# Our test uses a temp directory and patches `get_project_root` to point to it.
# This is a valid approach for integration tests.

# Additional note: The task description for T011b mentions:
# "Verify that the pipeline writes 'halted' gate and proceeds with internal validation
# when GEO datasets < 2, and halts completely when TCGA types < 3."
# Our tests cover exactly these two scenarios.

# We also need to ensure that the test file is placed in the correct location:
# tests/integration/test_feasibility_gate.py
# This matches the task description.

# One more thing: The task description says "Integration test".
# Our test mocks the data acquisition functions, which makes it more of a unit test
# for the gate logic. However, it tests the interaction between the gate logic
# and the file system (writing the JSON), so it qualifies as an integration test
# at the module level.

# If the implementation of run_feasibility_gate is not yet complete,
# we might get an AttributeError. To handle this gracefully in the test suite,
# we could catch the exception and mark the test as skipped, but the task
# requires the test to FAIL before implementation, so we let it raise.

# Final check: The test file should be importable and runnable with pytest.
# The structure looks correct.

# One potential issue: The `check_geo_datasets` function might not exist yet.
# We are mocking it, so it should be fine.

# Let's ensure the test file is complete and correct.
# The tests are:
# 1. test_tcga_types_less_than_3_halts_pipeline
# 2. test_tcga_types_ok_but_geo_less_than_2_proceeds
# 3. test_tcga_types_ok_and_geo_ok_proceeds
# 4. test_write_feasibility_gate_result_creates_correct_file

# These cover the requirements.

# We assume the implementation of run_feasibility_gate will:
# - Call discover_available_tcga_tumor_types
# - Call check_geo_datasets (or equivalent logic)
# - Based on counts, call write_feasibility_gate_result and possibly sys.exit
# - Return True if proceeding, False if halted (or similar)

# Our tests verify this behavior by mocking the dependencies.

# The test file is ready.
pass
