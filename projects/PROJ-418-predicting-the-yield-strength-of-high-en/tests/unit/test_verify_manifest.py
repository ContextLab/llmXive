"""
Unit tests for manifest verification (T122).

Tests the verify_manifest.py script to ensure it correctly validates
the presence of all required provenance fields in manifest.json.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_manifest import validate_manifest, load_manifest, REQUIRED_FIELDS, SUBFIELD_REQUIREMENTS


class TestManifestValidation:
    """Test cases for manifest validation logic."""

    def test_valid_manifest_passes(self):
        """Test that a complete manifest with all required fields passes validation."""
        valid_manifest = {
            "seeds": {
                "split": 42,
                "model": 42,
                "bootstrap": 42
            },
            "hyperparameters": {
                "random_forest": {"n_estimators": 500},
                "linear": {}
            },
            "versions": {
                "python": "3.9",
                "numpy": "1.21.0",
                "pandas": "1.3.0",
                "scikit-learn": "0.24.0"
            },
            "timestamps": {
                "pipeline_start": "2024-01-01T00:00:00",
                "pipeline_end": "2024-01-01T01:00:00",
                "manifest_generated": "2024-01-01T01:00:01"
            },
            "checksums": {
                "raw_dataset": "abc123",
                "processed_dataset": "def456",
                "descriptor_table": "ghi789"
            },
            "descriptor_version_hash": "desc_hash_123",
            "vif_remediation_decisions": {"method": "PCA"},
            "permutation_settings": {
                "n_permutations": 1000,
                "random_state": 42
            }
        }
        
        is_valid, errors = validate_manifest(valid_manifest)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_top_level_field(self):
        """Test that missing a top-level required field fails validation."""
        incomplete_manifest = {
            "seeds": {"split": 42, "model": 42, "bootstrap": 42},
            # Missing "hyperparameters"
            "versions": {"python": "3.9"},
            "timestamps": {},
            "checksums": {},
            "descriptor_version_hash": "hash",
            "vif_remediation_decisions": {},
            "permutation_settings": {}
        }
        
        is_valid, errors = validate_manifest(incomplete_manifest)
        assert is_valid is False
        assert "Missing required field: hyperparameters" in errors

    def test_missing_subfield_in_seeds(self):
        """Test that missing a subfield in seeds fails validation."""
        incomplete_manifest = {
            "seeds": {
                "split": 42,
                "model": 42
                # Missing "bootstrap"
            },
            "hyperparameters": {"random_forest": {}, "linear": {}},
            "versions": {"python": "3.9", "numpy": "1.0", "pandas": "1.0", "scikit-learn": "1.0"},
            "timestamps": {"pipeline_start": "t1", "pipeline_end": "t2", "manifest_generated": "t3"},
            "checksums": {"raw_dataset": "c1", "processed_dataset": "c2", "descriptor_table": "c3"},
            "descriptor_version_hash": "h",
            "vif_remediation_decisions": {},
            "permutation_settings": {"n_permutations": 1000, "random_state": 42}
        }
        
        is_valid, errors = validate_manifest(incomplete_manifest)
        assert is_valid is False
        assert "Missing subfield 'bootstrap' in 'seeds'" in errors

    def test_invalid_checksum_format(self):
        """Test that empty or non-string checksums fail validation."""
        invalid_manifest = {
            "seeds": {"split": 42, "model": 42, "bootstrap": 42},
            "hyperparameters": {"random_forest": {}, "linear": {}},
            "versions": {"python": "3.9", "numpy": "1.0", "pandas": "1.0", "scikit-learn": "1.0"},
            "timestamps": {"pipeline_start": "t1", "pipeline_end": "t2", "manifest_generated": "t3"},
            "checksums": {
                "raw_dataset": "",  # Empty string
                "processed_dataset": "valid",
                "descriptor_table": 123  # Non-string
            },
            "descriptor_version_hash": "h",
            "vif_remediation_decisions": {},
            "permutation_settings": {"n_permutations": 1000, "random_state": 42}
        }
        
        is_valid, errors = validate_manifest(invalid_manifest)
        assert is_valid is False
        assert any("Invalid checksum for raw_dataset" in e for e in errors)
        assert any("Invalid checksum for descriptor_table" in e for e in errors)

    def test_invalid_seed_format(self):
        """Test that non-integer seeds fail validation."""
        invalid_manifest = {
            "seeds": {
                "split": "42",  # String instead of int
                "model": 42,
                "bootstrap": 42
            },
            "hyperparameters": {"random_forest": {}, "linear": {}},
            "versions": {"python": "3.9", "numpy": "1.0", "pandas": "1.0", "scikit-learn": "1.0"},
            "timestamps": {"pipeline_start": "t1", "pipeline_end": "t2", "manifest_generated": "t3"},
            "checksums": {"raw_dataset": "c1", "processed_dataset": "c2", "descriptor_table": "c3"},
            "descriptor_version_hash": "h",
            "vif_remediation_decisions": {},
            "permutation_settings": {"n_permutations": 1000, "random_state": 42}
        }
        
        is_valid, errors = validate_manifest(invalid_manifest)
        assert is_valid is False
        assert "Invalid seed for split: must be integer" in errors

    def test_load_manifest_file_not_found(self):
        """Test that load_manifest raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_manifest("/nonexistent/path/manifest.json")

    def test_load_manifest_success(self, tmp_path):
        """Test successful loading of a valid manifest file."""
        manifest_data = {"test": "data"}
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))
        
        result = load_manifest(str(manifest_file))
        assert result == manifest_data


class TestManifestVerificationIntegration:
    """Integration tests for the manifest verification script."""

    @pytest.fixture
    def valid_manifest_file(self, tmp_path):
        """Create a temporary valid manifest file."""
        manifest = {
            "seeds": {"split": 42, "model": 42, "bootstrap": 42},
            "hyperparameters": {"random_forest": {}, "linear": {}},
            "versions": {"python": "3.9", "numpy": "1.0", "pandas": "1.0", "scikit-learn": "1.0"},
            "timestamps": {"pipeline_start": "t1", "pipeline_end": "t2", "manifest_generated": "t3"},
            "checksums": {"raw_dataset": "c1", "processed_dataset": "c2", "descriptor_table": "c3"},
            "descriptor_version_hash": "h",
            "vif_remediation_decisions": {},
            "permutation_settings": {"n_permutations": 1000, "random_state": 42}
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest))
        return str(manifest_file)

    def test_main_with_valid_manifest(self, valid_manifest_file, capsys):
        """Test main() returns 0 for a valid manifest."""
        with patch('verify_manifest.manifest_path', valid_manifest_file):
            # We need to patch the path used inside main
            import verify_manifest
            original_load = verify_manifest.load_manifest
            
            def mock_load(path):
                if path == valid_manifest_file:
                    return json.loads(open(valid_manifest_file).read())
                raise FileNotFoundError()
            
            verify_manifest.load_manifest = mock_load
            
            try:
                result = verify_manifest.main()
                assert result == 0
                captured = capsys.readouterr()
                assert "pass" in captured.out
            finally:
                verify_manifest.load_manifest = original_load

    def test_main_with_missing_manifest(self, capsys):
        """Test main() returns 1 for a missing manifest."""
        import verify_manifest
        original_load = verify_manifest.load_manifest
        
        def mock_load(path):
            raise FileNotFoundError("File not found")
        
        verify_manifest.load_manifest = mock_load
        
        try:
            result = verify_manifest.main()
            assert result == 1
            captured = capsys.readouterr()
            assert "fail" in captured.out
            assert "not found" in captured.out.lower()
        finally:
            verify_manifest.load_manifest = original_load