"""
Unit tests for the Null Result Protocol (T029c).

These tests verify that the main.py logic correctly handles the sample size gate:
1. Halts execution when N < N_MIN.
2. Generates the 'insufficient_sample_report.md'.
3. Writes the correct state to 'data/processed/routing_state.json'.
4. Prevents correlation analysis from running in the insufficient sample path.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions we are testing from main.py
# Note: We import the specific functions to test them in isolation,
# but we also test the integration via the main entry point logic.
from main import (
    load_research_config,
    count_usable_subjects,
    run_null_result_protocol,
    check_sample_size_gate
)
from config import get_data_root, ensure_directories
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure mimicking the project root."""
    temp_dir = tempfile.mkdtemp(prefix="llmXive_test_")
    # Create necessary subdirectories
    dirs = [
        "data/raw",
        "data/processed",
        "data/processed/avalanches",
        "data/results",
        "data/processed/eeg",
        "data/processed/connectomes"
    ]
    for d in dirs:
        os.makedirs(os.path.join(temp_dir, d), exist_ok=True)

    # Create a mock research_phase_config.json with N_MIN
    config_content = {
        "N_MIN": 5,
        "thresholds": [0.70, 0.75, 0.80]
    }
    config_path = os.path.join(temp_dir, "research_phase_config.json")
    with open(config_path, 'w') as f:
        json.dump(config_content, f)

    # Create a mock routing_state.json to simulate a clean start (or lack thereof)
    # We will let the code create it if it doesn't exist, or overwrite it.
    # Actually, for the test, we want to ensure the directory exists.
    # The code in main.py handles creation if missing.

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_subjects(temp_project_root):
    """Create a set of mock subject directories to simulate available data."""
    # Create 3 mock subjects (N=3)
    # This is less than N_MIN=5, triggering the Null Result Protocol
    subjects = ["sub-001", "sub-002", "sub-003"]
    for sub in subjects:
        # Create QC status file to indicate this subject is "usable"
        # The count_usable_subjects function looks for QC status files
        qc_dir = os.path.join(temp_project_root, "data/processed", "qc")
        os.makedirs(qc_dir, exist_ok=True)
        qc_file = os.path.join(qc_dir, f"{sub}_qc_status.json")
        with open(qc_file, 'w') as f:
            json.dump({"status": "usable", "excluded": False}, f)

        # Create dummy connectome and eeg files to ensure they "exist"
        conn_dir = os.path.join(temp_project_root, "data/processed/connectomes", sub)
        os.makedirs(conn_dir, exist_ok=True)
        with open(os.path.join(conn_dir, "connectome.npy"), 'w') as f:
            f.write("dummy")

        eeg_dir = os.path.join(temp_project_root, "data/processed/eeg", sub)
        os.makedirs(eeg_dir, exist_ok=True)
        with open(os.path.join(eeg_dir, "eeg_cleaned.fif"), 'w') as f:
            f.write("dummy")

    return subjects


@pytest.fixture
def mock_few_subjects(temp_project_root):
    """Create a set of mock subject directories where N < N_MIN."""
    # Create 2 mock subjects (N=2)
    # N_MIN is 5 in the config created by temp_project_root
    subjects = ["sub-001", "sub-002"]
    for sub in subjects:
        qc_dir = os.path.join(temp_project_root, "data/processed", "qc")
        os.makedirs(qc_dir, exist_ok=True)
        qc_file = os.path.join(qc_dir, f"{sub}_qc_status.json")
        with open(qc_file, 'w') as f:
            json.dump({"status": "usable", "excluded": False}, f)

        # Create dummy files
        conn_dir = os.path.join(temp_project_root, "data/processed/connectomes", sub)
        os.makedirs(conn_dir, exist_ok=True)
        with open(os.path.join(conn_dir, "connectome.npy"), 'w') as f:
            f.write("dummy")

        eeg_dir = os.path.join(temp_project_root, "data/processed/eeg", sub)
        os.makedirs(eeg_dir, exist_ok=True)
        with open(os.path.join(eeg_dir, "eeg_cleaned.fif"), 'w') as f:
            f.write("dummy")

    return subjects


@pytest.fixture
def mock_many_subjects(temp_project_root):
    """Create a set of mock subject directories where N >= N_MIN."""
    # Create 6 mock subjects (N=6)
    # N_MIN is 5 in the config created by temp_project_root
    subjects = [f"sub-{i:03d}" for i in range(1, 7)]
    for sub in subjects:
        qc_dir = os.path.join(temp_project_root, "data/processed", "qc")
        os.makedirs(qc_dir, exist_ok=True)
        qc_file = os.path.join(qc_dir, f"{sub}_qc_status.json")
        with open(qc_file, 'w') as f:
            json.dump({"status": "usable", "excluded": False}, f)

        # Create dummy files
        conn_dir = os.path.join(temp_project_root, "data/processed/connectomes", sub)
        os.makedirs(conn_dir, exist_ok=True)
        with open(os.path.join(conn_dir, "connectome.npy"), 'w') as f:
            f.write("dummy")

        eeg_dir = os.path.join(temp_project_root, "data/processed/eeg", sub)
        os.makedirs(eeg_dir, exist_ok=True)
        with open(os.path.join(eeg_dir, "eeg_cleaned.fif"), 'w') as f:
            f.write("dummy")

    return subjects


