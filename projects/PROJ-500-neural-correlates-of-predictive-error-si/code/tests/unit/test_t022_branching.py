import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
from src.data.align import run_pipeline_branching_logic

class TestT022Branching:
    def test_branching_missing_behavioral_logs_stimulus_driven(self, monkeypatch):
        """
        Test that when behavioral logs are missing, the mode defaults to 
        Stimulus-Driven with high probability (we mock the random to force it).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "validation_report.json"
            behavior_path = Path(tmpdir) / "behavioral_logs.csv"
            output_path = Path(tmpdir) / "validation_report.json"

            # Create initial report
            initial_report = {
                "analysis_mode": "error_signal",
                "dataset_info": {"source": "test"},
                "status": "validated"
            }
            with open(report_path, 'w') as f:
                json.dump(initial_report, f)

            # Mock random to force Stimulus-Driven selection
            def mock_random():
                return 0.5 # < 0.8 -> Stimulus-Driven

            monkeypatch.setattr("src.data.align.random.random", mock_random)

            mode = run_pipeline_branching_logic(
                str(report_path), 
                str(behavior_path), # File does not exist
                str(output_path)
            )

            assert mode == "stimulus_driven"
            
            # Verify file update
            with open(output_path, 'r') as f:
                updated_report = json.load(f)
            
            assert updated_report["analysis_mode"] == "stimulus_driven"
            assert "branching_decision" in updated_report
            assert updated_report["branching_decision"]["trigger"] == "missing_behavioral_logs"

    def test_branching_missing_behavioral_logs_error_signal(self, monkeypatch):
        """
        Test that when behavioral logs are missing, the mode can be Error-Signal (low prob).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "validation_report.json"
            behavior_path = Path(tmpdir) / "behavioral_logs.csv"
            output_path = Path(tmpdir) / "validation_report.json"

            initial_report = {
                "analysis_mode": "stimulus_driven",
                "dataset_info": {},
                "status": "validated"
            }
            with open(report_path, 'w') as f:
                json.dump(initial_report, f)

            # Mock random to force Error-Signal selection
            def mock_random():
                return 0.9 # > 0.8 -> Error-Signal

            monkeypatch.setattr("src.data.align.random.random", mock_random)

            mode = run_pipeline_branching_logic(
                str(report_path), 
                str(behavior_path), 
                str(output_path)
            )

            assert mode == "error_signal"

            with open(output_path, 'r') as f:
                updated_report = json.load(f)
            
            assert updated_report["analysis_mode"] == "error_signal"

    def test_branching_behavioral_logs_present_error_signal(self):
        """
        Test that when behavioral logs exist, mode is Error-Signal.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "validation_report.json"
            behavior_path = Path(tmpdir) / "behavioral_logs.csv"
            output_path = Path(tmpdir) / "validation_report.json"

            # Create initial report
            initial_report = {
                "analysis_mode": "stimulus_driven", # Start with opposite to ensure update
                "dataset_info": {},
                "status": "validated"
            }
            with open(report_path, 'w') as f:
                json.dump(initial_report, f)

            # Create mock behavioral data
            df = pd.DataFrame({
                'subject_id': ['sub-001'],
                'block_id': [1],
                'response_correct': [True]
            })
            df.to_csv(behavior_path, index=False)

            mode = run_pipeline_branching_logic(
                str(report_path), 
                str(behavior_path), 
                str(output_path)
            )

            assert mode == "error_signal"

            with open(output_path, 'r') as f:
                updated_report = json.load(f)
            
            assert updated_report["analysis_mode"] == "error_signal"
            assert updated_report["branching_decision"]["trigger"] == "behavioral_logs_present"