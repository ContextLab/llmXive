import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from extract_facial import run_openface_on_video, aggregate_facial_features, main

def test_run_openface_on_video_missing_file():
    """Test that run_openface_on_video handles missing input files gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_openface_on_video("nonexistent_video.mp4", tmpdir)
        assert result is None

def test_aggregate_facial_features_empty():
    """Test aggregation with no CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.csv")
        aggregate_facial_features(tmpdir, output_path)
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert df.empty

def test_aggregate_facial_features_valid():
    """Test aggregation with valid CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy CSV files
        df1 = pd.DataFrame({
            'timestamp': [1, 2, 3],
            'value': [0.1, 0.2, 0.3]
        })
        df1_path = os.path.join(tmpdir, "video1.csv")
        df1.to_csv(df1_path, index=False)

        df2 = pd.DataFrame({
            'timestamp': [1, 2],
            'value': [0.4, 0.5]
        })
        df2_path = os.path.join(tmpdir, "video2.csv")
        df2.to_csv(df2_path, index=False)

        output_path = os.path.join(tmpdir, "output.csv")
        aggregate_facial_features(tmpdir, output_path)

        assert os.path.exists(output_path)
        result_df = pd.read_csv(output_path)
        assert not result_df.empty
        assert 'video_id' in result_df.columns
        assert len(result_df) == 5  # 3 rows from video1 + 2 from video2

@patch('extract_facial.subprocess.run')
def test_run_openface_on_video_success(mock_run):
    """Test successful OpenFace execution flow."""
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy output CSV to simulate OpenFace output
        output_csv = os.path.join(tmpdir, "test_video.csv")
        pd.DataFrame({'timestamp': [1, 2], 'AU01_r': [0.5, 0.6]}).to_csv(output_csv, index=False)
        
        # Mock the video path
        video_path = os.path.join(tmpdir, "test_video.mp4")
        # Create a dummy video file so glob finds it (though we mock subprocess)
        Path(video_path).touch()
        
        result = run_openface_on_video(video_path, tmpdir)
        
        # Since we mocked subprocess, we need to ensure the file exists for the check
        # In a real scenario, subprocess would create it. Here we manually create it for the test logic.
        # The function checks if the file exists after subprocess.run
        
        assert result == output_csv
        mock_run.assert_called_once()
