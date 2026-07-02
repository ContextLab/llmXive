"""
Unit tests for generate_condition_labels module.
"""

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from manipulation.generate_condition_labels import (
    load_participants_tsv,
    load_events_json,
    extract_exclusion_labels_from_participants,
    extract_labels_from_events_json,
    generate_condition_labels,
)


class TestLoadParticipantsTsv:
    def test_load_valid_participants_tsv(self, tmp_path):
        """Test loading a valid participants.tsv file."""
        participants_file = tmp_path / 'participants.tsv'
        content = """participant_id\tcondition\tage
        sub-01\texclusion\t25
        sub-02\tinclusion\t30
        sub-03\texclusion\t22"""

        participants_file.write_text(content)

        participants = load_participants_tsv(participants_file)

        assert len(participants) == 3
        assert participants[0]['participant_id'] == 'sub-01'
        assert participants[0]['condition'] == 'exclusion'
        assert participants[1]['condition'] == 'inclusion'

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_participants_tsv(tmp_path / 'nonexistent.tsv')


class TestLoadEventsJson:
    def test_load_valid_events_json(self, tmp_path):
        """Test loading a valid events.json file."""
        events_file = tmp_path / 'events.json'
        events_data = [
            {"onset": 0, "duration": 1, "trial_type": "exclusion"},
            {"onset": 2, "duration": 1, "trial_type": "inclusion"}
        ]

        events_file.write_text(json.dumps(events_data))

        events = load_events_json(events_file)

        assert len(events) == 2
        assert events[0]['trial_type'] == 'exclusion'

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_events_json(tmp_path / 'nonexistent.json')


class TestExtractExclusionLabels:
    def test_extract_from_condition_column(self):
        """Test extraction when 'condition' column exists."""
        participants = [
            {'participant_id': 'sub-01', 'condition': 'exclusion'},
            {'participant_id': 'sub-02', 'condition': 'inclusion'},
            {'participant_id': 'sub-03', 'condition': 'exclusion'}
        ]

        labels = extract_exclusion_labels_from_participants(participants, 'ds000246')

        assert labels['sub-01'] == 'excluded'
        assert labels['sub-02'] == 'included'
        assert labels['sub-03'] == 'excluded'

    def test_extract_from_group_column(self):
        """Test extraction when 'group' column exists."""
        participants = [
            {'participant_id': 'sub-01', 'group': 'excluded'},
            {'participant_id': 'sub-02', 'group': 'included'}
        ]

        labels = extract_exclusion_labels_from_participants(participants, 'ds000246')

        assert labels['sub-01'] == 'excluded'
        assert labels['sub-02'] == 'included'

    def test_extract_unknown_values(self):
        """Test handling of unknown condition values."""
        participants = [
            {'participant_id': 'sub-01', 'condition': 'unknown'},
            {'participant_id': 'sub-02', 'condition': 'exclusion'}
        ]

        labels = extract_exclusion_labels_from_participants(participants, 'ds000246')

        assert 'sub-01' not in labels
        assert labels['sub-02'] == 'excluded'

    def test_no_condition_column(self):
        """Test when no condition column is found."""
        participants = [
            {'participant_id': 'sub-01', 'age': 25},
            {'participant_id': 'sub-02', 'age': 30}
        ]

        labels = extract_exclusion_labels_from_participants(participants, 'ds000246')

        assert len(labels) == 0


class TestGenerateConditionLabels:
    @pytest.fixture
    def sample_dataset_structure(self, tmp_path):
        """Create a sample BIDS dataset structure."""
        # Create participants.tsv
        participants_file = tmp_path / 'participants.tsv'
        participants_content = """participant_id\tcondition
        sub-01\texclusion
        sub-02\tinclusion
        sub-03\texclusion
        sub-04\tinclusion"""
        participants_file.write_text(participants_content)

        return tmp_path

    def test_generate_labels_creates_output(self, sample_dataset_structure, tmp_path):
        """Test that generate_condition_labels creates the output file."""
        output_path = tmp_path / 'output_labels.csv'

        labels = generate_condition_labels(
            sample_dataset_structure,
            'ds000246',
            output_path
        )

        assert output_path.exists()
        assert len(labels) == 4

        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 4
        assert rows[0]['condition'] == 'excluded'
        assert rows[1]['condition'] == 'included'

    def test_generate_labels_missing_participants(self, tmp_path):
        """Test error handling when participants.tsv is missing."""
        output_path = tmp_path / 'output_labels.csv'

        with pytest.raises(FileNotFoundError):
            generate_condition_labels(
                tmp_path,
                'ds000246',
                output_path
            )

    def test_generate_labels_fallback_to_id_pattern(self, tmp_path):
        """Test fallback when no explicit condition labels exist."""
        # Create participants.tsv without condition column
        participants_file = tmp_path / 'participants.tsv'
        participants_content = """participant_id\tage
        sub-01_exclusion\t25
        sub-02_inclusion\t30"""
        participants_file.write_text(participants_content)

        output_path = tmp_path / 'output_labels.csv'

        labels = generate_condition_labels(
            tmp_path,
            'ds000246',
            output_path
        )

        assert output_path.exists()
        assert labels['sub-01_exclusion'] == 'excluded'
        assert labels['sub-02_inclusion'] == 'included'
