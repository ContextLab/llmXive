import os
import sys
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path
import logging

# Add code directory to path
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from src.data.extract_audio import extract_audio_features, process_audio_clips
from src.utils import setup_logging

@pytest.fixture
def temp_audio_dir():
    """Create a temporary directory with dummy audio files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy wav file (just bytes, not a real valid wav, to test error handling)
        # Or create a minimal valid one if librosa is strict. 
        # For this test, we want to test the logic, so we'll create a file that exists.
        # Since we can't easily generate a valid audio file without dependencies in a test fixture,
        # we will test the 'missing file' path and the 'file exists but fails load' path.
        
        # Create a fake file that exists
        fake_file = Path(tmpdir) / "test_clip.wav"
        fake_file.write_bytes(b"RIFF....WAVE") # Minimal header to make it a file, likely invalid for librosa
        
        yield tmpdir, str(fake_file)

def test_extract_audio_missing_file(temp_audio_dir, caplog):
    """Test that missing file sets missing_data_flag=True."""
    logger = setup_logging("test_extract_audio")
    logger.setLevel(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="extract_audio")
    
    clip_id = "missing_clip"
    dimension = "test_dim"
    missing_path = os.path.join(temp_audio_dir[0], "nonexistent.wav")
    
    result = extract_audio_features(missing_path, clip_id, dimension, logger)
    
    assert result["clip_id"] == clip_id
    assert result["dimension"] == dimension
    assert result["missing_data_flag"] is True
    assert result["feature_vector"] == []

def test_process_audio_clips_missing_files(temp_audio_dir):
    """Test processing a dataframe with missing files."""
    logger = setup_logging("test_process")
    
    # Create a mock dataframe
    data = {
        "clip_id": ["clip1", "clip2"],
        "dimension": ["dim1", "dim2"],
        "file_path": [
            os.path.join(temp_audio_dir[0], "clip1.wav"), # Exists but invalid
            os.path.join(temp_audio_dir[0], "clip2.wav")  # Does not exist
        ]
    }
    
    # Create the first file
    Path(temp_audio_dir[0], "clip1.wav").write_bytes(b"RIFF....WAVE")
    
    df = pd.DataFrame(data)
    
    results = process_audio_clips(df, logger)
    
    assert len(results) == 2
    # Both should have missing_data_flag=True because either file doesn't exist or is invalid
    assert all(r["missing_data_flag"] for r in results)
    
    # Check clip_id mapping
    ids = [r["clip_id"] for r in results]
    assert "clip1" in ids
    assert "clip2" in ids