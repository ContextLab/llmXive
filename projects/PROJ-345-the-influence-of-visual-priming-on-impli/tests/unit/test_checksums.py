import pytest
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.state.checksums import calculate_file_checksum, calculate_linked_metadata_percentage
from config import get_path

def test_calculate_checksum():
    """Test checksum calculation on a known file."""
    # Create a temporary test file
    test_content = b"Hello, World!"
    test_file = get_path("data/raw/test_checksum.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_file.write_bytes(test_content)
    
    try:
        checksum = calculate_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert checksum != ""
    finally:
        if test_file.exists():
            test_file.unlink()

def test_calculate_linked_metadata_percentage():
    """Test linked metadata percentage calculation."""
    # Create a mock linked_trials.csv
    processed_dir = get_path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    mock_file = processed_dir / "linked_trials.csv"
    
    mock_data = [
        {"trial_id": "T001", "response_time": "500", "stimulus_id": "S001", "prime_condition": "pos", "participant_id": "P01"},
        {"trial_id": "T002", "response_time": "520", "stimulus_id": "", "prime_condition": "neg", "participant_id": "P01"},
        {"trial_id": "T003", "response_time": "480", "stimulus_id": "S003", "prime_condition": "pos", "participant_id": "P01"},
        {"trial_id": "T004", "response_time": "510", "stimulus_id": "S004", "prime_condition": "neg", "participant_id": "P01"},
        {"trial_id": "T005", "response_time": "490", "stimulus_id": "", "prime_condition": "pos", "participant_id": "P01"},
    ]
    
    with open(mock_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["trial_id", "response_time", "stimulus_id", "prime_condition", "participant_id"])
        writer.writeheader()
        writer.writerows(mock_data)
    
    try:
        percentage = calculate_linked_metadata_percentage()
        # 3 out of 5 have stimulus_id -> 60%
        assert percentage == 0.6
    finally:
        if mock_file.exists():
            mock_file.unlink()