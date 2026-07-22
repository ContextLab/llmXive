import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import validate_source_id, FatalError
from code.config import Config

class TestVerifiedSourceGate:
    """Tests for T041: Strict Verified Source Gate in download.py"""

    @pytest.fixture
    def temp_verified_sources(self, tmp_path):
        """Create a temporary verified_sources.json file."""
        data = {
            "openneuro_id": "ds004563",
            "verified_date": "2023-10-27",
            "notes": "Test dataset"
        }
        file_path = tmp_path / "verified_sources.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return file_path

    def test_valid_source_id_passes(self, temp_verified_sources):
        """Test that a matching ID passes validation."""
        assert validate_source_id("ds004563", temp_verified_sources) is True

    def test_missing_file_raises_fatal(self, tmp_path):
        """Test that missing verified_sources.json raises FatalError."""
        missing_path = tmp_path / "nonexistent.json"
        with pytest.raises(FatalError, match="Missing verified dataset source file"):
            validate_source_id("ds001234", missing_path)

    def test_malformed_json_raises_fatal(self, tmp_path):
        """Test that malformed JSON raises FatalError."""
        file_path = tmp_path / "bad.json"
        file_path.write_text("not valid json {")
        with pytest.raises(FatalError, match="Malformed verified sources file"):
            validate_source_id("ds001234", file_path)

    def test_missing_key_raises_fatal(self, tmp_path):
        """Test that missing 'openneuro_id' key raises FatalError."""
        data = {"other_key": "value"}
        file_path = tmp_path / "bad.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        with pytest.raises(FatalError, match="Invalid format"):
            validate_source_id("ds001234", file_path)

    def test_empty_id_raises_fatal(self, tmp_path):
        """Test that empty ID in file raises FatalError."""
        data = {"openneuro_id": ""}
        file_path = tmp_path / "bad.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        with pytest.raises(FatalError, match="Missing verified dataset source"):
            validate_source_id("ds001234", file_path)

    def test_mismatched_id_raises_fatal(self, temp_verified_sources):
        """Test that a non-matching ID raises FatalError."""
        with pytest.raises(FatalError, match="Source ID mismatch"):
            validate_source_id("ds999999", temp_verified_sources)

    def test_default_id_mismatch_raises_fatal(self, temp_verified_sources):
        """Test that default 'ds000000' raises FatalError if not verified."""
        with pytest.raises(FatalError, match="Source ID mismatch"):
            validate_source_id("ds000000", temp_verified_sources)
