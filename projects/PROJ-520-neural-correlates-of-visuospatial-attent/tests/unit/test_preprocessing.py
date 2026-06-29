import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing import (
    get_subject_epoch_counts,
    select_subjects_for_memory_limit,
    validate_epoch_counts,
    log_epoch_rejection_rate
)
from config import get_config

@pytest.fixture
def mock_bids_root(tmp_path):
    """Create a mock BIDS structure."""
    # Create sub-01, sub-02, sub-03
    for i in [1, 2, 3]:
        sub_dir = tmp_path / f"sub-{i:02d}"
        sub_dir.mkdir()
        # Create events.tsv with varying counts
        events_file = sub_dir / "eeg" / "sub-01_task-navigation_events.tsv"
        events_file.parent.mkdir(parents=True, exist_ok=True)
        count = i * 50 # sub-01: 50, sub-02: 100, sub-03: 150
        with open(events_file, 'w') as f:
            f.write("onset\tduration\ttrial_type\n")
            for _ in range(count):
                f.write("1.0\t0.5\tactive\n")
    return str(tmp_path)

def test_get_subject_epoch_counts(mock_bids_root):
    counts = get_subject_epoch_counts(mock_bids_root)
    assert 'sub-01' in counts
    assert 'sub-02' in counts
    assert 'sub-03' in counts
    # Check approximate counts (might vary if parsing logic changes)
    assert counts['sub-01'] == 50
    assert counts['sub-02'] == 100
    assert counts['sub-03'] == 150

def test_select_subjects_for_memory_limit_deterministic(mock_bids_root):
    """Test that selection is deterministic and sorts by epoch count descending."""
    # We want min_epochs=100. 
    # Sorted: sub-03 (150), sub-02 (100), sub-01 (50)
    # Expected: sub-03 (150 >= 100) -> Stop.
    selected = select_subjects_for_memory_limit(
        mock_bids_root, 
        max_ram_gb=10.0, # High enough to not hit RAM limit
        min_epochs=100,
        avg_bytes_per_epoch=1000 # Small to not hit RAM limit
    )
    assert len(selected) == 1
    assert selected[0] == 'sub-03'

def test_select_subjects_for_memory_limit_ram_constraint(mock_bids_root):
    """Test selection stops due to RAM constraint."""
    # Set a very low RAM limit
    selected = select_subjects_for_memory_limit(
        mock_bids_root,
        max_ram_gb=0.001, # 1 MB - effectively 0
        min_epochs=1000,
        avg_bytes_per_epoch=1000000000 # 1GB per epoch (huge)
    )
    # Should select nothing or very few
    # With 1GB per epoch and 1MB limit, should select 0
    assert len(selected) == 0

def test_validate_epoch_counts():
    # Mock epochs object
    class MockEpochs:
        def __len__(self):
            return 100
    
    epochs = MockEpochs()
    assert validate_epoch_counts(epochs, 100) is True
    assert validate_epoch_counts(epochs, 101) is False

def test_log_epoch_rejection_rate(tmp_path):
    output_file = tmp_path / "rejection_report.json"
    log_epoch_rejection_rate(100, 10, str(output_file))
    assert output_file.exists()
    import json
    with open(output_file) as f:
        data = json.load(f)
    assert data['total_epochs'] == 100
    assert data['rejected_epochs'] == 10
    assert abs(data['rejection_rate'] - 0.1) < 1e-6
    assert 'timestamp' in data