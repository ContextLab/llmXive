"""
Unit tests for the ingestion module.
"""
import pytest
import os
import tempfile
import csv
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the functions to test
from ingestion import extract_false_claim_from_text, validate_schema, save_to_csv

class TestExtractFalseClaim:
    def test_extract_from_false_claim_column(self):
        text = "This is a false claim: The earth is flat."
        result = extract_false_claim_from_text(text)
        assert result == "The earth is flat."
    
    def test_extract_from_claim_column(self):
        text = "claim: Vaccines cause autism."
        result = extract_false_claim_from_text(text)
        assert result == "Vaccines cause autism."
    
    def test_extract_from_misinformation_column(self):
        text = "misinformation: 5G towers spread viruses."
        result = extract_false_claim_from_text(text)
        assert result == "5G towers spread viruses."
    
    def test_no_match_returns_none(self):
        text = "This is a normal sentence without any claim markers."
        result = extract_false_claim_from_text(text)
        assert result is None
    
    def test_empty_string_returns_none(self):
        result = extract_false_claim_from_text("")
        assert result is None

class TestValidateSchema:
    def test_schema_present(self):
        row = {"prompt": "Test", "false_claim": "Fake info"}
        is_valid, claim = validate_schema(row)
        assert is_valid is True
        assert claim == "Fake info"
    
    def test_schema_missing_extract_success(self):
        row = {"prompt": "false_claim: The moon is made of cheese."}
        is_valid, claim = validate_schema(row)
        assert is_valid is True
        assert claim == "The moon is made of cheese."
    
    def test_schema_missing_extract_fail(self):
        row = {"prompt": "Just a normal sentence."}
        is_valid, claim = validate_schema(row)
        assert is_valid is False
        assert claim is None

class TestSaveToCsv:
    def test_save_rows(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
        
        rows = [
            {"id": "1", "prompt": "Test 1", "false_claim": "Fake 1"},
            {"id": "2", "prompt": "Test 2", "false_claim": "Fake 2"}
        ]
        
        save_to_csv(rows, tmp_path)
        
        assert os.path.exists(tmp_path)
        with open(tmp_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            assert len(data) == 2
            assert data[0]["id"] == "1"
            assert data[0]["false_claim"] == "Fake 1"
        
        os.unlink(tmp_path)
    
    def test_save_empty_rows(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
        
        save_to_csv([], tmp_path)
        
        assert os.path.exists(tmp_path)
        with open(tmp_path, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1 # Header only
        
        os.unlink(tmp_path)