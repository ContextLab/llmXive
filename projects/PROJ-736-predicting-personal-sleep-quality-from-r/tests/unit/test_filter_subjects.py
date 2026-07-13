import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the function to test
from data.download_hcp import filter_subjects

def test_filter_subjects_valid_data():
    """Test filtering with valid Sleep Scores and FD."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "behavioral.csv")
        output_path = os.path.join(tmpdir, "filtered.txt")
        
        # Create a mock behavioral dataframe
        data = {
            'Subject': ['100307', '100408', '100509', '100610'],
            'SleepScore': [7.5, 8.2, 6.0, 9.1],
            'MeanFD': [0.1, 0.2, 0.4, 0.15]  # 0.4 is > 0.3
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        subjects = filter_subjects(input_path, output_path, fd_threshold=0.3)
        
        # Expected: 100307, 100408, 100610 (FD <= 0.3)
        # Excluded: 100509 (FD = 0.4)
        expected = ['100307', '100408', '100610']
        
        assert subjects == expected
        
        # Verify file content
        with open(output_path, 'r') as f:
            file_content = [line.strip() for line in f.readlines()]
        assert file_content == expected

def test_filter_subjects_missing_sleep():
    """Test filtering with missing Sleep Score."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "behavioral.csv")
        output_path = os.path.join(tmpdir, "filtered.txt")
        
        data = {
            'Subject': ['100307', '100408'],
            'SleepScore': [7.5, None],
            'MeanFD': [0.1, 0.1]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        subjects = filter_subjects(input_path, output_path, fd_threshold=0.3)
        
        # Only 100307 should be valid
        assert subjects == ['100307']

def test_filter_subjects_column_detection():
    """Test column detection with different naming."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "behavioral.csv")
        output_path = os.path.join(tmpdir, "filtered.txt")
        
        # Use different column names
        data = {
            'HCP_Subject': ['100307', '100408'],
            'Sleep_Quality': [7.5, 8.0],
            'FramewiseDisplacement': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        subjects = filter_subjects(input_path, output_path, fd_threshold=0.3)
        assert subjects == ['100307', '100408']

def test_filter_subjects_missing_file():
    """Test that FileNotFoundError is raised if input missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "nonexistent.csv")
        output_path = os.path.join(tmpdir, "filtered.txt")
        
        with pytest.raises(FileNotFoundError):
            filter_subjects(input_path, output_path)