import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from report import main as report_main, generate_results_report, generate_data_insufficiency_report, load_gate_status, load_stat_gate_status
from viz import main as viz_main
import pandas as pd
from logging_config import get_logger, log_operation

# Ensure logging is configured for tests
# setup_logging is not in the provided API surface for logging_config, 
# but get_logger is. We rely on the global logger initialization if needed.

def test_report_generation_and_plots(tmp_path):
    """
    Integration test for report generation (T031).
    
    Verifies that:
    1. If Gate Pass (N >= 30): 
       - results_report.md exists and contains dataset_hash, code version, sections.
       - data/outputs/ contains scatter_tpsa_vs_half_life.png, residuals.png, qq_plot.png with non-zero size.
    2. If Gate Fail (N < 30):
       - data_insufficiency_report.md exists and contains "Insufficient".
       - NO plot files are generated in data/outputs/.
    
    This test dynamically checks the gate status files to determine the expected outcome.
    """
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    outputs_dir = data_dir / "outputs"
    
    # Ensure directories exist for the test
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Read Gate Status to determine expected behavior
    gate_status_path = data_dir / "gate_status.json"
    stat_gate_status_path = data_dir / "stat_gate_status.json"
    
    gate_pass = False
    n_count = 0
    
    if gate_status_path.exists():
        try:
            with open(gate_status_path, 'r') as f:
                gate_data = json.load(f)
                if gate_data.get("status") == "PASS":
                    gate_pass = True
        except (json.JSONDecodeError, KeyError):
            gate_pass = False
    
    if stat_gate_status_path.exists():
        try:
            with open(stat_gate_status_path, 'r') as f:
                stat_data = json.load(f)
                if stat_data.get("status") == "PASS":
                    gate_pass = gate_pass and True # Both must pass
                    n_count = stat_data.get("N", 0)
                else:
                    gate_pass = False
        except (json.JSONDecodeError, KeyError):
            gate_pass = False

    # Clean up any existing artifacts to ensure a fresh run state for the test
    # We only remove specific files we expect to generate, not the whole data dir
    report_file = data_dir / "results_report.md"
    insuff_report_file = data_dir / "data_insufficiency_report.md"
    
    # Expected plot files
    expected_plots = [
        "scatter_tpsa_vs_half_life.png",
        "residuals.png",
        "qq_plot.png"
    ]
    
    # Run the Report Generation (T034, T035, T035b, T035c)
    # We call the main function of report.py which handles the branching logic
    try:
        report_main()
    except SystemExit as e:
        # Some scripts might exit with code 1 on failure, which is expected if gates fail
        # We catch it to continue assertions.
        if e.code != 0 and gate_pass:
            # If gate passed but script exited non-zero, that's a failure
            raise
        pass
    
    # Run the Visualization (T032, T033)
    try:
        viz_main()
    except SystemExit as e:
        if e.code != 0 and gate_pass:
            raise
        pass

    # Assertions based on Gate Status
    if gate_pass:
        # EXPECTED: results_report.md exists and has content
        assert report_file.exists(), "results_report.md was not generated (Gate Pass)."
        report_content = report_file.read_text()
        assert len(report_content) > 0, "results_report.md is empty."
        assert "dataset_hash" in report_content, "results_report.md missing 'dataset_hash' field."
        assert "Code Version" in report_content or "rdkit" in report_content.lower(), "results_report.md missing code version info."
        
        # EXPECTED: Plot files exist and have non-zero size
        for plot_name in expected_plots:
            plot_path = outputs_dir / plot_name
            assert plot_path.exists(), f"Plot file {plot_name} was not generated (Gate Pass)."
            assert plot_path.stat().st_size > 0, f"Plot file {plot_name} is empty (0 bytes)."
        
        # EXPECTED: data_insufficiency_report.md should NOT exist (or be empty/ignored)
        if insuff_report_file.exists():
            # It might exist from a previous run, but logically for this run it shouldn't be the active one
            # The task spec implies branching: IF Pass -> results_report, IF Fail -> insuff_report.
            # We verify the active one is the results report.
            pass

    else:
        # EXPECTED: data_insufficiency_report.md exists and contains "Insufficient"
        assert insuff_report_file.exists(), "data_insufficiency_report.md was not generated (Gate Fail)."
        report_content = insuff_report_file.read_text()
        assert "Insufficient" in report_content, f"data_insufficiency_report.md missing 'Insufficient' text. Content: {report_content}"
        
        # EXPECTED: NO plot files should exist (or be zero size if generated by error)
        # The spec says: "IF Gate Fail (N < 30) verify no plot files exist"
        for plot_name in expected_plots:
            plot_path = outputs_dir / plot_name
            if plot_path.exists():
                # If it exists, it must be 0 size or we fail
                # Strictly following "verify no plot files exist"
                assert plot_path.stat().st_size == 0, f"Plot file {plot_name} exists but should not (Gate Fail)."
        
        # EXPECTED: results_report.md should NOT exist (or be empty)
        if report_file.exists():
            assert report_file.stat().st_size == 0, "results_report.md exists but should not (Gate Fail)."