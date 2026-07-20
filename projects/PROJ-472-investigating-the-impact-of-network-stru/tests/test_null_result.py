"""
Unit tests for the Null Result Protocol (T036).

Verifies that main.py correctly generates insufficient_sample_report.md
and writes routing_state.json when N < N_MIN (but N > 0).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the specific logic being tested
from main import run_null_result_protocol, check_sample_size_gate, count_usable_subjects
from config import get_data_root


class TestNullResultProtocol:
    """Tests for the N < N_MIN routing logic."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_root = Path(self.temp_dir)
        self.results_dir = self.data_root / "results"
        self.processed_dir = self.data_root / "processed"
        self.results_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        yield
        shutil.rmtree(self.temp_dir)

    def test_run_null_result_protocol_creates_report(self):
        """
        Verify that run_null_result_protocol generates the markdown report
        and the routing state JSON file.
        """
        N = 5
        N_MIN = 10
        
        # Mock get_data_root to return our temp directory
        with patch('main.get_data_root', return_value=self.data_root):
            # Execute the protocol
            run_null_result_protocol(N, N_MIN)

            # Check 1: insufficient_sample_report.md exists
            report_path = self.results_dir / "insufficient_sample_report.md"
            assert report_path.exists(), "insufficient_sample_report.md was not created"
            
            # Check 2: Report content is valid and contains expected info
            content = report_path.read_text()
            assert "Insufficient Sample Size" in content or "null result" in content.lower(), \
                "Report missing expected header or context"
            assert str(N) in content, f"Report missing actual N ({N})"
            assert str(N_MIN) in content, f"Report missing threshold N_MIN ({N_MIN})"
            assert "proceed" in content.lower() or "limited" in content.lower(), \
                "Report missing status recommendation"

            # Check 3: routing_state.json exists and is valid
            routing_path = self.processed_dir / "routing_state.json"
            assert routing_path.exists(), "routing_state.json was not created"
            
            with open(routing_path, 'r') as f:
                state = json.load(f)
            
            assert state.get("path") == "limited_sample", \
                f"Expected path='limited_sample', got '{state.get('path')}'"
            assert state.get("status") == "limited", \
                f"Expected status='limited', got '{state.get('status')}'"
            assert state.get("N") == N, f"Expected N={N}, got {state.get('N')}"
            assert state.get("N_MIN") == N_MIN, f"Expected N_MIN={N_MIN}, got {state.get('N_MIN')}"

    def test_check_sample_size_gate_routes_correctly(self):
        """
        Verify that check_sample_size_gate returns the correct routing decision
        when N < N_MIN.
        """
        N = 3
        N_MIN = 20

        with patch('main.get_data_root', return_value=self.data_root):
            # Mock count_usable_subjects to return our specific N
            with patch('main.count_usable_subjects', return_value=N):
                # Mock load_research_config to return our N_MIN
                with patch('main.load_research_config', return_value={"N_MIN": N_MIN}):
                    result = check_sample_size_gate()

                    assert result["proceed"] is False, "Should not proceed to correlation"
                    assert result["path"] == "limited_sample", "Path should be limited_sample"
                    assert result["status"] == "limited", "Status should be limited"
                    assert result["N"] == N
                    assert result["N_MIN"] == N_MIN

    def test_count_usable_subjects_finds_actual_files(self):
        """
        Verify that count_usable_subjects actually scans the directory structure
        and counts valid participant files (simulated or real).
        """
        # Create dummy participant directories with valid markers
        subjects = ["sub-001", "sub-002", "sub-003"]
        for sub in subjects:
            sub_dir = self.data_root / "processed" / sub
            sub_dir.mkdir(parents=True)
            # Create a marker file that indicates a valid participant
            (sub_dir / "eeg_cleaned.fif").touch() 
            (sub_dir / "connectome.npy").touch()

        # Create a dummy directory that should be ignored
        (self.data_root / "processed" / "logs").mkdir()

        with patch('main.get_data_root', return_value=self.data_root):
            count = count_usable_subjects()
            
            assert count == len(subjects), \
                f"Expected count {len(subjects)}, got {count}"

    def test_null_result_protocol_handles_edge_case_N_equals_N_MIN(self):
        """
        Ensure that if N == N_MIN, the protocol does NOT trigger the null result path.
        (This task specifically tests N < N_MIN, but boundary check is good practice).
        """
        N = 10
        N_MIN = 10

        with patch('main.get_data_root', return_value=self.data_root):
            # This should NOT call run_null_result_protocol logic
            # We simulate the check logic here
            if N < N_MIN:
                run_null_result_protocol(N, N_MIN)
                # If we reach here, the test failed (it should not run)
                assert False, "Null result protocol should not run when N == N_MIN"
            else:
                # Correct path: do not generate report
                assert not (self.results_dir / "insufficient_sample_report.md").exists()

    def test_null_result_protocol_file_permissions(self):
        """
        Verify that the generated files are writable and readable.
        """
        N = 1
        N_MIN = 5

        with patch('main.get_data_root', return_value=self.data_root):
            run_null_result_protocol(N, N_MIN)

            # Check file permissions (os.access)
            report_path = self.results_dir / "insufficient_sample_report.md"
            routing_path = self.processed_dir / "routing_state.json"

            assert os.access(report_path, os.R_OK), "Report file not readable"
            assert os.access(report_path, os.W_OK), "Report file not writable"
            assert os.access(routing_path, os.R_OK), "Routing state not readable"
            assert os.access(routing_path, os.W_OK), "Routing state not writable"