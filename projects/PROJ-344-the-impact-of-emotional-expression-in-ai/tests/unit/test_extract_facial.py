"""
Unit tests for the facial feature extraction module (T013).

These tests verify the logic of the extraction pipeline without
requiring the actual OpenFace binary to be installed in the test environment.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from extract_facial import (
    get_openface_command,
    extract_features_from_video,
    consolidate_features,
    run_facial_extraction
)
from logging_config import setup_logging

# Setup logging for tests
setup_logging()

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test inputs and outputs."""
    base = tempfile.mkdtemp()
    input_dir = Path(base) / "input"
    output_dir = Path(base) / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    yield {
        "base": base,
        "input": input_dir,
        "output": output_dir
    }
    shutil.rmtree(base)

def test_get_openface_command_found_in_path():
    """Test that the command is constructed correctly when openface is in PATH."""
    with patch('extract_facial.shutil.which', return_value='/usr/bin/openface'):
        cmd = get_openface_command()
        assert cmd == ['/usr/bin/openface']

def test_get_openface_command_not_found():
    """Test that an error is raised when openface is not found."""
    with patch('extract_facial.shutil.which', return_value=None):
        with patch('extract_facial.os.environ.get', return_value=None):
            with pytest.raises(RuntimeError, match="OpenFace binary not found"):
                get_openface_command()

def test_extract_features_from_video_nonexistent():
    """Test handling of non-existent video file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output"
        output_path.mkdir()
        fake_video = Path(tmpdir) / "fake.mp4"
        
        result = extract_features_from_video(fake_video, output_path)
        assert result is None

def test_extract_features_from_video_unsupported_format():
    """Test handling of unsupported video format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output"
        output_path.mkdir()
        fake_video = Path(tmpdir) / "fake.txt"
        fake_video.touch()
        
        result = extract_features_from_video(fake_video, output_path)
        assert result is None

@patch('extract_facial.subprocess.run')
@patch('extract_facial.Path.glob')
@patch('extract_facial.Path.exists', return_value=True)
def test_extract_features_from_video_success(mock_exists, mock_glob, mock_run, temp_dirs):
    """Test successful extraction flow."""
    # Mock subprocess to return success
    mock_run.return_value = MagicMock(returncode=0, stdout="Success")
    
    # Mock the glob to find a CSV file
    mock_csv = MagicMock()
    mock_csv.name = "test_video_face.csv"
    mock_glob.return_value = [mock_csv]
    
    # Create a dummy video file
    video_path = temp_dirs["input"] / "test_video.mp4"
    video_path.touch()
    
    # Mock the file reading for consolidate step (not needed here but good practice)
    with patch('extract_facial.Path.mkdir', return_value=None):
        result = extract_features_from_video(video_path, temp_dirs["output"])
        
    assert result is not None
    # Verify subprocess was called
    assert mock_run.called

@patch('extract_facial.pd.read_csv')
@patch('extract_facial.Path.glob')
@patch('extract_facial.Path.mkdir', return_value=None)
@patch('extract_facial.Path.exists', return_value=True)
def test_consolidate_features_success(mock_exists, mock_mkdir, mock_glob, mock_read_csv, temp_dirs):
    """Test successful consolidation of features."""
    # Create a mock DataFrame
    mock_df = pd.DataFrame({
        'video_id': ['test'],
        'timestamp': [1.0],
        'AU01_r': [0.5]
    })
    mock_read_csv.return_value = mock_df
    
    # Mock glob to find the CSV
    mock_csv = MagicMock()
    mock_csv.name = "test_video_face.csv"
    mock_glob.return_value = [mock_csv]
    
    # Create a dummy directory structure
    video_dir = temp_dirs["output"] / "test_video"
    video_dir.mkdir()
    (video_dir / "test_video_face.csv").touch()
    
    output_csv = temp_dirs["output"] / "facial_features.csv"
    
    success = consolidate_features(temp_dirs["output"], output_csv)
    
    assert success is True
    assert output_csv.exists()
    
    # Verify the content
    result_df = pd.read_csv(output_csv)
    assert 'video_id' in result_df.columns
    assert len(result_df) == 1

def test_consolidate_features_no_files(temp_dirs):
    """Test consolidation when no files are found."""
    output_csv = temp_dirs["output"] / "facial_features.csv"
    success = consolidate_features(temp_dirs["output"], output_csv)
    assert success is False

@patch('extract_facial.run_facial_extraction')
def test_main_success(mock_run):
    """Test main function success path."""
    mock_run.return_value = True
    with patch('sys.exit') as mock_exit:
        from extract_facial import main
        main()
        mock_exit.assert_called_with(0)

@patch('extract_facial.run_facial_extraction')
def test_main_failure(mock_run):
    """Test main function failure path."""
    mock_run.return_value = False
    with patch('sys.exit') as mock_exit:
        from extract_facial import main
        main()
        mock_exit.assert_called_with(1)