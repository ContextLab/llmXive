"""
Unit tests for quickstart validation logic.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.quickstart_validation import (
    verify_artifacts,
    validate_metrics_content,
    run_step
)


class TestVerifyArtifacts:
    """Tests for verify_artifacts function."""

    def test_all_artifacts_exist(self, tmp_path):
        """Test when all artifacts exist and are non-empty."""
        # Create test artifacts
        for artifact in ['artifact1.csv', 'artifact2.json']:
            full_path = tmp_path / artifact
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("test content")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            all_exist, missing = verify_artifacts(['artifact1.csv', 'artifact2.json'])

        assert all_exist is True
        assert len(missing) == 0

    def test_missing_artifacts(self, tmp_path):
        """Test when some artifacts are missing."""
        # Create only one artifact
        full_path = tmp_path / 'artifact1.csv'
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("test content")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            all_exist, missing = verify_artifacts(['artifact1.csv', 'artifact2.json'])

        assert all_exist is False
        assert 'artifact2.json' in missing
        assert len(missing) == 1

    def test_empty_artifacts(self, tmp_path):
        """Test when artifacts exist but are empty."""
        # Create empty artifact
        full_path = tmp_path / 'empty.csv'
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            all_exist, missing = verify_artifacts(['empty.csv'])

        assert all_exist is False
        assert 'empty.csv' in missing


class TestValidateMetricsContent:
    """Tests for validate_metrics_content function."""

    def test_valid_metrics(self, tmp_path):
        """Test with valid metrics content."""
        metrics = {
            'rf_r2': 0.75,
            'rf_mae': 0.5,
            'rf_rmse': 0.8,
            'gb_r2': 0.78,
            'gb_mae': 0.45,
            'gb_rmse': 0.75,
            'overfitting_ratio': 0.02,
            'predictive_power': True,
            'final_r2_source': 'holdout'
        }

        metrics_path = tmp_path / 'model_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = validate_metrics_content('model_metrics.json')

        assert result is True

    def test_missing_required_field(self, tmp_path):
        """Test when a required field is missing."""
        metrics = {
            'rf_r2': 0.75,
            'rf_mae': 0.5,
            # Missing rf_rmse
            'gb_r2': 0.78,
            'gb_mae': 0.45,
            'gb_rmse': 0.75,
            'overfitting_ratio': 0.02,
            'predictive_power': True,
            'final_r2_source': 'holdout'
        }

        metrics_path = tmp_path / 'model_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = validate_metrics_content('model_metrics.json')

        assert result is False

    def test_invalid_r2_value(self, tmp_path):
        """Test when R² value is out of range."""
        metrics = {
            'rf_r2': 1.5,  # Invalid: > 1.0
            'rf_mae': 0.5,
            'rf_rmse': 0.8,
            'gb_r2': 0.78,
            'gb_mae': 0.45,
            'gb_rmse': 0.75,
            'overfitting_ratio': 0.02,
            'predictive_power': True,
            'final_r2_source': 'holdout'
        }

        metrics_path = tmp_path / 'model_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = validate_metrics_content('model_metrics.json')

        assert result is False

    def test_invalid_final_r2_source(self, tmp_path):
        """Test when final_r2_source is not 'holdout'."""
        metrics = {
            'rf_r2': 0.75,
            'rf_mae': 0.5,
            'rf_rmse': 0.8,
            'gb_r2': 0.78,
            'gb_mae': 0.45,
            'gb_rmse': 0.75,
            'overfitting_ratio': 0.02,
            'predictive_power': True,
            'final_r2_source': 'cross_validation'  # Invalid
        }

        metrics_path = tmp_path / 'model_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = validate_metrics_content('model_metrics.json')

        assert result is False

    def test_invalid_json(self, tmp_path):
        """Test when JSON is malformed."""
        metrics_path = tmp_path / 'model_metrics.json'
        metrics_path.write_text("invalid json {")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = validate_metrics_content('model_metrics.json')

        assert result is False


class TestRunStep:
    """Tests for run_step function."""

    def test_successful_step(self, tmp_path):
        """Test when step completes successfully."""
        # Create a simple test script
        test_script = tmp_path / 'test_script.py'
        test_script.write_text("print('Success')\n")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = run_step(
                'test_step',
                ['python', str(test_script)],
                timeout=10
            )

        assert result is True

    def test_failed_step(self, tmp_path):
        """Test when step fails with non-zero return code."""
        # Create a failing script
        test_script = tmp_path / 'failing_script.py'
        test_script.write_text("import sys; sys.exit(1)\n")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = run_step(
                'failing_step',
                ['python', str(test_script)],
                timeout=10
            )

        assert result is False

    def test_timeout_step(self, tmp_path):
        """Test when step times out."""
        # Create a slow script
        test_script = tmp_path / 'slow_script.py'
        test_script.write_text("import time; time.sleep(5)\n")

        with patch('code.quickstart_validation.PROJECT_ROOT', tmp_path):
            result = run_step(
                'timeout_step',
                ['python', str(test_script)],
                timeout=1  # 1 second timeout
            )

        assert result is False
