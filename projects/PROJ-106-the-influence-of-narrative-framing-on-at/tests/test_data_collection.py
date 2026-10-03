import pytest
import csv
import json
import tempfile
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from dataclasses import dataclass
from typing import List, Dict, Any
from code_04_data_collection import is_partial_response, validate_and_process_row, ingest_and_clean, export_cleaned_data, Participant

class TestDataCollection:
    
    def test_is_partial_response_few_items(self):
        """Test that a response with too few items is marked as partial."""
        row = {
            'participant_id': 'P001',
            'condition': 'partner',
            'manipulation_check': '1',
            'attitude_item_1': '4',
            'attitude_item_2': '5',
            'attitude_item_3': '',
            'attitude_item_4': '',
            'attitude_item_5': '',
            'attitude_item_6': '',
            'attitude_item_7': '',
            'usefulness_item_1': '',
            'usefulness_item_2': '',
            'usefulness_item_3': '',
            'trust_item_1': '',
            'trust_item_2': '',
            'trust_item_3': '',
            'trust_item_4': '',
        }
        # Total items = 14. 50% = 7. Only 2 filled -> partial
        assert is_partial_response(row) is True

    def test_is_partial_response_missing_manipulation_check(self):
        """Test that missing manipulation check marks response as partial."""
        row = {
            'participant_id': 'P002',
            'condition': 'tool',
            'manipulation_check': '',  # Missing
            'attitude_item_1': '4',
            'attitude_item_2': '5',
            'attitude_item_3': '3',
            'attitude_item_4': '4',
            'attitude_item_5': '5',
            'attitude_item_6': '4',
            'attitude_item_7': '3',
            'usefulness_item_1': '5',
            'usefulness_item_2': '4',
            'usefulness_item_3': '5',
            'trust_item_1': '4',
            'trust_item_2': '5',
            'trust_item_3': '4',
            'trust_item_4': '5',
        }
        assert is_partial_response(row) is True

    def test_is_partial_response_complete(self):
        """Test that a complete response is NOT marked as partial."""
        row = {
            'participant_id': 'P003',
            'condition': 'partner',
            'manipulation_check': '1',
            'attitude_item_1': '4',
            'attitude_item_2': '5',
            'attitude_item_3': '3',
            'attitude_item_4': '4',
            'attitude_item_5': '5',
            'attitude_item_6': '4',
            'attitude_item_7': '3',
            'usefulness_item_1': '5',
            'usefulness_item_2': '4',
            'usefulness_item_3': '5',
            'trust_item_1': '4',
            'trust_item_2': '5',
            'trust_item_3': '4',
            'trust_item_4': '5',
        }
        assert is_partial_response(row) is False

    def test_validate_and_process_row_partial(self):
        """Test that partial responses return None."""
        row = {
            'participant_id': 'P004',
            'condition': 'tool',
            'manipulation_check': '',  # Missing
            'attitude_item_1': '4',
            # ... rest missing
        }
        result = validate_and_process_row(row)
        assert result is None

    def test_validate_and_process_row_valid(self):
        """Test that valid responses are processed correctly."""
        row = {
            'participant_id': 'P005',
            'condition': 'partner',
            'manipulation_check': '1',
            'attitude_item_1': '4',
            'attitude_item_2': '5',
            'attitude_item_3': '3',
            'attitude_item_4': '4',
            'attitude_item_5': '5',
            'attitude_item_6': '4',
            'attitude_item_7': '3',
            'usefulness_item_1': '5',
            'usefulness_item_2': '4',
            'usefulness_item_3': '5',
            'trust_item_1': '4',
            'trust_item_2': '5',
            'trust_item_3': '4',
            'trust_item_4': '5',
            'timestamp': '2023-10-01T12:00:00'
        }
        result = validate_and_process_row(row)
        assert result is not None
        assert result.participant_id == 'P005'
        assert result.condition == 'partner'
        assert result.manipulation_check_failed is False
        assert len(result.attitude_items) == 7
        assert result.attitude_items[0] == 4

    def test_ingest_and_clean_filters_partials(self):
        """Test that ingest_and_clean filters out partial responses."""
        raw_data = [
            {
                'participant_id': 'P001',
                'condition': 'partner',
                'manipulation_check': '', # Partial
                'attitude_item_1': '4',
            },
            {
                'participant_id': 'P002',
                'condition': 'tool',
                'manipulation_check': '1',
                'attitude_item_1': '4', 'attitude_item_2': '5', 'attitude_item_3': '3',
                'attitude_item_4': '4', 'attitude_item_5': '5', 'attitude_item_6': '4', 'attitude_item_7': '3',
                'usefulness_item_1': '5', 'usefulness_item_2': '4', 'usefulness_item_3': '5',
                'trust_item_1': '4', 'trust_item_2': '5', 'trust_item_3': '4', 'trust_item_4': '5',
                'timestamp': '2023-10-01T12:00:00'
            }
        ]
        cleaned = ingest_and_clean(raw_data)
        assert len(cleaned) == 1
        assert cleaned[0].participant_id == 'P002'

    def test_export_cleaned_data_creates_file(self):
        """Test that export creates the correct CSV file."""
        participants = [
            Participant(
                participant_id='P001',
                condition='partner',
                manipulation_check='1',
                manipulation_check_failed=False,
                attitude_items=[4, 5, 3, 4, 5, 4, 3],
                usefulness_items=[5, 4, 5],
                trust_items=[4, 5, 4, 5],
                is_partial=False,
                timestamp='2023-10-01T12:00:00'
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'cleaned.csv'
            export_cleaned_data(participants, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['participant_id'] == 'P001'
                assert rows[0]['attitude_item_1'] == '4'
                assert rows[0]['manipulation_check_failed'] == '0'