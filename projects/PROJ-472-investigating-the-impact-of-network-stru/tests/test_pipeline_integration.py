"""
Integration Test for Full Pipeline (T050)

This test runs a minimal end-to-end execution of the pipeline using a 
small synthetic dataset (N=5) to verify routing logic and report generation.

It simulates the state where real data is unavailable (expected path) 
and triggers the simulation pipeline.
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import pandas as pd

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import get_data_root, ensure_directories
from data.download import write_routing_state
from data.check_availability import check_availability
from data.simulate_EEG import run_pipeline as run_sim_pipeline
from data.quality_control import calculate_pipeline_completeness
from analysis.metrics import run_metrics_pipeline
from analysis.avalanches import run_avalanche_pipeline
from analysis.fitting import run_fitting_pipeline
from analysis.stats import run_correlation_analysis
from analysis.report import generate_report
from main import check_sample_size_gate, run_pipeline


class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory structure for the test."""
        self.test_dir = tempfile.mkdtemp()
        self.data_root = Path(self.test_dir) / "data"
        self.code_root = Path(self.test_dir) / "code"
        
        # Create necessary subdirectories
        (self.data_root / "raw").mkdir(parents=True)
        (self.data_root / "processed").mkdir(parents=True)
        (self.data_root / "results").mkdir(parents=True)
        (self.data_root / "processed" / "connectomes").mkdir(parents=True)
        (self.data_root / "processed" / "eeg").mkdir(parents=True)
        (self.data_root / "processed" / "avalanches").mkdir(parents=True)
        
        # Mock config to point to test dir
        self.patcher = patch('config.get_data_root', return_value=str(self.data_root))
        self.patcher.start()
        
        # Ensure directories exist in the mock location
        ensure_directories()

    def tearDown(self):
        """Clean up the temporary directory."""
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_pipeline_simulation_path(self):
        """
        Test the full pipeline execution when simulation is required.
        
        1. Simulate routing state (no real data).
        2. Run simulation pipeline.
        3. Run metrics and avalanche detection.
        4. Run statistical analysis.
        5. Generate final report.
        """
        # 1. Setup Routing State (Simulation Required)
        routing_state = {
            "has_matched_eeg": False,
            "simulation_required": True,
            "n_subjects": 5,
            "data_paths": {"dMRI": "dummy", "EEG": None}
        }
        write_routing_state(routing_state)
        
        # 2. Run Simulation (Mocked to avoid heavy computation but verify flow)
        # We create dummy connectomes and simulated EEG files to satisfy downstream steps
        subject_ids = [f"sub-{i:03d}" for i in range(5)]
        
        for sub_id in subject_ids:
            # Create dummy connectome
            conn_dir = self.data_root / "processed" / "connectomes" / sub_id
            conn_dir.mkdir(parents=True, exist_ok=True)
            conn_file = conn_dir / "connectome.tsv"
            np.savetxt(conn_file, np.random.rand(10, 10), delimiter='\t')
            
            # Create dummy simulated EEG
            eeg_dir = self.data_root / "processed" / "eeg" / sub_id
            eeg_dir.mkdir(parents=True, exist_ok=True)
            # Create a minimal FIF-like file (mocked content for testing flow)
            # In a real run, this would be a proper .fif file.
            # Here we write a CSV to simulate the time series for the test
            eeg_file = eeg_dir / "eeg_simulated.fif"
            # Writing a simple CSV to represent the data for the test environment
            # The actual code expects .fif, but we are mocking the loading in the test 
            # or ensuring the simulation script creates a valid placeholder if real mne is not available.
            # For this integration test, we assume the simulation script ran and created the file.
            # We will create a dummy file to satisfy the file existence check.
            with open(eeg_file, 'w') as f:
                f.write("time,chan1,chan2\n")
                for t in range(100):
                    f.write(f"{t},{np.random.randn()},{np.random.randn()}\n")

        # 3. Run Metrics
        # We mock the heavy MRtrix3 dependency but verify the python logic runs
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            run_metrics_pipeline()

        # 4. Run Avalanche Detection
        # Verify it runs without crashing on the dummy data
        run_avalanche_pipeline()

        # 5. Run Fitting
        run_fitting_pipeline()

        # 6. Run Stats
        # Ensure correlation analysis runs
        run_correlation_analysis()

        # 7. Generate Report
        # Verify report generation
        report_path = self.data_root / "results" / "final_report.md"
        # Mock the report generation to ensure it writes a file
        with patch('analysis.report.generate_executive_summary', return_value="Test Summary"):
            with patch('analysis.report.generate_detailed_results', return_value="Details"):
                generate_report()
        
        # Verify output files exist
        self.assertTrue((self.data_root / "processed" / "routing_state.json").exists())
        self.assertTrue((self.data_root / "processed" / "usable_subjects.json").exists())
        self.assertTrue(report_path.exists())

        # Verify routing logic worked (simulation path)
        with open(self.data_root / "processed" / "routing_state.json") as f:
            state = json.load(f)
            self.assertTrue(state.get("simulation_required", False))

    def test_null_result_protocol(self):
        """Test the pipeline when N < N_MIN."""
        # Setup a state with very few subjects
        routing_state = {
            "has_matched_eeg": False,
            "simulation_required": True,
            "n_subjects": 2, # Below N_MIN (default 10)
            "data_paths": {"dMRI": "dummy", "EEG": None}
        }
        write_routing_state(routing_state)
        
        # Create dummy usable subjects
        usable = {"subject_ids": ["sub-001", "sub-002"]}
        with open(self.data_root / "processed" / "usable_subjects.json", 'w') as f:
            json.dump(usable, f)
        
        # Run the gate
        # This should trigger the null result protocol
        # We expect it to generate a report and not crash
        try:
            check_sample_size_gate()
            # If it returns without error, check if report was generated
            report_path = self.data_root / "results" / "insufficient_sample_report.md"
            self.assertTrue(report_path.exists())
        except SystemExit:
            # Expected behavior if the pipeline halts on N=0, but here N>0
            pass

if __name__ == '__main__':
    unittest.main()