import pytest
import os
import csv
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import (
    extract_false_claim_from_text,
    validate_schema,
    save_to_csv,
    save_checksum_to_state
)
from error_handling import DatasetDownloadError

class TestExtractFalseClaim:
    """Tests for regex extraction fallback."""
    
    def test_extract_claim_with_pattern(self):
        """Test extraction with known pattern."""
        text = "The false claim: 'Vaccines cause autism' is widespread."
        result = extract_false_claim_from_text(text)
        assert result == "Vaccines cause autism"
    
    def test_extract_claim_no_pattern(self):
        """Test extraction when no pattern matches."""
        text = "This is a normal sentence without any claims."
        result = extract_false_claim_from_text(text)
        assert result is None
    
    def test_extract_claim_multiple_patterns(self):
        """Test extraction with multiple potential patterns (should return first match)."""
        text = "The false claim: 'Test claim 1' and misinformation: 'Test claim 2'."
        result = extract_false_claim_from_text(text)
        assert result == "Test claim 1"

class TestValidateSchema:
    """Tests for schema validation."""
    
    def test_validate_schema_with_false_claim(self):
        """Test validation when false_claim column exists."""
        data = [
            {"prompt": "Test prompt", "label": "Authority-framed", "false_claim": "Test claim"}
        ]
        assert validate_schema(data) is True
    
    def test_validate_schema_missing_false_claim_with_extraction(self):
        """Test validation when false_claim is missing but can be extracted."""
        data = [
            {
                "prompt": "The false claim: 'Test claim' is false.",
                "label": "Exception-poisoning"
            }
        ]
        assert validate_schema(data) is True
        # Verify the false_claim was added
        assert "false_claim" in data[0]
    
    def test_validate_schema_empty_dataset(self):
        """Test validation with empty dataset."""
        with pytest.raises(DatasetDownloadError):
            validate_schema([])
    
    def test_validate_schema_missing_required_column(self):
        """Test validation when required column is missing and cannot be extracted."""
        data = [
            {"prompt": "Test prompt"}  # Missing 'label'
        ]
        with pytest.raises(DatasetDownloadError):
            validate_schema(data)

class TestSaveToCsv:
    """Tests for CSV saving functionality."""
    
    def test_save_to_csv_creates_file(self, tmp_path):
        """Test that save_to_csv creates the file correctly."""
        data = [
            {"prompt": "Test 1", "label": "Authority-framed"},
            {"prompt": "Test 2", "label": "Exception-poisoning"}
        ]
        output_path = tmp_path / "test.csv"
        
        save_to_csv(data, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert rows[0]["prompt"] == "Test 1"
        assert rows[0]["label"] == "Authority-framed"
    
    def test_save_to_csv_empty_data(self, tmp_path):
        """Test saving empty data."""
        output_path = tmp_path / "test_empty.csv"
        save_to_csv([], str(output_path))
        
        # Should create file with headers only (or empty file)
        assert output_path.exists()

class TestSaveChecksumToState:
    """Tests for checksum saving functionality."""
    
    def test_save_checksum_creates_state_file(self, tmp_path):
        """Test that checksum is saved correctly."""
        data = [{"test": "data"}]
        state_file = tmp_path / "state.yaml"
        
        save_checksum_to_state(data, str(state_file))
        
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        assert "medmis_subset_sha256" in state
        assert "last_updated" in state
        # Verify checksum is a valid hex string
        assert len(state["medmis_subset_sha256"]) == 64
    
    def test_save_checksum_updates_existing_state(self, tmp_path):
        """Test that checksum is updated in existing state file."""
        data = [{"test": "data"}]
        state_file = tmp_path / "state.yaml"
        
        # Create initial state
        initial_state = {"other_key": "value"}
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        save_checksum_to_state(data, str(state_file))
        
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        assert "other_key" in state  # Existing data preserved
        assert "medmis_subset_sha256" in state  # New checksum added
