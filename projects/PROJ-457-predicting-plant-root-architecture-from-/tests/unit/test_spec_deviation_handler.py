import json
import os
import tempfile
from pathlib import Path
import pytest

# We need to temporarily modify the path to import the handler
# In a real run, this would be in the PYTHONPATH or installed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from spec_deviation_handler import load_deviations, save_deviations, record_spec_deviation_fr002

def test_load_deviations_empty_file():
    """Test loading from a non-existent file returns empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override the global path constant for testing
        import spec_deviation_handler
        original_path = spec_deviation_handler.DEVIATIONS_FILE_PATH
        try:
            # Use a file in the temp dir that doesn't exist
            fake_path = Path(tmpdir) / "nonexistent.json"
            spec_deviation_handler.DEVIATIONS_FILE_PATH = str(fake_path)
            
            result = load_deviations()
            assert result == []
        finally:
            spec_deviation_handler.DEVIATIONS_FILE_PATH = original_path

def test_load_deviations_corrupt_json():
    """Test handling of corrupt JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import spec_deviation_handler
        original_path = spec_deviation_handler.DEVIATIONS_FILE_PATH
        try:
            corrupt_file = Path(tmpdir) / "corrupt.json"
            with open(corrupt_file, 'w') as f:
                f.write("{ not valid json }")
            
            spec_deviation_handler.DEVIATIONS_FILE_PATH = str(corrupt_file)
            
            result = load_deviations()
            assert result == []
        finally:
            spec_deviation_handler.DEVIATIONS_FILE_PATH = original_path

def test_save_and_load_deviations():
    """Test saving and loading a list of deviations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import spec_deviation_handler
        original_path = spec_deviation_handler.DEVIATIONS_FILE_PATH
        try:
            test_file = Path(tmpdir) / "test_deviations.json"
            spec_deviation_handler.DEVIATIONS_FILE_PATH = str(test_file)
            
            test_data = [
                {"fr_id": "FR-001", "deviation": "Test deviation", "impact": "Test impact"}
            ]
            save_deviations(test_data)
            
            assert test_file.exists()
            
            loaded = load_deviations()
            assert loaded == test_data
        finally:
            spec_deviation_handler.DEVIATIONS_FILE_PATH = original_path

def test_record_fr002_appends_correctly():
    """Test that record_spec_deviation_fr002 appends the correct object."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import spec_deviation_handler
        original_path = spec_deviation_handler.DEVIATIONS_FILE_PATH
        try:
            test_file = Path(tmpdir) / "fr002_test.json"
            spec_deviation_handler.DEVIATIONS_FILE_PATH = str(test_file)
            
            # Pre-populate with a dummy entry
            save_deviations([{"fr_id": "FR-000", "deviation": "Existing", "impact": "Impact"}])
            
            record_spec_deviation_fr002()
            
            loaded = load_deviations()
            assert len(loaded) == 2
            assert loaded[0]["fr_id"] == "FR-000"
            
            fr002_entry = loaded[1]
            assert fr002_entry["fr_id"] == "FR-002"
            assert fr002_entry["deviation"] == "ISRIC merge excluded due to lack of verified source; proceeding with PlantPheno only."
            assert fr002_entry["impact"] == "SC-001 metric redefined as P/N Availability Rate"
        finally:
            spec_deviation_handler.DEVIATIONS_FILE_PATH = original_path

def test_record_fr002_no_duplicate():
    """Test that record_spec_deviation_fr002 does not duplicate if already present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import spec_deviation_handler
        original_path = spec_deviation_handler.DEVIATIONS_FILE_PATH
        try:
            test_file = Path(tmpdir) / "fr002_dup_test.json"
            spec_deviation_handler.DEVIATIONS_FILE_PATH = str(test_file)
            
            # Pre-populate with FR-002
            existing_entry = {
                "fr_id": "FR-002",
                "deviation": "ISRIC merge excluded due to lack of verified source; proceeding with PlantPheno only.",
                "impact": "SC-001 metric redefined as P/N Availability Rate"
            }
            save_deviations([existing_entry])
            
            record_spec_deviation_fr002()
            
            loaded = load_deviations()
            # Should still be length 1, not 2
            assert len(loaded) == 1
            assert loaded[0]["fr_id"] == "FR-002"
        finally:
            spec_deviation_handler.DEVIATIONS_FILE_PATH = original_path
