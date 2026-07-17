"""
Unit tests for the annotation module (T017a).

Tests cover:
- Recruitment logic generation
- File output structure
- Mode switching behavior
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from annotation import RaterRecruiter, run_recruitment_pipeline
from config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config for testing."""
    # Mock the Config class to use temporary directories
    config = MagicMock(spec=Config)
    config.data_interim_path = tmp_path
    return config


def test_rater_recruiter_manual_mode(temp_config):
    """Test that manual mode generates the correct number of raters."""
    n_raters = 50
    recruiter = RaterRecruiter(temp_config, mode="manual")
    raters = recruiter.recruit(n_raters)

    assert len(raters) == n_raters
    for rater in raters:
        assert "rater_id" in rater
        assert "consent_timestamp" in rater
        assert rater["status"] == "consented"
        assert rater["platform"] == "prolific"  # Simulated platform ID


def test_recruitment_log_structure(temp_config):
    """Test that the saved log has the correct JSON structure."""
    n_raters = 10
    recruiter = RaterRecruiter(temp_config, mode="manual")
    recruiter.recruit(n_raters)
    log_path = recruiter.save_recruitment_log()

    assert log_path.exists()

    with open(log_path, 'r') as f:
        data = json.load(f)

    assert data["task_id"] == "T017a"
    assert data["user_story"] == "US1"
    assert data["purpose"] == "feature_validation"
    assert data["total_raters"] == n_raters
    assert "raters" in data
    assert isinstance(data["raters"], list)


def test_run_recruitment_pipeline_integration(temp_config):
    """Test the full pipeline function."""
    n_raters = 20
    # Patch the Config initialization to use our temp config
    with patch('annotation.Config', return_value=temp_config):
        log_path = run_recruitment_pipeline(n=n_raters, mode="manual")

    assert log_path.exists()
    with open(log_path, 'r') as f:
        data = json.load(f)
    assert data["total_raters"] == n_raters


def test_fallback_to_manual_on_prolific_failure(temp_config):
    """Test that if prolific mode fails, it falls back to manual."""
    # Mock get_prolific_api_key to raise an error
    with patch('annotation.get_prolific_api_key', side_effect=RuntimeError("Key missing")):
        recruiter = RaterRecruiter(temp_config, mode="prolific")
        # The constructor should have caught the error and switched mode
        assert recruiter.mode == "manual"

        raters = recruiter.recruit(5)
        assert len(raters) == 5