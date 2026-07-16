"""
Unit tests for the RawDataLogger module.
"""
import pytest
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from simulator.raw_data_logger import RawDataLogger
from simulator.data_validator import DataValidator
from config.settings import get_settings


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def mock_settings(temp_data_dir):
    """Mock settings to use temporary directory."""
    settings = MagicMock()
    settings.data_raw_dir = str(temp_data_dir)
    return settings


def test_log_session_complete(mock_settings, temp_data_dir):
    """Test logging a complete session."""
    with patch('simulator.raw_data_logger.get_settings', return_value=mock_settings):
        logger = RawDataLogger()
        
        # Mock the validator to always pass
        with patch.object(logger.validator, 'validate_session', return_value=True):
            path = logger.log_session(
                participant_id="P001",
                disability_type="visual",
                interface_type="Explainable",
                sequence="Traditional->Explainable",
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_count=2,
                explanation_engagement_time_seconds=15.5,
                sus_score=85.0,
                status="complete"
            )

            # Verify file was created
            assert os.path.exists(path)
            
            # Verify content
            with open(path, 'r') as f:
                data = json.load(f)
            
            assert data["participant_id"] == "P001"
            assert data["status"] == "complete"
            assert data["dropout_reason"] is None
            assert "checksum" in data


def test_log_session_incomplete(mock_settings, temp_data_dir):
    """Test logging an incomplete session."""
    with patch('simulator.raw_data_logger.get_settings', return_value=mock_settings):
        logger = RawDataLogger()
        
        with patch.object(logger.validator, 'validate_session', return_value=True):
            path = logger.log_incomplete_session(
                participant_id="P002",
                disability_type="motor",
                interface_type="Traditional",
                sequence="Explainable->Traditional",
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_count=5,
                explanation_engagement_time_seconds=0.0,
                sus_score=40.0,
                dropout_reason="Fatigue"
            )

            assert os.path.exists(path)
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            assert data["status"] == "incomplete"
            assert data["dropout_reason"] == "Fatigue"


def test_log_session_validation_failure(mock_settings, temp_data_dir):
    """Test that logging fails if validation fails."""
    with patch('simulator.raw_data_logger.get_settings', return_value=mock_settings):
        logger = RawDataLogger()
        
        with patch.object(logger.validator, 'validate_session', return_value=False):
            with pytest.raises(ValueError, match="Session data failed validation"):
                logger.log_session(
                    participant_id="P003",
                    disability_type="visual",
                    interface_type="Explainable",
                    sequence="Traditional->Explainable",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_count=2,
                    explanation_engagement_time_seconds=15.5,
                    sus_score=85.0,
                    status="complete"
                )