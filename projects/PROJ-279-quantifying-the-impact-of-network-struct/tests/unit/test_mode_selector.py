"""
Unit tests for the ModeSelector logic (T007b).

These tests verify the logic of mode selection without requiring a full
dataset download. They mock the file system interactions.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mode_selector import ModeSelector


@pytest.fixture
def temp_dirs():
    """Creates temporary directories for raw and processed data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        raw_dir = base / "raw"
        processed_dir = base / "processed"
        vdos_dir = processed_dir / "vdos"
        
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        vdos_dir.mkdir(parents=True)
        
        yield {
            'raw': raw_dir,
            'processed': processed_dir,
            'vdos': vdos_dir,
            'base': base
        }


def test_scan_config_ids(temp_dirs):
    """Test that _scan_config_ids correctly identifies files in raw/."""
    # Create dummy files
    (temp_dirs['raw'] / "config1.xyz").touch()
    (temp_dirs['raw'] / "config2.json").touch()
    (temp_dirs['raw'] / "config3.dat").touch()
    (temp_dirs['raw'] / "ignored.txt").touch() # Should be ignored
    
    selector = ModeSelector(data_dir=temp_dirs['base'])
    ids = selector._scan_config_ids()
    
    assert len(ids) == 3
    assert set(ids) == {"config1", "config2", "config3"}


def test_check_vdos_availability_partial(temp_dirs):
    """Test VDOS availability check with partial data."""
    config_ids = ["config1", "config2", "config3"]
    
    # Create VDOS for only config1 and config3
    (temp_dirs['vdos'] / "config1_vdos.json").touch()
    (temp_dirs['vdos'] / "config3_vdos.json").touch()
    
    selector = ModeSelector(data_dir=temp_dirs['base'], processed_dir=temp_dirs['base'] / "processed")
    status, fraction = selector._check_vdos_availability(config_ids)
    
    assert status["config1"] is True
    assert status["config2"] is False
    assert status["config3"] is True
    assert fraction == pytest.approx(2/3)


def test_determine_mode_full(temp_dirs):
    """Test Full mode determination when thresholds are met."""
    config_ids = [f"config{i}" for i in range(100)]
    
    # Create VDOS and metadata for 90% (90 configs)
    for i in range(90):
        (temp_dirs['vdos'] / f"config{i}_vdos.json").touch()
    
    # Create metadata.json with k_values for 90 configs
    metadata = [{"id": f"config{i}", "k_value": 1.5} for i in range(90)]
    with open(temp_dirs['raw'] / "metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # Create raw files for all 100
    for i in range(100):
        (temp_dirs['raw'] / f"config{i}.xyz").touch()
        
    selector = ModeSelector(data_dir=temp_dirs['base'], processed_dir=temp_dirs['base'] / "processed")
    report = selector.determine_mode()
    
    assert report['mode'] == 'Full'
    assert report['vdos_fraction'] == pytest.approx(0.90)
    assert report['k_fraction'] == pytest.approx(0.90)
    assert 'Full mode enabled' in report['reason']


def test_determine_mode_structure_only(temp_dirs):
    """Test Structure-Only mode when VDOS is missing."""
    config_ids = [f"config{i}" for i in range(100)]
    
    # Create VDOS for only 50% (50 configs)
    for i in range(50):
        (temp_dirs['vdos'] / f"config{i}_vdos.json").touch()
    
    # Create metadata for 100%
    metadata = [{"id": f"config{i}", "k_value": 1.5} for i in range(100)]
    with open(temp_dirs['raw'] / "metadata.json", 'w') as f:
        json.dump(metadata, f)
        
    for i in range(100):
        (temp_dirs['raw'] / f"config{i}.xyz").touch()
        
    selector = ModeSelector(data_dir=temp_dirs['base'], processed_dir=temp_dirs['base'] / "processed")
    report = selector.determine_mode()
    
    assert report['mode'] == 'Structure-Only'
    assert report['vdos_fraction'] == pytest.approx(0.50)
    assert 'Structure-Only mode enabled' in report['reason']


def test_determine_mode_no_data(temp_dirs):
    """Test default behavior when no data is present."""
    selector = ModeSelector(data_dir=temp_dirs['base'], processed_dir=temp_dirs['base'] / "processed")
    report = selector.determine_mode()
    
    assert report['mode'] == 'Structure-Only'
    assert report['vdos_fraction'] == 0.0
    assert 'No configurations found' in report['reason']


def test_save_mode_report(temp_dirs):
    """Test that the report is saved correctly to JSON."""
    # Setup minimal data
    (temp_dirs['raw'] / "config1.xyz").touch()
    selector = ModeSelector(data_dir=temp_dirs['base'], processed_dir=temp_dirs['base'] / "processed")
    
    output_path = selector.save_mode_report()
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'mode' in data
    assert 'reason' in data
    assert data['mode'] == 'Structure-Only' # Since no VDOS/k present