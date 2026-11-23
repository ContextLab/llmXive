import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd

from code.data.calculate_ingest_metrics import calculate_linked_metadata_percentage, write_metrics_to_json

def test_calculate_linked_metadata_percentage():
    """Test the calculation of linked metadata percentage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a mock linked_trials.csv
        linked_data = {
            'trial_id': ['t1', 't2', 't3'],
            'response_time': [0.5, 0.6, 0.7],
            'stimulus_id': ['s1', 's2', 's3'],
            'prime_condition': ['p1', 'p2', 'p3'],
            'participant_id': ['pid1', 'pid2', 'pid3']
        }
        linked_df = pd.DataFrame(linked_data)
        linked_path = tmpdir_path / "linked_trials.csv"
        linked_df.to_csv(linked_path, index=False)

        # Create a mock raw data directory with CSVs
        raw_dir = tmpdir_path / "raw"
        raw_dir.mkdir()
        raw_data = {
            'trial_id': ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 't10'],
            'response_time': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
            'stimulus_id': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'],
            'prime_condition': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10'],
            'participant_id': ['pid1', 'pid2', 'pid3', 'pid4', 'pid5', 'pid6', 'pid7', 'pid8', 'pid9', 'pid10']
        }
        raw_df = pd.DataFrame(raw_data)
        raw_path = raw_dir / "raw_trials.csv"
        raw_df.to_csv(raw_path, index=False)

        # Calculate percentage
        percentage = calculate_linked_metadata_percentage(
            linked_trials_path=str(linked_path),
            total_trials_path=str(raw_dir)
        )

        # Expected: 3 linked / 10 total = 30%
        assert abs(percentage - 30.0) < 0.01, f"Expected 30.0%, got {percentage}%"

def test_write_metrics_to_json():
    """Test writing metrics to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        output_path = tmpdir_path / "metrics.json"
        
        metrics = {
            "linked_metadata_percentage": 30.0,
            "check_id": "SC-001"
        }

        write_metrics_to_json(metrics, str(output_path))

        assert output_path.exists(), "Output JSON file was not created."
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["linked_metadata_percentage"] == 30.0
        assert data["check_id"] == "SC-001"

def test_missing_linked_trials():
    """Test behavior when linked trials file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create raw data
        raw_dir = tmpdir_path / "raw"
        raw_dir.mkdir()
        raw_data = {'trial_id': ['t1', 't2']}
        pd.DataFrame(raw_data).to_csv(raw_dir / "raw.csv", index=False)

        # Call with non-existent linked path
        percentage = calculate_linked_metadata_percentage(
            linked_trials_path=str(tmpdir_path / "nonexistent.csv"),
            total_trials_path=str(raw_dir)
        )

        # Should return 0.0
        assert percentage == 0.0

def test_missing_total_trials():
    """Test behavior when total trials file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create linked data
        linked_data = {'trial_id': ['t1']}
        pd.DataFrame(linked_data).to_csv(tmpdir_path / "linked.csv", index=False)

        # Call with non-existent raw path
        with pytest.raises(FileNotFoundError):
            calculate_linked_metadata_percentage(
                linked_trials_path=str(tmpdir_path / "linked.csv"),
                total_trials_path=str(tmpdir_path / "nonexistent")
            )