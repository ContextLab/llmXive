import pytest
import os
import json
import yaml
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Import functions to test
from code.ingest import (
    save_checksums,
    calculate_file_hash,
    decide_design_branch,
    verify_conditions_present,
    check_participant_overlap
)
from code.config import get_path

class TestChecksums:
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file with known content."""
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("test content for checksum")
        return str(file_path)

    @pytest.fixture
    def temp_state_file(self, tmp_path):
        """Create a temporary state file."""
        state_path = tmp_path / "state.yaml"
        state_path.write_text("")
        return str(state_path)

    def test_calculate_file_hash(self, temp_file):
        """Test SHA-256 calculation."""
        hash_val = calculate_file_hash(temp_file)
        assert len(hash_val) == 64  # SHA-256 hex length
        assert isinstance(hash_val, str)

    def test_save_checksums_creates_entry(self, temp_file, temp_state_file):
        """Test that save_checksums creates the correct entry in state file."""
        dataset_id = "ds000208"
        save_checksums(dataset_id, temp_file, temp_state_file)
        
        with open(temp_state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        assert 'artifact_hashes' in state
        assert dataset_id in state['artifact_hashes']
        assert 'sha256' in state['artifact_hashes'][dataset_id]
        assert 'size_bytes' in state['artifact_hashes'][dataset_id]
        assert 'updated_at' in state

    def test_save_checksums_updates_existing(self, temp_file, temp_state_file):
        """Test that save_checksums updates an existing entry."""
        dataset_id = "ds000208"
        
        # Create initial state
        initial_state = {
            'artifact_hashes': {
                'ds000001': {'sha256': 'old_hash', 'size_bytes': 100}
            },
            'updated_at': '2023-01-01T00:00:00Z'
        }
        with open(temp_state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        save_checksums(dataset_id, temp_file, temp_state_file)
        
        with open(temp_state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        assert 'ds000001' in state['artifact_hashes']
        assert state['artifact_hashes']['ds000001']['sha256'] == 'old_hash'
        assert dataset_id in state['artifact_hashes']
        assert state['artifact_hashes'][dataset_id]['sha256'] != 'old_hash'

class TestDesignBranch:
    def test_within_subjects_decision(self):
        """Test decision when single cohort and overlap."""
        result = decide_design_branch(
            validation_passed=True,
            condition_report={'rejection_present': True, 'control_present': True},
            single_cohort=True,
            overlap=True
        )
        assert result['design_type'] == 'Within-Subjects'
        assert result['branch'] == 'single_cohort'

    def test_between_subjects_decision_no_overlap(self):
        """Test decision when single cohort but no overlap."""
        result = decide_design_branch(
            validation_passed=True,
            condition_report={'rejection_present': True, 'control_present': True},
            single_cohort=True,
            overlap=False
        )
        assert result['design_type'] == 'Between-Subjects'
        assert result['branch'] == 'between_subjects'

    def test_halt_on_validation_failure(self):
        """Test decision when validation fails."""
        result = decide_design_branch(
            validation_passed=False,
            condition_report={},
            single_cohort=True,
            overlap=True
        )
        assert result['branch'] == 'halt'
        assert result['design_type'] is None

class TestConditions:
    def test_verify_conditions_present_valid(self):
        """Test condition verification with valid data."""
        df = pd.DataFrame({
            'Condition': ['Rejection', 'Control', 'Rejection'],
            'Reaction Time': [200, 300, 250],
            'Mood': [1, 2, 1]
        })
        report = verify_conditions_present(df)
        assert report['rejection_present'] is True
        assert report['control_present'] is True
        assert report['status'] == 'valid'

    def test_verify_conditions_present_missing(self):
        """Test condition verification with missing condition."""
        df = pd.DataFrame({
            'Condition': ['Rejection', 'Rejection', 'Rejection'],
            'Reaction Time': [200, 300, 250],
            'Mood': [1, 2, 1]
        })
        report = verify_conditions_present(df)
        assert report['rejection_present'] is True
        assert report['control_present'] is False
        assert report['status'] == 'invalid'

class TestOverlap:
    def test_check_participant_overlap_true(self):
        """Test overlap detection with shared IDs."""
        df = pd.DataFrame({
            'Participant': [1, 1, 2, 2],
            'Condition': ['Rejection', 'Control', 'Rejection', 'Control']
        })
        assert check_participant_overlap(df) is True

    def test_check_participant_overlap_false(self):
        """Test overlap detection with no shared IDs."""
        df = pd.DataFrame({
            'Participant': [1, 1, 2, 2],
            'Condition': ['Rejection', 'Rejection', 'Control', 'Control']
        })
        assert check_participant_overlap(df) is False
