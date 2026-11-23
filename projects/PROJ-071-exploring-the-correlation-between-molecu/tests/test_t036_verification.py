"""
Tests for T036: Artifact Verification.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust import path for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_outputs import (
    check_gate_status,
    verify_plot_files,
    verify_report,
    get_data_path,
    get_project_root
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_check_gate_status_missing_file(temp_dir, caplog):
    """Test behavior when gate_status.json is missing."""
    # Mock get_data_path to return temp_dir
    with patch('verify_outputs.get_data_path', return_value=temp_dir):
        result = check_gate_status()
        assert result["status"] == "UNKNOWN"
        assert result["reason"] == "File missing"

def test_check_gate_status_valid_file(temp_dir):
    """Test reading a valid gate status file."""
    gate_file = temp_dir / "gate_status.json"
    data = {"status": "PASS", "N": 50}
    gate_file.write_text(json.dumps(data))

    with patch('verify_outputs.get_data_path', return_value=temp_dir):
        result = check_gate_status()
        assert result["status"] == "PASS"
        assert result["N"] == 50

def test_verify_plots_pass(temp_dir):
    """Test plot verification when Gate is PASS."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir()
    
    # Create dummy plot files
    (outputs_dir / "scatter_tpsa_vs_half_life.png").write_bytes(b"fake_png_data")
    (outputs_dir / "residuals.png").write_bytes(b"fake_png_data")
    (outputs_dir / "qq_plot.png").write_bytes(b"fake_png_data")

    gate_status = {"status": "PASS"}
    
    with patch('verify_outputs.get_data_path', return_value=temp_dir):
        assert verify_plot_files(gate_status) is True

def test_verify_plots_pass_missing_file(temp_dir):
    """Test plot verification when Gate is PASS but a file is missing."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir()
    
    # Create only one plot file
    (outputs_dir / "scatter_tpsa_vs_half_life.png").write_bytes(b"fake_png_data")

    gate_status = {"status": "PASS"}
    
    with patch('verify_outputs.get_data_path', return_value=temp_dir):
        assert verify_plot_files(gate_status) is False

def test_verify_plots_fail_no_files(temp_dir):
    """Test plot verification when Gate is FAIL and no files exist."""
    outputs_dir = temp_dir / "outputs"
    # Do not create outputs_dir or files
    
    gate_status = {"status": "FAIL"}
    
    with patch('verify_outputs.get_data_path', return_value=temp_dir):
        assert verify_plot_files(gate_status) is True

def test_verify_plots_fail_files_exist(temp_dir):
    """Test plot verification when Gate is FAIL but files exist (error case)."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir()
    (outputs_dir / "scatter_tpsa_vs_half_life.png").write_bytes(b"fake_png_data")

    gate_status = {"status": "FAIL"}
    
    with patch('verify_outputs.get_data_path', return_value=temp_dir):
        assert verify_plot_files(gate_status) is False

def test_verify_report_pass(temp_dir):
    """Test report verification when Gate is PASS."""
    report_file = temp_dir / "results_report.md"
    report_file.write_text("# Results\n\nMethodology\n\nResults")
    
    gate_status = {"status": "PASS"}
    
    with patch('verify_outputs.get_project_root', return_value=temp_dir):
        assert verify_report(gate_status) is True

def test_verify_report_pass_missing(temp_dir):
    """Test report verification when Gate is PASS but file is missing."""
    gate_status = {"status": "PASS"}
    
    with patch('verify_outputs.get_project_root', return_value=temp_dir):
        assert verify_report(gate_status) is False

def test_verify_report_fail(temp_dir):
    """Test report verification when Gate is FAIL."""
    report_file = temp_dir / "data"
    report_file.mkdir()
    insuff_file = report_file / "data_insufficiency_report.md"
    insuff_file.write_text("# Data Insufficiency\n\nInsufficient data found.")
    
    gate_status = {"status": "FAIL"}
    
    # Mock get_project_root to return parent of data dir
    with patch('verify_outputs.get_project_root', return_value=temp_dir):
        assert verify_report(gate_status) is True

def test_verify_report_fail_missing(temp_dir):
    """Test report verification when Gate is FAIL but file is missing."""
    gate_status = {"status": "FAIL"}
    
    with patch('verify_outputs.get_project_root', return_value=temp_dir):
        assert verify_report(gate_status) is False
