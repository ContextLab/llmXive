"""
Unit tests for ingestion module.
"""
import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from code.ingestion import (
    compute_sha256,
    extract_false_claim_from_text,
    validate_schema,
    save_to_csv,
    save_checksum_to_state
)

class TestComputeSha256:
    def test_compute_sha256_known_file(self):
        """Test SHA-256 computation on a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_sha256(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

class TestExtractFalseClaimFromText:
    def test_extract_false_claim_standard_format(self):
        """Test extraction from standard format."""
        text = "Question: What is X? false_claim: 'Vaccines cause autism'"
        result = extract_false_claim_from_text(text)
        assert result == "Vaccines cause autism"

    def test_extract_false_claim_misleading_format(self):
        """Test extraction from misleading format."""
        text = "Question: What is X? misleading: 'Global warming is fake'"
        result = extract_false_claim_from_text(text)
        assert result == "Global warming is fake"

    def test_extract_false_claim_no_match(self):
        """Test when no pattern matches."""
        text = "Question: What is X? This is just text."
        result = extract_false_claim_from_text(text)
        assert result is None

class TestValidateSchema:
    def test_validate_schema_valid(self):
        """Test validation with valid schema."""
        items = [{
            "prompt_id": "1",
            "prompt_text": "test",
            "false_claim": "claim",
            "correct_answer": "answer"
        }]
        is_valid, error_msg = validate_schema(items)
        assert is_valid is True
        assert error_msg is None

    def test_validate_schema_missing_column(self):
        """Test validation with missing column."""
        items = [{
            "prompt_id": "1",
            "prompt_text": "test"
            # Missing false_claim and correct_answer
        }]
        is_valid, error_msg = validate_schema(items)
        assert is_valid is False
        assert "Missing required columns" in error_msg

    def test_validate_schema_empty(self):
        """Test validation with empty list."""
        items = []
        is_valid, error_msg = validate_schema(items)
        assert is_valid is False
        assert "Dataset is empty" in error_msg

class TestSaveToCsv:
    def test_save_to_csv_success(self):
        """Test saving items to CSV."""
        items = [{
            "prompt_id": "1",
            "prompt_text": "test",
            "false_claim": "claim",
            "correct_answer": "answer"
        }]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            save_to_csv(items, temp_path)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "prompt_id" in content
                assert "test" in content
        finally:
            os.unlink(temp_path)

    def test_save_to_csv_empty_items(self):
        """Test saving empty items list raises error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            with pytest.raises(Exception) as exc_info:
                save_to_csv([], temp_path)
            assert "Cannot save empty dataset" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

class TestSaveChecksumToState:
    def test_save_checksum_creates_file(self):
        """Test that checksum file is created."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        with tempfile.TemporaryDirectory() as temp_dir:
            checksum_file = os.path.join(temp_dir, "state.yaml")
            
            save_checksum_to_state(temp_file, checksum_file)
            
            assert os.path.exists(checksum_file)
            
            with open(checksum_file, 'r') as f:
                state = yaml.safe_load(f)
                assert "medmis_subset" in state
                assert "sha256" in state["medmis_subset"]
                assert len(state["medmis_subset"]["sha256"]) == 64
        
        os.unlink(temp_file)
