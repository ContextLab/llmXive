"""
Unit tests for the Data Collection Module (US2)

Tests cover:
- Likert scale validation
- Manipulation check flagging
- Partial response exclusion
- CSV structure validation
"""

import pytest
import csv
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.data_validation import validate_liker_scale
from data_collection import (
    is_partial_response,
    validate_and_process_row,
    normalize_row,
    Participant,
    OUTPUT_COLUMNS
)


class TestLikertValidation:
    def test_valid_liker_scale(self):
        assert validate_liker_scale(1) is True
        assert validate_liker_scale(4) is True
        assert validate_liker_scale(7) is True

    def test_invalid_liker_scale_low(self):
        assert validate_liker_scale(0) is False
        assert validate_liker_scale(-1) is False

    def test_invalid_liker_scale_high(self):
        assert validate_liker_scale(8) is False
        assert validate_liker_scale(100) is False

    def test_non_integer_liker(self):
        assert validate_liker_scale(3.5) is False
        assert validate_liker_scale("3") is False  # String, not int


class TestManipulationCheck:
    def test_correct_partner_frame(self):
        row = {
            "participant_id": "P001",
            "condition": "Partner",
            "manipulation_check_response": "Partner",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        participant = validate_and_process_row(row)
        assert participant is not None
        assert participant.manipulation_check_failed is False

    def test_incorrect_partner_frame(self):
        row = {
            "participant_id": "P002",
            "condition": "Partner",
            "manipulation_check_response": "Tool",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        participant = validate_and_process_row(row)
        assert participant is not None
        assert participant.manipulation_check_failed is True

    def test_correct_tool_frame(self):
        row = {
            "participant_id": "P003",
            "condition": "Tool",
            "manipulation_check_response": "Tool",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        participant = validate_and_process_row(row)
        assert participant is not None
        assert participant.manipulation_check_failed is False

    def test_incorrect_tool_frame(self):
        row = {
            "participant_id": "P004",
            "condition": "Tool",
            "manipulation_check_response": "Partner",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        participant = validate_and_process_row(row)
        assert participant is not None
        assert participant.manipulation_check_failed is True


class TestPartialResponseExclusion:
    def test_complete_response(self):
        row = {
            "participant_id": "P005",
            "condition": "Partner",
            "manipulation_check_response": "Partner",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        assert is_partial_response(row) is False

    def test_missing_attitude_items(self):
        row = {
            "participant_id": "P006",
            "condition": "Partner",
            "manipulation_check_response": "Partner",
            "attitude_item_1": "5",
            "attitude_item_2": "",
            "attitude_item_3": "",
            "attitude_item_4": "",
            "attitude_item_5": "",
            "attitude_item_6": "",
            "attitude_item_7": "",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        assert is_partial_response(row) is True

    def test_missing_condition(self):
        row = {
            "participant_id": "P007",
            "condition": "",
            "manipulation_check_response": "Partner",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        assert is_partial_response(row) is True


class TestNormalization:
    def test_standard_keys(self):
        row = {
            "participant_id": "P008",
            "condition": "Partner",
            "manipulation_check_response": "Partner",
            "attitude_item_1": "5",
            "attitude_item_2": "5",
            "attitude_item_3": "5",
            "attitude_item_4": "5",
            "attitude_item_5": "5",
            "attitude_item_6": "5",
            "attitude_item_7": "5",
            "usefulness_item_1": "5",
            "usefulness_item_2": "5",
            "usefulness_item_3": "5",
            "trust_item_1": "5",
            "trust_item_2": "5",
            "trust_item_3": "5",
            "trust_item_4": "5"
        }
        normalized = normalize_row(row)
        assert normalized["participant_id"] == "P008"
        assert normalized["condition"] == "Partner"

    def test_alternative_keys(self):
        row = {
            "ParticipantID": "P009",
            "Frame": "Tool",
            "DidYouRead": "Tool",
            "Q_attitude_1": "5",
            "Q_usefulness_1": "5",
            "Q_trust_1": "5",
            # ... fill rest with defaults
            "attitude_item_1": "5", "attitude_item_2": "5", "attitude_item_3": "5",
            "attitude_item_4": "5", "attitude_item_5": "5", "attitude_item_6": "5", "attitude_item_7": "5",
            "usefulness_item_1": "5", "usefulness_item_2": "5", "usefulness_item_3": "5",
            "trust_item_1": "5", "trust_item_2": "5", "trust_item_3": "5", "trust_item_4": "5"
        }
        normalized = normalize_row(row)
        assert normalized["participant_id"] == "P009"
        assert normalized["condition"] == "Tool"
        assert normalized["manipulation_check_response"] == "Tool"


class TestParticipantEntity:
    def test_creation(self):
        p = Participant(
            participant_id="P010",
            condition="Partner",
            manipulation_check="Partner",
            manipulation_check_failed=False,
            attitude_item_1=5, attitude_item_2=5, attitude_item_3=5,
            attitude_item_4=5, attitude_item_5=5, attitude_item_6=5, attitude_item_7=5,
            usefulness_item_1=5, usefulness_item_2=5, usefulness_item_3=5,
            trust_item_1=5, trust_item_2=5, trust_item_3=5, trust_item_4=5
        )
        assert p.participant_id == "P010"
        assert p.condition == "Partner"
        assert p.manipulation_check_failed is False
        assert p.attitude_item_1 == 5