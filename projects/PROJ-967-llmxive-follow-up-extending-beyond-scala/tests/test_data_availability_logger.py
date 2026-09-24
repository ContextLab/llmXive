import json
import os
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys_path = str(Path(__file__).parent.parent / "code")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from data_availability_logger import log_dataset_availability, setup_directories

def test_log_zreward_unavailable_creates_correct_json():
    """
    Test that T037z logs the unavailability of Z-Reward correctly.
    Verifies the content of data/raw/validation_log.json.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)
        
        # Call the function simulating Z-Reward unavailability
        result = log_dataset_availability(
            base_dir=base_dir,
            zreward_available=False,
            fallback_source="oxford_pets",
            message="Z-Reward dataset not found; using synthetic Oxford Pets pipeline."
        )
        
        # Verify file exists
        log_path = base_dir / "data" / "raw" / "validation_log.json"
        assert log_path.exists(), "validation_log.json was not created"
        
        # Verify content
        with open(log_path, "r") as f:
            data = json.load(f)
        
        assert data["source"] == "oxford_pets"
        assert data["status"] == "synthetic_fallback"
        assert "Z-Reward dataset not found" in data["message"]
        assert data["schema_valid"] is False
        assert data["sample_count"] is None

def test_log_zreward_available_creates_correct_json():
    """
    Test logging when Z-Reward IS available (edge case check).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)
        
        result = log_dataset_availability(
            base_dir=base_dir,
            zreward_available=True,
            fallback_source="oxford_pets",
            message="Z-Reward dataset loaded successfully."
        )
        
        log_path = base_dir / "data" / "raw" / "validation_log.json"
        assert log_path.exists()
        
        with open(log_path, "r") as f:
            data = json.load(f)
        
        assert data["source"] == "zreward_evaluation"
        assert data["status"] == "available"
        assert data["schema_valid"] is True
        assert data["sample_count"] == 0 # Default for this test case