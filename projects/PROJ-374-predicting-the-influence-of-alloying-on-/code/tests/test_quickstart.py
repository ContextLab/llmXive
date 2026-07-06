"""
Unit tests for quickstart validation logic.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from quickstart_validation import verify_outputs, log

class TestVerifyOutputs:
    def test_missing_files(self):
        """Test detection of missing output files."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Mock the global paths
            import quickstart_validation
            original_root = quickstart_validation.PROJECT_ROOT
            quickstart_validation.PROJECT_ROOT = tmp_path
            
            try:
                errors = verify_outputs()
                # Should find errors for missing files
                assert len(errors) > 0
                assert any("cleaned_compositions.csv" in e for e in errors)
            finally:
                quickstart_validation.PROJECT_ROOT = original_root

    def test_valid_outputs(self):
        """Test successful verification when all files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create required directory structure
            (tmp_path / "data" / "processed").mkdir(parents=True)
            (tmp_path / "state").mkdir(parents=True)
            (tmp_path / "docs" / "figures").mkdir(parents=True)
            
            # Create required files
            (tmp_path / "data" / "processed" / "cleaned_compositions.csv").touch()
            (tmp_path / "data" / "processed" / "final_features.csv").touch()
            
            model_output = {
                "r2_score": 0.5,
                "ci_lower": 0.3,
                "ci_upper": 0.7,
                "p_value": 0.01,
                "f_statistic": 10.5,
                "f_p_value": 0.001,
                "feature_importances": [0.1, 0.2]
            }
            with open(tmp_path / "data" / "processed" / "model_output.json", "w") as f:
                json.dump(model_output, f)
            
            (tmp_path / "state" / "cv_fold_scores.json").touch()
            (tmp_path / "docs" / "figures" / "top_descriptors_scatter.png").touch()
            
            report_content = "R² = 0.5\nClassification: Success\n95% CI: [0.3, 0.7]"
            with open(tmp_path / "docs" / "report.md", "w") as f:
                f.write(report_content)
            
            import quickstart_validation
            original_root = quickstart_validation.PROJECT_ROOT
            quickstart_validation.PROJECT_ROOT = tmp_path
            
            try:
                errors = verify_outputs()
                assert len(errors) == 0, f"Unexpected errors: {errors}"
            finally:
                quickstart_validation.PROJECT_ROOT = original_root

    def test_invalid_model_json(self):
        """Test detection of missing keys in model_output.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "data" / "processed").mkdir(parents=True)
            
            # Create invalid model output
            invalid_output = {"r2_score": 0.5}
            with open(tmp_path / "data" / "processed" / "model_output.json", "w") as f:
                json.dump(invalid_output, f)
            
            import quickstart_validation
            original_root = quickstart_validation.PROJECT_ROOT
            quickstart_validation.PROJECT_ROOT = tmp_path
            
            try:
                errors = verify_outputs()
                assert any("model_output.json" in e for e in errors)
            finally:
                quickstart_validation.PROJECT_ROOT = original_root

class TestLog:
    def test_log_format(self):
        """Test that log function produces expected format."""
        # This is a basic check, actual output goes to stdout
        try:
            log("Test message")
            log("Test error", level="ERROR")
        except Exception:
            pytest.fail("Log function raised exception")
