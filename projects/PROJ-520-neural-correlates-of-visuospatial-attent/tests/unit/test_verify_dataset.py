import pytest
import os
import json
import tempfile
from pathlib import Path
from verify_dataset import check_bids_structure, check_event_markers, VerificationError

def test_check_bids_structure_valid():
    """Test BIDS validation with a valid structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create required files
        (root / 'dataset_description.json').write_text('{}')
        (root / 'participants.tsv').write_text('participant_id\nsub-01')
        (root / 'sub-01').mkdir()
        
        result = check_bids_structure(str(root))
        assert result['valid'] is True
        assert len(result['issues']) == 0
        assert result['subject_count'] == 1

def test_check_bids_structure_missing_files():
    """Test BIDS validation with missing required files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create only one required file
        (root / 'dataset_description.json').write_text('{}')
        
        result = check_bids_structure(str(root))
        assert result['valid'] is False
        assert any('participants.tsv' in issue for issue in result['issues'])

def test_check_event_markers_found():
    """Test event marker detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / 'dataset_description.json').write_text('{}')
        sub_dir = root / 'sub-01'
        sub_dir.mkdir()
        func_dir = sub_dir / 'func'
        func_dir.mkdir()
        (func_dir / 'events.tsv').write_text('onset\tduration\ttrial_type')
        
        result = check_event_markers(str(root))
        assert result['valid'] is True
        assert len(result['markers']) == 1
        assert result['source'] == 'events.tsv'

def test_check_event_markers_missing_raises():
    """Test that missing event markers raise an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / 'dataset_description.json').write_text('{}')
        (root / 'sub-01').mkdir()
        
        with pytest.raises(VerificationError) as excinfo:
            check_event_markers(str(root))
        
        assert "Missing event markers" in str(excinfo.value)
