"""
Integration tests for VIF compliance verification (Task T030).

These tests verify that the system correctly handles VIF > 5 scenarios
and that suppression logic is properly applied.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.verify_vif_compliance import (
    verify_vif_suppression_logic,
    generate_final_verification_report,
    load_model_results,
    load_vif_status
)


class TestVIFComplianceVerification:
    """Test suite for VIF compliance verification."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    @pytest.fixture
    def sample_model_results(self):
        """Create sample model results DataFrame."""
        data = {
            'model_type': ['OLS', 'OLS', 'Ridge', 'RandomForest'],
            'predictor': ['depth', 'surface_area', 'depth', 'depth'],
            'coefficient': [0.5, 0.3, 0.4, 0.55],
            'p_value': [0.01, 0.02, 0.015, 0.008],
            'r2': [0.65, 0.65, 0.66, 0.68],
            'adj_p_value': [0.03, 0.04, 0.035, 0.02]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_vif_status_no_high_vif(self):
        """Create sample VIF status with no high VIF detected."""
        return {
            'vif_detected': False,
            'vif_threshold': 5.0,
            'high_vif_predictors': [],
            'suppression_applied': False,
            'verification_status': 'pending'
        }

    @pytest.fixture
    def sample_vif_status_high_vif_suppressed(self):
        """Create sample VIF status with high VIF and suppression applied."""
        return {
            'vif_detected': True,
            'vif_threshold': 5.0,
            'high_vif_predictors': ['depth', 'surface_area'],
            'suppression_applied': True,
            'verification_status': 'pending'
        }

    @pytest.fixture
    def sample_vif_status_high_vif_not_suppressed(self):
        """Create sample VIF status with high VIF but no suppression."""
        return {
            'vif_detected': True,
            'vif_threshold': 5.0,
            'high_vif_predictors': ['depth'],
            'suppression_applied': False,
            'verification_status': 'pending'
        }

    def test_verify_vif_no_high_vif_detected(
        self,
        sample_model_results,
        sample_vif_status_no_high_vif
    ):
        """Test verification when no high VIF is detected."""
        result = verify_vif_suppression_logic(
            sample_model_results,
            sample_vif_status_no_high_vif
        )

        assert result['vif_detected'] is False
        assert result['suppression_applied'] is False
        assert result['verification_status'] == 'passed'
        assert result['claims_suppressed_correctly'] is True

    def test_verify_vif_high_vif_suppressed(
        self,
        sample_model_results,
        sample_vif_status_high_vif_suppressed
    ):
        """Test verification when high VIF is detected and suppression is applied."""
        result = verify_vif_suppression_logic(
            sample_model_results,
            sample_vif_status_high_vif_suppressed
        )

        assert result['vif_detected'] is True
        assert result['suppression_applied'] is True
        assert result['verification_status'] == 'passed'
        assert result['claims_suppressed_correctly'] is True
        assert set(result['high_vif_predictors']) == {'depth', 'surface_area'}

    def test_verify_vif_high_vif_not_suppressed(
        self,
        sample_model_results,
        sample_vif_status_high_vif_not_suppressed
    ):
        """Test verification when high VIF is detected but suppression is NOT applied."""
        result = verify_vif_suppression_logic(
            sample_model_results,
            sample_vif_status_high_vif_not_suppressed
        )

        assert result['vif_detected'] is True
        assert result['suppression_applied'] is False
        assert result['verification_status'] == 'failed'
        assert result['claims_suppressed_correctly'] is False

    def test_generate_final_verification_report(self, temp_dir, sample_model_results):
        """Test that the final verification report is generated correctly."""
        vif_status = {
            'vif_detected': True,
            'vif_threshold': 5.0,
            'high_vif_predictors': ['depth'],
            'suppression_applied': True,
            'verification_status': 'pending'
        }

        verification_result = verify_vif_suppression_logic(
            sample_model_results,
            vif_status
        )

        output_path = temp_dir / "test_vif_compliance.yaml"
        generate_final_verification_report(verification_result, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            saved_data = yaml.safe_load(f)

        assert saved_data['vif_detected'] is True
        assert saved_data['suppression_applied'] is True
        assert saved_data['verification_status'] == 'passed'
        assert 'verification_timestamp' in saved_data
        assert saved_data['task_id'] == 'T030'

    def test_load_model_results_file_not_found(self, temp_dir):
        """Test that FileNotFoundError is raised when model results file is missing."""
        non_existent_path = temp_dir / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_model_results(non_existent_path)

    def test_load_vif_status_file_not_found(self, temp_dir):
        """Test that FileNotFoundError is raised when VIF status file is missing."""
        non_existent_path = temp_dir / "non_existent.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_vif_status(non_existent_path)