"""
Unit tests for code/data/download.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.download import validate_record_metadata, VALID_INSTRUMENTS

class TestValidateRecordMetadata:
    def test_valid_record_with_mmse(self):
        record = {
            "age": 25,
            "cognitive_score": 28,
            "cognitive_instrument": "MMSE"
        }
        is_valid, reason = validate_record_metadata(record)
        assert is_valid is True
        assert reason == "OK"

    def test_valid_record_with_moca(self):
        record = {
            "age": 60,
            "cognitive_score": 25,
            "cognitive_instrument": "MoCA"
        }
        is_valid, reason = validate_record_metadata(record)
        assert is_valid is True
        assert reason == "OK"

    def test_invalid_age(self):
        record = {
            "age": 17,
            "cognitive_score": 30,
            "cognitive_instrument": "MMSE"
        }
        is_valid, reason = validate_record_metadata(record)
        assert is_valid is False
        assert reason == "INVALID_AGE"

    def test_missing_cognitive_score(self):
        record = {
            "age": 40,
            "cognitive_score": None,
            "cognitive_instrument": None
        }
        is_valid, reason = validate_record_metadata(record)
        # Task says: "If missing, flag as 'Missing Cognitive Data' (do not fail)."
        # However, our function returns (is_valid, reason). 
        # In the context of the report, we count this separately.
        # The function logic in download.py sets reason to "MISSING_COGNITIVE" but returns True for the record existence?
        # Let's check the implementation: 
        # In download.py: if cognitive_score is None: report["missing_cognitive_count"] += 1; reason = "MISSING_COGNITIVE"
        # It does NOT return False. So is_valid should be True.
        assert is_valid is True
        assert reason == "MISSING_COGNITIVE"

    def test_invalid_instrument(self):
        record = {
            "age": 50,
            "cognitive_score": 20,
            "cognitive_instrument": "Wechsler"
        }
        is_valid, reason = validate_record_metadata(record)
        assert is_valid is True
        assert reason == "INVALID_INSTRUMENT"

    def test_missing_age(self):
        record = {
            "age": None,
            "cognitive_score": 20,
            "cognitive_instrument": "MMSE"
        }
        is_valid, reason = validate_record_metadata(record)
        assert is_valid is False
        assert reason == "INVALID_AGE"

class TestConstants:
    def test_valid_instruments(self):
        assert "MMSE" in VALID_INSTRUMENTS
        assert "MoCA" in VALID_INSTRUMENTS
        assert len(VALID_INSTRUMENTS) == 2