"""
Tests for T024: Trial Count Validation.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.trial_validation import validate_trial_counts, run_validation_pipeline

class TestTrialValidation:
    
    def setup_method(self):
        """Create temporary directory and files for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = os.path.join(self.temp_dir.name, "features.csv")
        self.config_path = os.path.join(self.temp_dir.name, "config.yaml")

    def teardown_method(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def _create_config(self, aggregation: bool):
        """Helper to create a config file."""
        config_data = {
            "seeds": {"random": 42},
            "thresholds": [0.4, 0.5],
            "paths": {
                "processed_data": os.path.dirname(self.data_path),
                "raw_data": "data/raw"
            },
            "aggregation": aggregation
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def _create_data(self, subject_trial_map: dict):
        """
        Helper to create a features.csv with specific trial counts per subject.
        subject_trial_map: {subject_id: [trial_ids]}
        """
        rows = []
        for sub_id, trials in subject_trial_map.items():
            for trial_id in trials:
                rows.append({
                    'subject_id': sub_id,
                    'trial_id': trial_id,
                    'pupil_mean': 1.0,
                    'search_time': 2.0
                })
        df = pd.DataFrame(rows)
        df.to_csv(self.data_path, index=False)

    def test_all_subjects_pass_no_aggregation(self):
        """Test: All subjects have >= 20 trials, aggregation=False -> Pass."""
        # 2 subjects, 25 trials each
        self._create_config(aggregation=False)
        self._create_data({
            'S01': list(range(25)),
            'S02': list(range(25))
        })
        
        success, details = validate_trial_counts(self.data_path, self.config_path)
        assert success is True
        assert len(details) == 0

    def test_one_subject_fails_no_aggregation_raises(self):
        """Test: One subject has < 20 trials, aggregation=False -> RuntimeError."""
        self._create_config(aggregation=False)
        self._create_data({
            'S01': list(range(25)), # Pass
            'S02': list(range(10))  # Fail
        })
        
        with pytest.raises(RuntimeError) as excinfo:
            validate_trial_counts(self.data_path, self.config_path)
        
        assert "Subject S02" in str(excinfo.value)
        assert "10 trials" in str(excinfo.value)

    def test_fail_subjects_pass_with_aggregation(self):
        """Test: Some subjects fail, but aggregation=True -> Pass (no error)."""
        self._create_config(aggregation=True)
        self._create_data({
            'S01': list(range(25)),
            'S02': list(range(5))  # Fail
        })
        
        success, details = validate_trial_counts(self.data_path, self.config_path)
        assert success is True
        assert len(details) == 1
        assert details[0]['subject_id'] == 'S02'
        assert details[0]['status'] == 'FAIL'

    def test_missing_config_raises_file_not_found(self):
        """Test: Missing config file raises FileNotFoundError."""
        self._create_data({'S01': list(range(25))})
        # Don't create config file
        invalid_path = os.path.join(self.temp_dir.name, "nonexistent.yaml")
        
        with pytest.raises(FileNotFoundError):
            validate_trial_counts(self.data_path, invalid_path)

    def test_missing_data_raises_file_not_found(self):
        """Test: Missing data file raises FileNotFoundError."""
        self._create_config(aggregation=False)
        # Don't create data file
        invalid_data = os.path.join(self.temp_dir.name, "missing.csv")
        
        with pytest.raises(FileNotFoundError):
            validate_trial_counts(invalid_data, self.config_path)

    def test_missing_aggregation_key_defaults_to_false(self):
        """Test: If 'aggregation' key is missing, defaults to False and warns (log)."""
        # Create config without 'aggregation' key
        config_data = {
            "seeds": {"random": 42},
            "paths": {"processed_data": os.path.dirname(self.data_path)}
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        self._create_data({
            'S01': list(range(25)),
            'S02': list(range(10)) # Fail
        })
        
        # Should raise RuntimeError because it defaults to False
        with pytest.raises(RuntimeError) as excinfo:
            validate_trial_counts(self.data_path, self.config_path)
        
        assert "Subject S02" in str(excinfo.value)