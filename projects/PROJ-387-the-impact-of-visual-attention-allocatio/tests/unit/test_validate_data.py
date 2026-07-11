import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.validate_data import (
    validate_columns,
    validate_data_quality_metrics,
    validate_valence_labels,
    write_quality_report
)
from utils.config import get_project_root

def test_validate_columns_pass():
    """Test that validate_columns returns True when all required columns are present."""
    df = pd.DataFrame({
        "fixation_duration": [100.0],
        "saccade_amplitude": [2.0],
        "gaze_distribution": [0.8],
        "recall_accuracy": [0.9],
        "valence_label": ["Positive"]
    })
    assert validate_columns(df) is True

def test_validate_columns_fail():
    """Test that validate_columns returns False when a required column is missing."""
    df = pd.DataFrame({
        "fixation_duration": [100.0],
        "saccade_amplitude": [2.0]
    })
    assert validate_columns(df) is False

def test_validate_data_quality_metrics_track_loss_pass():
    """Test track loss validation when loss is within threshold."""
    df = pd.DataFrame({
        "track_loss": [False] * 100,  # 0% loss
        "calibrated": [True] * 100
    })
    metrics = validate_data_quality_metrics(df)
    assert metrics["track_loss_percent"] == 0.0
    assert metrics["track_loss_passed"] is True
    assert metrics["calibration_passed"] is True

def test_validate_data_quality_metrics_track_loss_fail():
    """Test track loss validation when loss exceeds threshold."""
    # Create 100 rows, 10 with track loss (10% > 5%)
    df = pd.DataFrame({
        "track_loss": [True] * 10 + [False] * 90,
        "calibrated": [True] * 100
    })
    metrics = validate_data_quality_metrics(df)
    assert metrics["track_loss_percent"] == 10.0
    assert metrics["track_loss_passed"] is False

def test_validate_data_quality_metrics_calibration_fail():
    """Test calibration validation when not calibrated."""
    df = pd.DataFrame({
        "track_loss": [False] * 100,
        "calibrated": [False] * 100
    })
    metrics = validate_data_quality_metrics(df)
    assert metrics["is_calibrated"] is False
    assert metrics["calibration_passed"] is False

def test_validate_valence_labels():
    """Test valence label validation."""
    df = pd.DataFrame({
        "valence_label": ["Positive", "Neutral", "Negative", "Positive"]
    })
    metrics = validate_valence_labels(df)
    assert metrics["valence_categories_count"] == 3
    assert metrics["valence_passed"] is True

def test_write_quality_report(tmp_path):
    """Test that write_quality_report creates a valid markdown file."""
    quality_metrics = {
        "track_loss_percent": 2.0,
        "track_loss_passed": True,
        "calibration_passed": True,
        "total_records": 100,
        "valid_records": 98
    }
    valence_metrics = {
        "valence_categories_count": 3,
        "valence_categories_found": ["Positive", "Neutral", "Negative"],
        "valence_passed": True
    }
    
    output_file = tmp_path / "quality_report.md"
    write_quality_report(quality_metrics, valence_metrics, output_file)
    
    assert output_file.exists()
    content = output_file.read_text()
    assert "Data Quality Report" in content
    assert "Track Loss: 2.00%" in content
    assert "Status" in content
    assert "PASSED" in content