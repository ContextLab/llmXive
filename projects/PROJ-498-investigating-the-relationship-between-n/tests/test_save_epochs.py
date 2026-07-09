"""
Tests for T019: Save clean epochs.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from save_epochs import (
    load_processed_subject_data,
    save_clean_epochs,
    get_subjects_to_process,
    main
)
from config import ensure_directories

def test_save_clean_epochs_integration():
    """
    Integration test: Ensure the script runs without crashing and creates output files.
    """
    # Create a temporary directory structure for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup directories
        data_raw = tmpdir / "data" / "raw"
        data_processed = tmpdir / "data" / "processed"
        data_raw.mkdir(parents=True)
        data_processed.mkdir(parents=True)
        
        # Mock data: Create a fake intermediate epoch file
        # Since we can't easily create a real .fif without MNE in this test env,
        # we will mock the mne.read_epochs and mne.Epochs.save calls.
        
        mock_epochs = MagicMock()
        mock_epochs.save = MagicMock()
        
        # Create a dummy file to represent the "loaded" data
        dummy_file = data_raw / "sub-01_cleaned_epochs.fif"
        dummy_file.touch()
        
        # Patch mne
        with patch('save_epochs.mne') as mock_mne:
            mock_mne.read_epochs.return_value = mock_epochs
            mock_mne.Epochs = MagicMock()
            
            # Run the save function directly
            data = {"epochs": mock_epochs, "path": str(dummy_file)}
            result_path = save_clean_epochs("01", data, data_processed)
            
            assert result_path is not None, "save_clean_epochs should return a path"
            assert "sub-01_clean_epochs.fif" in result_path
            mock_epochs.save.assert_called_once()
            
            # Verify file exists
            assert Path(result_path).exists()

def test_get_subjects_to_process():
    """
    Test subject discovery logic.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_raw = tmpdir / "data" / "raw"
        data_raw.mkdir(parents=True)
        
        # Create dummy subject files
        (data_raw / "sub-01_task-switching_eeg.fif").touch()
        (data_raw / "sub-02_task-switching_eeg.fif").touch()
        (data_raw / "readme.txt").touch()
        
        # Patch the global DATA_RAW_DIR
        with patch('save_epochs.DATA_RAW_DIR', data_raw):
            subjects = get_subjects_to_process()
            
            assert "01" in subjects
            assert "02" in subjects
            assert len(subjects) == 2

def test_exclusion_logic_integration():
    """
    Test that excluded subjects are skipped.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        data_raw = tmpdir / "data" / "raw"
        data_processed = tmpdir / "data" / "processed"
        data_raw.mkdir(parents=True)
        data_processed.mkdir(parents=True)
        
        # Create dummy file
        (data_raw / "sub-01_task-switching_eeg.fif").touch()
        (data_raw / "sub-02_task-switching_eeg.fif").touch()
        
        # Create exclusions file
        exclusions_file = tmpdir / "data" / "exclusions.csv"
        exclusions_file.parent.mkdir(parents=True)
        with open(exclusions_file, "w") as f:
            f.write("subject_id,reason\n02,insufficient trials\n")
        
        # Patch paths
        with patch('save_epochs.DATA_RAW_DIR', data_raw):
            with patch('save_epochs.DATA_PROCESSED_DIR', data_processed):
                with patch('save_epochs.EXCLUSIONS_FILE', exclusions_file):
                    # We need to mock mne to avoid import errors in test
                    with patch('save_epochs.mne') as mock_mne:
                        mock_epochs = MagicMock()
                        mock_epochs.save = MagicMock()
                        mock_mne.read_epochs.return_value = mock_epochs
                        
                        # Run main
                        main()
                        
                        # Check that save was called only for sub-01
                        # We can verify by checking the call count or by inspecting logs/files
                        # Since we can't easily capture logs here, we rely on the file count
                        saved_files = list(data_processed.glob("*.fif"))
                        assert len(saved_files) == 1
                        assert "sub-01" in saved_files[0].name

if __name__ == "__main__":
    test_save_clean_epochs_integration()
    test_get_subjects_to_process()
    test_exclusion_logic_integration()
    print("All tests passed.")