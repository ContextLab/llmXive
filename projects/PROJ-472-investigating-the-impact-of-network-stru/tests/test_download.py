import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the config to use a temp directory
from unittest.mock import patch, MagicMock

def test_match_subjects_logic():
    """
    Tests the logic of subject matching between dMRI and EEG.
    """
    from data.download import match_subjects, write_routing_state
    
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir)
        
        # Create fake directories
        dMRI_dir = data_root / "raw" / "ds004230"
        eeg_dir = data_root / "raw" / "ds004231"
        processed_dir = data_root / "processed"
        processed_dir.mkdir(parents=True)
        
        dMRI_dir.mkdir(parents=True)
        eeg_dir.mkdir(parents=True)
        
        # Create sub-01 in both
        (dMRI_dir / "sub-01").mkdir()
        (eeg_dir / "sub-01").mkdir()
        
        # Create sub-02 only in dMRI
        (dMRI_dir / "sub-02").mkdir()
        
        # Create sub-03 only in EEG
        (eeg_dir / "sub-03").mkdir()
        
        result = match_subjects(dMRI_dir, eeg_dir)
        
        assert "sub-01" in result['matched_subjects']
        assert "sub-02" in result['dMRI_subjects']
        assert "sub-03" in result['EEG_subjects']
        assert len(result['matched_subjects']) == 1
        assert result['simulation_required'] == False
        
        # Test simulation required case
        shutil.rmtree(eeg_dir)
        eeg_dir.mkdir() # Empty
        
        result = match_subjects(dMRI_dir, eeg_dir)
        assert result['simulation_required'] == True
        assert len(result['matched_subjects']) == 0

def test_write_routing_state():
    """
    Tests that routing_state.json is written correctly.
    """
    from data.download import write_routing_state
    
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir)
        processed_dir = data_root / "processed"
        processed_dir.mkdir()
        
        match_result = {
            'dMRI_subjects': ['sub-01', 'sub-02'],
            'EEG_subjects': ['sub-01'],
            'matched_subjects': ['sub-01'],
            'simulation_required': False
        }
        
        write_routing_state(data_root, match_result)
        
        routing_file = processed_dir / "routing_state.json"
        assert routing_file.exists()
        
        with open(routing_file) as f:
            state = json.load(f)
        
        assert state['simulation_required'] == False
        assert state['matched_subjects'] == ['sub-01']
        assert state['dMRI_available'] == True
        assert state['EEG_available'] == True