import json
import os
import tempfile
import pytest

# Ensure code/ is in path
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.join(current_dir, "..", "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from baseline_validator import BaselineValidator
from utils import compute_sha256

class TestBaselineValidator:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.valid_baseline_path = os.path.join(self.temp_dir, "valid_baseline.json")
        self.invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        self.missing_fields_path = os.path.join(self.temp_dir, "missing.json")
        self.nonexistent_path = os.path.join(self.temp_dir, "nonexistent.json")

        # Create a valid baseline file
        self.valid_data = {
            "dataset_name": "GAM Baseline Training Set",
            "version": "1.0.0",
            "description": "Original Geometric Action Model training metadata",
            "source": "GAM Original Publication",
            "statistics": {
                "total_tasks": 1000,
                "kinematic_chains": [{"type": "fixed_base", "count": 400}],
                "materials": [{"type": "rigid", "count": 1000}],
                "task_categories": ["pick_and_place", "pushing"]
            },
            "checksum": "sha256:dummy_checksum",
            "created_at": "2023-01-01T00:00:00Z",
            "overlap_verification": {
                "novel_kinematic_chains": False,
                "novel_materials": False,
                "novel_task_categories": False
            }
        }

        with open(self.valid_baseline_path, 'w') as f:
            json.dump(self.valid_data, f)

        # Create an invalid JSON file
        with open(self.invalid_json_path, 'w') as f:
            f.write("{ invalid json content")

        # Create a file with missing required fields
        self.missing_data = {
            "dataset_name": "Incomplete Dataset",
            "version": "1.0.0"
        }
        with open(self.missing_fields_path, 'w') as f:
            json.dump(self.missing_data, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ingest_valid_baseline(self):
        """Test ingestion of a valid baseline file."""
        validator = BaselineValidator(self.valid_baseline_path)
        result = validator.ingest_and_validate()
        
        assert result is True
        assert validator.is_valid is True
        assert len(validator.validation_errors) == 0
        assert validator.metadata["dataset_name"] == "GAM Baseline Training Set"
        assert validator.metadata["statistics"]["total_tasks"] == 1000

    def test_compute_hash(self):
        """Test that the computed hash is deterministic and correct."""
        validator = BaselineValidator(self.valid_baseline_path)
        validator.ingest_and_validate()
        
        # Hash should be computed
        assert validator.computed_hash != ""
        assert len(validator.computed_hash) == 64  # SHA-256 hex length

        # Verify hash matches manual computation
        hashable_data = {k: v for k, v in self.valid_data.items() if k != "checksum"}
        expected_hash = compute_sha256(json.dumps(hashable_data, sort_keys=True))
        assert validator.computed_hash == expected_hash

    def test_missing_file(self):
        """Test validation fails when file is missing."""
        validator = BaselineValidator(self.nonexistent_path)
        result = validator.ingest_and_validate()
        
        assert result is False
        assert validator.is_valid is False
        assert len(validator.validation_errors) > 0
        assert "not found" in validator.validation_errors[0]

    def test_invalid_json(self):
        """Test validation fails on invalid JSON."""
        validator = BaselineValidator(self.invalid_json_path)
        result = validator.ingest_and_validate()
        
        assert result is False
        assert validator.is_valid is False
        assert len(validator.validation_errors) > 0
        assert "Invalid JSON" in validator.validation_errors[0]

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        validator = BaselineValidator(self.missing_fields_path)
        result = validator.ingest_and_validate()
        
        assert result is False
        assert validator.is_valid is False
        assert len(validator.validation_errors) > 0
        assert "Missing required fields" in validator.validation_errors[0]

    def test_get_baseline_summary(self):
        """Test that baseline summary is correctly generated."""
        validator = BaselineValidator(self.valid_baseline_path)
        validator.ingest_and_validate()
        
        summary = validator.get_baseline_summary()
        
        assert summary["dataset_name"] == "GAM Baseline Training Set"
        assert summary["version"] == "1.0.0"
        assert summary["total_tasks"] == 1000
        assert "pick_and_place" in summary["task_categories"]
        assert summary["computed_hash"] == validator.computed_hash

    def test_metadata_property_before_validation(self):
        """Test that accessing metadata before validation raises error."""
        validator = BaselineValidator(self.valid_baseline_path)
        
        with pytest.raises(RuntimeError):
            _ = validator.metadata

        with pytest.raises(RuntimeError):
            _ = validator.computed_hash
