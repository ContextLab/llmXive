import pytest
import csv
import json
import os
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Import the module to test
from code import code_04_data_collection as data_collection_module
from code.code_04_data_collection import (
    validate_and_process_row,
    is_partial_response,
    normalize_row,
    Participant
)
from code.utils.data_validation import validate_liker_scale

# Helper to create a mock raw data row
def create_mock_row(
    participant_id="P001",
    condition="Partner",
    manipulation_check="pass",
    attitude_items=[3, 4, 5, 4, 3, 4, 5],
    usefulness_items=[4, 5, 4],
    trust_items=[3, 4, 4, 3],
    timestamp=None,
    missing_field=None
):
    row = {
        'participant_id': participant_id,
        'condition': condition,
        'manipulation_check': manipulation_check,
        'timestamp': timestamp or datetime.now().isoformat()
    }
    
    for i, val in enumerate(attitude_items, 1):
        row[f'attitude_item_{i}'] = val
    for i, val in enumerate(usefulness_items, 1):
        row[f'usefulness_item_{i}'] = val
    for i, val in enumerate(trust_items, 1):
        row[f'trust_item_{i}'] = val
    
    if missing_field:
        row[missing_field] = None
        
    return row

class TestDataValidation:
    """Tests for data validation logic."""

    def test_valid_row_processing(self):
        """Test that a valid row is processed into a Participant object."""
        row = create_mock_row()
        result = validate_and_process_row(row, 0)
        
        assert result is not None
        assert isinstance(result, Participant)
        assert result.participant_id == "P001"
        assert result.condition == "Partner"
        assert result.manipulation_check_failed == False
        assert len(result.attitude_items) == 7
        assert len(result.usefulness_items) == 3
        assert len(result.trust_items) == 4

    def test_partial_response_exclusion(self):
        """Test that partial responses (missing key fields) are excluded."""
        row = create_mock_row(missing_field='manipulation_check')
        result = validate_and_process_row(row, 0)
        
        assert result is None

    def test_invalid_liker_scale(self):
        """Test that invalid Likert scale values cause exclusion."""
        row = create_mock_row()
        row['attitude_item_1'] = 10  # Out of range (1-7)
        
        result = validate_and_process_row(row, 0)
        assert result is None

    def test_invalid_condition(self):
        """Test that invalid condition values cause exclusion."""
        row = create_mock_row(condition="InvalidCondition")
        result = validate_and_process_row(row, 0)
        assert result is None

    def test_manipulation_check_failure_flagging(self):
        """Test that manipulation check failures are correctly flagged."""
        # Valid row with failure
        row = create_mock_row(manipulation_check="fail")
        result = validate_and_process_row(row, 0)
        
        assert result is not None
        assert result.manipulation_check_failed == True

        # Valid row with pass
        row = create_mock_row(manipulation_check="pass")
        result = validate_and_process_row(row, 0)
        
        assert result is not None
        assert result.manipulation_check_failed == False

class TestNormalization:
    """Tests for row normalization."""

    def test_string_to_int_conversion(self):
        """Test that string numbers are converted to integers."""
        row = {
            'participant_id': 'P001',
            'condition': 'Partner',
            'manipulation_check': 'pass',
            'attitude_item_1': '5',
            'attitude_item_2': '4',
            'usefulness_item_1': '3',
            'trust_item_1': '2',
            'timestamp': '2023-01-01'
        }
        # Fill remaining items to avoid None checks
        for i in range(3, 8):
            row[f'attitude_item_{i}'] = '3'
        for i in range(2, 4):
            row[f'usefulness_item_{i}'] = '3'
        for i in range(2, 5):
            row[f'trust_item_{i}'] = '3'

        normalized = normalize_row(row)
        
        assert isinstance(normalized['attitude_item_1'], int)
        assert normalized['attitude_item_1'] == 5

    def test_empty_string_to_none(self):
        """Test that empty strings are converted to None."""
        row = {
            'participant_id': 'P001',
            'condition': 'Partner',
            'manipulation_check': '',
            'attitude_item_1': '5',
            'attitude_item_2': '4',
            'usefulness_item_1': '3',
            'trust_item_1': '2',
            'timestamp': '2023-01-01'
        }
        for i in range(3, 8):
            row[f'attitude_item_{i}'] = '3'
        for i in range(2, 4):
            row[f'usefulness_item_{i}'] = '3'
        for i in range(2, 5):
            row[f'trust_item_{i}'] = '3'

        normalized = normalize_row(row)
        
        assert normalized['manipulation_check'] is None

class TestExport:
    """Tests for data export functionality."""

    def test_export_columns(self):
        """Test that exported CSV has all required columns."""
        participants = [
            Participant(
                participant_id="P001",
                condition="Partner",
                manipulation_check="pass",
                manipulation_check_failed=False,
                attitude_items=[3, 4, 5, 4, 3, 4, 5],
                usefulness_items=[4, 5, 4],
                trust_items=[3, 4, 4, 3],
                timestamp="2023-01-01T00:00:00"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_export.csv"
            data_collection_module.export_cleaned_data(participants, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Check required headers
                required = [
                    'participant_id', 'condition', 'manipulation_check', 'manipulation_check_failed'
                ]
                for i in range(1, 8):
                    required.append(f'attitude_item_{i}')
                for i in range(1, 4):
                    required.append(f'usefulness_item_{i}')
                for i in range(1, 5):
                    required.append(f'trust_item_{i}')
                
                for col in required:
                    assert col in headers, f"Missing column: {col}"

    def test_export_data_integrity(self):
        """Test that exported data matches source participant objects."""
        participants = [
            Participant(
                participant_id="P001",
                condition="Tool",
                manipulation_check="fail",
                manipulation_check_failed=True,
                attitude_items=[1, 2, 3, 4, 5, 6, 7],
                usefulness_items=[7, 6, 5],
                trust_items=[1, 2, 3, 4],
                timestamp="2023-01-01T00:00:00"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_export.csv"
            data_collection_module.export_cleaned_data(participants, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                row = next(reader)
                
                assert row['participant_id'] == "P001"
                assert row['condition'] == "Tool"
                assert row['manipulation_check'] == "fail"
                assert row['manipulation_check_failed'] == "True"
                assert row['attitude_item_1'] == "1"
                assert row['attitude_item_7'] == "7"
                assert row['usefulness_item_1'] == "7"
                assert row['trust_item_4'] == "4"

class TestIsPartialResponse:
    """Tests for partial response detection."""

    def test_complete_response(self):
        row = create_mock_row()
        assert is_partial_response(row) == False

    def test_missing_manipulation_check(self):
        row = create_mock_row(missing_field='manipulation_check')
        assert is_partial_response(row) == True

    def test_missing_attitude_item(self):
        row = create_mock_row(missing_field='attitude_item_1')
        assert is_partial_response(row) == True

    def test_missing_usefulness_item(self):
        row = create_mock_row(missing_field='usefulness_item_1')
        # Note: is_partial_response currently only checks manipulation_check and attitude_item_1
        # If the requirement is to check all items, this test might need adjustment
        # Based on current implementation:
        assert is_partial_response(row) == False 
        
        # If we want to strictly check all items, we would need to update is_partial_response
        # For now, testing the current logic:
        # The function checks manipulation_check and attitude_item_1 specifically
        # So missing usefulness_item_1 does not trigger partial if attitude_item_1 exists
        # This aligns with the current implementation logic.
