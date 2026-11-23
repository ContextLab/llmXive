"""
Unit tests for T009: download_clips.py
"""
import os
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import cv2

# Import the module under test
# We need to ensure the path is set up correctly if running from root
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data_curation.download_clips import (
    load_verification_pool,
    stratified_sample,
    extract_clip_from_frames,
    main
)

def test_load_verification_pool_missing_file():
    """Test that load_verification_pool raises FileNotFoundError if file is missing."""
    with patch('code.data_curation.download_clips.INPUT_POOL_PATH', Path('/nonexistent/pool.csv')):
        try:
            load_verification_pool()
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError as e:
            assert "Verification pool not found" in str(e)

def test_load_verification_pool_valid():
    """Test loading a valid verification pool."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pool_path = Path(tmpdir) / "pool.csv"
        data = {
            'video_id': ['v1', 'v2', 'v3', 'v4'],
            'source_dataset': ['kinetics', 'kinetics', 'ucf101', 'ucf101'],
            'label': ['continuous', 'cut', 'continuous', 'cut']
        }
        df_input = pd.DataFrame(data)
        df_input.to_csv(pool_path, index=False)
        
        with patch('code.data_curation.download_clips.INPUT_POOL_PATH', pool_path):
            df_out = load_verification_pool()
            assert len(df_out) == 4
            assert set(df_out['label']) == {'continuous', 'cut'}

def test_stratified_sample_balanced():
    """Test that stratified_sample returns equal numbers of each class."""
    data = {
        'video_id': [f'v{i}' for i in range(10)],
        'source_dataset': ['kinetics'] * 10,
        'label': ['continuous'] * 5 + ['cut'] * 5
    }
    df = pd.DataFrame(data)
    
    sampled = stratified_sample(df, target_size=4)
    assert len(sampled) == 4
    assert sampled['label'].value_counts()['continuous'] == 2
    assert sampled['label'].value_counts()['cut'] == 2

def test_stratified_sample_unbalanced_pool():
    """Test stratified sampling when one class is smaller."""
    data = {
        'video_id': [f'v{i}' for i in range(6)],
        'source_dataset': ['kinetics'] * 6,
        'label': ['continuous'] * 5 + ['cut'] * 1
    }
    df = pd.DataFrame(data)
    
    # Target 4, but only 1 cut available -> max 2 total
    sampled = stratified_sample(df, target_size=4)
    assert len(sampled) == 2
    assert sampled['label'].value_counts()['cut'] == 1
    assert sampled['label'].value_counts()['continuous'] == 1

def test_extract_clip_from_frames():
    """Test that extract_clip_from_frames creates a valid video file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.mp4"
        
        # Create dummy frames
        frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(50)]
        
        result = extract_clip_from_frames(frames, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify it can be read by OpenCV
        cap = cv2.VideoCapture(str(output_path))
        assert cap.isOpened()
        frame_count = 0
        while True:
            ret, _ = cap.read()
            if not ret:
                break
            frame_count += 1
        cap.release()
        assert frame_count == 50

def test_main_execution_structure():
    """Test that main() runs without crashing if data sources are mocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup input pool
        pool_path = Path(tmpdir) / "pool.csv"
        data = {
            'video_id': ['v1', 'v2'],
            'source_dataset': ['kinetics', 'ucf101'],
            'label': ['continuous', 'cut']
        }
        pd.DataFrame(data).to_csv(pool_path, index=False)
        
        output_dir = Path(tmpdir) / "clips"
        manifest_path = output_dir / "sampling_manifest.json"
        
        # Mock the download functions to return True and create dummy files
        with patch('code.data_curation.download_clips.INPUT_POOL_PATH', pool_path):
            with patch('code.data_curation.download_clips.OUTPUT_DIR', output_dir):
                with patch('code.data_curation.download_clips.download_kinetics_clip') as mock_kin:
                    with patch('code.data_curation.download_clips.download_ucf101_clip') as mock_ucf:
                        mock_kin.return_value = True
                        mock_ucf.return_value = True
                        
                        # Create dummy output files for the mocks
                        def create_dummy(path):
                            # Create a minimal valid mp4 header or just a file
                            # For testing existence, a file is enough, but extract_clip_from_frames expects a valid video
                            # We'll rely on the mock returning True, but we need the file to exist for hash check
                            # Let's just create an empty file here for the test to pass the path check
                            # Actually, the mock returns True, but the real code tries to hash it.
                            # So we need to ensure the file exists.
                            pass
                        
                        # We need to patch the file creation logic or just ensure the mock creates the file
                        # Since we can't easily mock the internal file writing of extract_clip_from_frames
                        # without refactoring, let's just patch the hash function to avoid file read errors
                        with patch('code.data_curation.download_clips.compute_sha256', return_value="dummy_hash"):
                            with patch('code.data_curation.download_clips.extract_clip_from_frames', return_value=True):
                                # We also need to ensure the file exists for the mock to be valid
                                # Let's patch the download functions to create the file
                                def mock_kin_real(video_id, path):
                                    Path(path).touch()
                                    return True
                                def mock_ucf_real(video_id, path):
                                    Path(path).touch()
                                    return True
                                
                                mock_kin.side_effect = mock_kin_real
                                mock_ucf.side_effect = mock_ucf_real
                                
                                result = main()
                                
                                assert result is True
                                assert manifest_path.exists()
                                
                                with open(manifest_path) as f:
                                    manifest = json.load(f)
                                    assert manifest['successful'] == 2
                                    assert len(manifest['failed_ids']) == 0