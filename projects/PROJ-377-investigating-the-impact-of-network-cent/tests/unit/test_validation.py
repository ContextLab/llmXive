import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from code.data.validation import validate_retention_and_behavioral_data

class TestRetentionValidation:
    """
    Unit tests for T003: Retention & Behavioral Validation.
    """

    def setup_method(self):
        """Setup temporary directory and test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_path = os.path.join(self.temp_dir, "metadata.csv")
        self.output_path = os.path.join(self.temp_dir, "retention_metrics.json")

    def teardown_method(self):
        """Cleanup temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_metadata_file(self, data):
        """Helper to create a metadata CSV file."""
        df = pd.DataFrame(data)
        df.to_csv(self.metadata_path, index=False)

    def test_high_retention_success(self):
        """Test case where retention > 80% (valid behavioral data)."""
        data = [
            {"subject_id": "sub-01", "pre_motor_score": 10, "post_motor_score": 15},
            {"subject_id": "sub-02", "pre_motor_score": 12, "post_motor_score": 18},
            {"subject_id": "sub-03", "pre_motor_score": 8, "post_motor_score": 14},
            {"subject_id": "sub-04", "pre_motor_score": 11, "post_motor_score": 16},
            {"subject_id": "sub-05", "pre_motor_score": 9, "post_motor_score": 13},
        ]
        self.create_metadata_file(data)
        
        success, metrics = validate_retention_and_behavioral_data(
            self.metadata_path, self.output_path
        )
        
        assert success is True
        assert metrics["total_subjects"] == 5
        assert metrics["retained_subjects"] == 5
        assert metrics["retention_rate"] == 1.0
        assert metrics["threshold_met"] is True
        
        # Verify file was written
        assert os.path.exists(self.output_path)
        with open(self.output_path, 'r') as f:
            saved_metrics = json.load(f)
        assert saved_metrics["retention_rate"] == 1.0

    def test_low_retention_behavioral_failure(self):
        """Test case where retention < 80% due to missing behavioral data -> Fatal."""
        # 4 valid, 1 missing -> 80% exactly (pass). Need < 80%.
        # 3 valid, 2 missing -> 60% (fail).
        data = [
            {"subject_id": "sub-01", "pre_motor_score": 10, "post_motor_score": 15},
            {"subject_id": "sub-02", "pre_motor_score": 12, "post_motor_score": 18},
            {"subject_id": "sub-03", "pre_motor_score": 8, "post_motor_score": 14},
            {"subject_id": "sub-04", "pre_motor_score": None, "post_motor_score": None}, # Missing
            {"subject_id": "sub-05", "pre_motor_score": None, "post_motor_score": None}, # Missing
        ]
        self.create_metadata_file(data)
        
        with pytest.raises(RuntimeError, match="Fatal: Retention < 80% due to missing behavioral data"):
            validate_retention_and_behavioral_data(self.metadata_path, self.output_path)

    def test_low_retention_motion_warning(self):
        """Test case where retention < 80% but due to motion artifacts -> Warning & Proceed."""
        # 3 valid, 2 missing due to motion -> 60% retention.
        # Assuming 'exclusion_reason' column exists.
        data = [
            {"subject_id": "sub-01", "pre_motor_score": 10, "post_motor_score": 15, "exclusion_reason": "valid"},
            {"subject_id": "sub-02", "pre_motor_score": 12, "post_motor_score": 18, "exclusion_reason": "valid"},
            {"subject_id": "sub-03", "pre_motor_score": 8, "post_motor_score": 14, "exclusion_reason": "valid"},
            {"subject_id": "sub-04", "pre_motor_score": None, "post_motor_score": None, "exclusion_reason": "motion artifacts"},
            {"subject_id": "sub-05", "pre_motor_score": None, "post_motor_score": None, "exclusion_reason": "motion artifacts"},
        ]
        self.create_metadata_file(data)
        
        # Should NOT raise, but log warning and return success
        success, metrics = validate_retention_and_behavioral_data(
            self.metadata_path, self.output_path
        )
        
        assert success is True
        assert metrics["retention_rate"] == 0.6
        assert metrics["motion_artifact_count"] == 2
        assert metrics["missing_behavioral_count"] == 2
        # File should still be written
        assert os.path.exists(self.output_path)

    def test_missing_columns_failure(self):
        """Test case where required columns are missing."""
        data = [
            {"subject_id": "sub-01", "age": 25},
            {"subject_id": "sub-02", "age": 30},
        ]
        self.create_metadata_file(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_retention_and_behavioral_data(self.metadata_path, self.output_path)

    def test_empty_file_failure(self):
        """Test case where metadata file is empty."""
        self.create_metadata_file([])
        
        with pytest.raises(ValueError, match="Metadata file is empty"):
            validate_retention_and_behavioral_data(self.metadata_path, self.output_path)

    def test_file_not_found_failure(self):
        """Test case where metadata file does not exist."""
        with pytest.raises(FileNotFoundError):
            validate_retention_and_behavioral_data(
                "non_existent_path.csv", self.output_path
            )
