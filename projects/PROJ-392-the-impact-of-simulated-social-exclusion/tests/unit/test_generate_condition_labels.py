"""
Unit tests for generate_condition_labels module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from manipulation.generate_condition_labels import (
    extract_condition_from_participants,
    extract_condition_from_events,
    generate_condition_labels,
    load_participants_tsv,
    load_task_events
)


class TestLoadParticipantsTsv:
    def test_load_valid_participants(self, tmp_path):
        """Test loading a valid participants.tsv file."""
        participants_data = "participant_id\tgroup\nsub-01\texclusion\nsub-02\tinclusion"
        participants_file = tmp_path / "participants.tsv"
        participants_file.write_text(participants_data)
        
        df = load_participants_tsv(participants_file)
        
        assert len(df) == 2
        assert 'participant_id' in df.columns
        assert 'group' in df.columns
        assert df.iloc[0]['participant_id'] == 'sub-01'
    
    def test_missing_file(self, tmp_path):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_participants_tsv(tmp_path / "nonexistent.tsv")


class TestLoadTaskEvents:
    def test_load_tsv_events(self, tmp_path):
        """Test loading events from TSV file."""
        events_data = "onset\tduration\ttrial_type\n0\t2\texclusion\n5\t2\tinclusion"
        events_file = tmp_path / "events.tsv"
        events_file.write_text(events_data)
        
        df = load_task_events(events_file)
        
        assert len(df) == 2
        assert 'trial_type' in df.columns
    
    def test_load_json_events(self, tmp_path):
        """Test loading events from JSON file."""
        events_data = [{"onset": 0, "duration": 2, "trial_type": "exclusion"}]
        events_file = tmp_path / "events.json"
        events_file.write_text(json.dumps(events_data))
        
        df = load_task_events(events_file)
        
        assert len(df) == 1
        assert df.iloc[0]['trial_type'] == 'exclusion'


class TestExtractConditionFromParticipants:
    def test_ds000246_exclusion(self):
        """Test extraction for ds000246 with exclusion group."""
        data = {
            'participant_id': ['sub-01', 'sub-02'],
            'group': ['exclusion', 'inclusion']
        }
        df = pd.DataFrame(data)
        
        result = extract_condition_from_participants(df, 'ds000246')
        
        assert result['sub-01'] == 'exclusion'
        assert result['sub-02'] == 'inclusion'
    
    def test_ds000246_alternative_terms(self):
        """Test extraction with alternative exclusion terms."""
        data = {
            'participant_id': ['sub-01', 'sub-02'],
            'group': ['ostracized', 'control']
        }
        df = pd.DataFrame(data)
        
        result = extract_condition_from_participants(df, 'ds000246')
        
        assert result['sub-01'] == 'exclusion'
        assert result['sub-02'] == 'inclusion'
    
    def test_ds004738_default(self):
        """Test extraction for ds004738 (reward task)."""
        data = {
            'participant_id': ['sub-01'],
            'group': ['control']
        }
        df = pd.DataFrame(data)
        
        result = extract_condition_from_participants(df, 'ds004738')
        
        assert result['sub-01'] == 'inclusion'  # Control group


class TestExtractConditionFromEvents:
    def test_exclusion_events(self):
        """Test extraction when only exclusion events are present."""
        data = {
            'participant_id': ['sub-01', 'sub-01'],
            'trial_type': ['exclusion', 'exclusion']
        }
        df = pd.DataFrame(data)
        
        result = extract_condition_from_events(df, 'ds000246')
        
        assert result['sub-01'] == 'exclusion'
    
    def test_inclusion_events(self):
        """Test extraction when only inclusion events are present."""
        data = {
            'participant_id': ['sub-01', 'sub-01'],
            'trial_type': ['inclusion', 'control']
        }
        df = pd.DataFrame(data)
        
        result = extract_condition_from_events(df, 'ds000246')
        
        assert result['sub-01'] == 'inclusion'
    
    def test_mixed_events_majority_exclusion(self):
        """Test extraction with mixed events, exclusion majority."""
        data = {
            'participant_id': ['sub-01', 'sub-01', 'sub-01'],
            'trial_type': ['exclusion', 'exclusion', 'inclusion']
        }
        df = pd.DataFrame(data)
        
        result = extract_condition_from_events(df, 'ds000246')
        
        assert result['sub-01'] == 'exclusion'


class TestGenerateConditionLabels:
    def test_full_generation(self, tmp_path):
        """Test full condition label generation."""
        # Create mock dataset structure
        dataset_path = tmp_path / "ds000246"
        dataset_path.mkdir()
        
        # Create participants.tsv
        participants_data = "participant_id\tgroup\nsub-01\texclusion\nsub-02\tinclusion"
        (dataset_path / "participants.tsv").write_text(participants_data)
        
        output_path = tmp_path / "output" / "condition_labels.csv"
        
        result_df = generate_condition_labels(dataset_path, 'ds000246', output_path)
        
        assert len(result_df) == 2
        assert 'participant_id' in result_df.columns
        assert 'condition' in result_df.columns
        assert output_path.exists()
    
    def test_missing_participants_file(self, tmp_path):
        """Test handling of missing participants file."""
        dataset_path = tmp_path / "ds000246"
        dataset_path.mkdir()
        
        output_path = tmp_path / "output" / "condition_labels.csv"
        
        # Should not raise, just return empty or default
        result_df = generate_condition_labels(dataset_path, 'ds000246', output_path)
        
        # Output file should be created (even if empty or with defaults)
        assert output_path.exists()