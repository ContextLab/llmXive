"""
Unit tests for linkage derivation fallback (T016).
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from data.linkage import derive_stimulus_id_from_trial_id, run_linkage_derivation
from data.models import Trial

@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with mock image files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        # Create some mock image files
        # Format: img_<hash_suffix>.png
        (dir_path / "img_a1b2c3d4.png").touch()
        (dir_path / "img_e5f6g7h8.png").touch()
        (dir_path / "stimulus_001.png").touch()
        (dir_path / "stimulus_002.png").touch()
        (dir_path / "trial_abc123.png").touch()
        yield dir_path

def test_derive_stimulus_id_direct_match(temp_image_dir):
    """Test direct substring match in filename."""
    # Trial ID 'abc123' should match 'trial_abc123.png'
    result = derive_stimulus_id_from_trial_id("trial_abc123", temp_image_dir, "prime")
    assert result == "trial_abc123"

def test_derive_stimulus_id_hash_match(temp_image_dir):
    """Test hash-based derivation."""
    # We don't know the exact hash, but we can test the logic
    # by mocking the hash or using a known pattern.
    # For now, test that it doesn't crash and returns None if no match.
    result = derive_stimulus_id_from_trial_id("nonexistent_trial", temp_image_dir, "prime")
    assert result is None

def test_derive_stimulus_id_numeric_match(temp_image_dir):
    """Test numeric trial ID matching."""
    # Trial ID '1' should match 'stimulus_001.png' (difference 1)
    result = derive_stimulus_id_from_trial_id("1", temp_image_dir, "prime")
    # Depending on the exact logic, this might match or not.
    # The logic allows difference <= 5.
    # 'stimulus_001' -> 1. Difference is 0.
    assert result == "stimulus_001"

def test_run_linkage_derivation_missing_ids(temp_image_dir):
    """Test run_linkage_derivation with missing stimulus IDs."""
    trials = [
        Trial(trial_id="trial_abc123", response_time=500.0, stimulus_id=None, stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
        Trial(trial_id="trial_xyz789", response_time=600.0, stimulus_id=None, stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
        Trial(trial_id="trial_001", response_time=550.0, stimulus_id="existing_id", stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
    ]
    
    updated_trials, success_rate = run_linkage_derivation(trials, temp_image_dir, temp_image_dir)
    
    # First trial should be derived
    assert updated_trials[0].stimulus_id == "trial_abc123"
    # Second trial should be None (no match)
    assert updated_trials[1].stimulus_id is None
    # Third trial should remain unchanged
    assert updated_trials[2].stimulus_id == "existing_id"
    
    # success_rate = 1 derived / 2 missing = 0.5
    assert success_rate == 0.5

def test_run_linkage_derivation_no_missing():
    """Test run_linkage_derivation when no IDs are missing."""
    trials = [
        Trial(trial_id="trial_001", response_time=500.0, stimulus_id="id1", stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        updated_trials, success_rate = run_linkage_derivation(trials, dir_path, dir_path)
    
    assert updated_trials[0].stimulus_id == "id1"
    assert success_rate == 1.0

def test_run_linkage_derivation_high_failure_rate(temp_image_dir):
    """Test that high failure rate is handled (logic check, not halting here)."""
    trials = [
        Trial(trial_id="missing1", response_time=500.0, stimulus_id=None, stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
        Trial(trial_id="missing2", response_time=500.0, stimulus_id=None, stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
        Trial(trial_id="missing3", response_time=500.0, stimulus_id=None, stimulus_type="prime", prime_condition="neutral", participant_id="P1"),
    ]
    
    # All will fail to derive
    updated_trials, success_rate = run_linkage_derivation(trials, temp_image_dir, temp_image_dir)
    
    assert all(t.stimulus_id is None for t in updated_trials)
    assert success_rate == 0.0