def test_load_research_config(temp_project_root):
    """Test that load_research_config correctly reads N_MIN."""
    # Patch the get_data_root to return our temp dir
    with patch('main.get_data_root', return_value=temp_project_root):
        config = load_research_config()
        assert config is not None
        assert config.get('N_MIN') == 5


def test_count_usable_subjects(mock_few_subjects, temp_project_root):
    """Test that count_usable_subjects correctly counts subjects with usable QC status."""
    with patch('main.get_data_root', return_value=temp_project_root):
        count = count_usable_subjects()
        assert count == 2  # We created 2 subjects


def test_run_null_result_protocol_generates_report(mock_few_subjects, temp_project_root):
    """
    Test that run_null_result_protocol:
    1. Generates data/results/insufficient_sample_report.md
    2. Writes data/processed/routing_state.json with correct state
    """
    with patch('main.get_data_root', return_value=temp_project_root):
        # Call the protocol
        run_null_result_protocol(2, 5)

        # Check for report file
        report_path = os.path.join(temp_project_root, "data/results/insufficient_sample_report.md")
        assert os.path.exists(report_path), "insufficient_sample_report.md was not generated"

        with open(report_path, 'r') as f:
            content = f.read()
            assert "Insufficient Sample Size" in content
            assert "N = 2" in content
            assert "N_MIN = 5" in content

        # Check for routing state file
        state_path = os.path.join(temp_project_root, "data/processed/routing_state.json")
        assert os.path.exists(state_path), "routing_state.json was not generated"

        with open(state_path, 'r') as f:
            state = json.load(f)
            assert state['path'] == 'insufficient_sample'
            assert state['N'] == 2
            assert state['N_MIN'] == 5
            assert state['status'] == 'halted'


def test_check_sample_size_gate_halt(mock_few_subjects, temp_project_root):
    """
    Test that check_sample_size_gate halts execution when N < N_MIN.
    This simulates the logic in main.py that calls this function.
    """
    with patch('main.get_data_root', return_value=temp_project_root):
        # We expect a SystemExit or a specific exception if the protocol is designed to exit
        # Based on the task description, it should "HALT" and generate reports.
        # In the main.py implementation, this usually involves printing and exiting.
        # We will mock sys.exit to capture the call instead of actually exiting the test runner.
        
        with patch('main.sys.exit') as mock_exit:
            check_sample_size_gate()
            
            # Verify sys.exit was called (indicating the halt)
            mock_exit.assert_called_once()
            
            # Verify the side effects (files generated)
            report_path = os.path.join(temp_project_root, "data/results/insufficient_sample_report.md")
            assert os.path.exists(report_path)
            
            state_path = os.path.join(temp_project_root, "data/processed/routing_state.json")
            assert os.path.exists(state_path)
            
            with open(state_path, 'r') as f:
                state = json.load(f)
                assert state['status'] == 'halted'


def test_check_sample_size_gate_proceed(mock_many_subjects, temp_project_root):
    """
    Test that check_sample_size_gate allows execution to proceed when N >= N_MIN.
    """
    with patch('main.get_data_root', return_value=temp_project_root):
        with patch('main.sys.exit') as mock_exit:
            check_sample_size_gate()
            
            # sys.exit should NOT be called
            mock_exit.assert_not_called()
            
            # Verify the routing state file indicates "proceed"
            state_path = os.path.join(temp_project_root, "data/processed/routing_state.json")
            assert os.path.exists(state_path)
            
            with open(state_path, 'r') as f:
                state = json.load(f)
                assert state['status'] == 'proceed'
                assert state['path'] == 'correlation'


def test_null_result_protocol_with_zero_subjects(temp_project_root):
    """Test behavior when no subjects are found (N=0)."""
    # Ensure no subjects are created
    with patch('main.get_data_root', return_value=temp_project_root):
        with patch('main.sys.exit') as mock_exit:
            # Manually call the protocol with N=0
            run_null_result_protocol(0, 5)
            
            report_path = os.path.join(temp_project_root, "data/results/insufficient_sample_report.md")
            assert os.path.exists(report_path)
            
            with open(report_path, 'r') as f:
                content = f.read()
                assert "N = 0" in content
            
            state_path = os.path.join(temp_project_root, "data/processed/routing_state.json")
            assert os.path.exists(state_path)
            
            with open(state_path, 'r') as f:
                state = json.load(f)
                assert state['N'] == 0
                assert state['status'] == 'halted'

def test_routing_state_overwrite(temp_project_root, mock_few_subjects):
    """Test that the routing state file is overwritten if it already exists."""
    # Create an initial state file
    state_path = os.path.join(temp_project_root, "data/processed/routing_state.json")
    initial_state = {
        "path": "correlation",
        "N": 10,
        "N_MIN": 5,
        "status": "proceed"
    }
    with open(state_path, 'w') as f:
        json.dump(initial_state, f)
    
    with patch('main.get_data_root', return_value=temp_project_root):
        with patch('main.sys.exit'):
            check_sample_size_gate()
            
            # Verify the state was updated to 'halted'
            with open(state_path, 'r') as f:
                state = json.load(f)
                assert state['status'] == 'halted'
                assert state['N'] == 2  # Updated N
                assert state['path'] == 'insufficient_sample'  # Updated path