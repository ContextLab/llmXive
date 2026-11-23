import os
import sys
import tempfile
import pytest
from pathlib import Path
import yaml

# Add parent to path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from data.download import verify_dataset_integrity, main, download_dataset

class TestDatasetVerification:
    def test_verify_present_file(self, tmp_path):
        """Test that verification passes when required file exists."""
        # Create a dummy dataset structure
        dataset_dir = tmp_path / "ds000246"
        dataset_dir.mkdir()
        sub_dir = dataset_dir / "sub-01"
        sub_dir.mkdir()
        (sub_dir / "gaze.tsv").write_text("x\ty\n1\t2")
        
        exists, missing = verify_dataset_integrity(str(dataset_dir), ["gaze.tsv"])
        assert exists is True
        assert len(missing) == 0

    def test_verify_missing_file_raises(self, tmp_path):
        """Test that verification fails and lists missing file when gaze.tsv is absent."""
        dataset_dir = tmp_path / "ds000246"
        dataset_dir.mkdir()
        sub_dir = dataset_dir / "sub-01"
        sub_dir.mkdir()
        (sub_dir / "eeg_data.tsv").write_text("data") # Wrong file
        
        exists, missing = verify_dataset_integrity(str(dataset_dir), ["gaze.tsv"])
        assert exists is False
        assert "gaze.tsv" in missing

    def test_main_halts_on_missing_gaze(self, tmp_path, monkeypatch):
        """
        Integration test for the strict verification gate in main().
        Simulates a download that results in a directory without gaze.tsv.
        """
        # Mock download_dataset to return a directory without gaze.tsv
        def mock_download(dataset_id, target_dir):
            path = Path(target_dir) / dataset_id
            path.mkdir(parents=True, exist_ok=True)
            (path / "sub-01").mkdir(parents=True, exist_ok=True)
            (path / "sub-01" / "eeg").mkdir(parents=True, exist_ok=True)
            (path / "sub-01" / "eeg" / "sub-01_eeg.tsv").write_text("data")
            return str(path)
        
        monkeypatch.setattr("data.download.download_dataset", mock_download)
        
        # We expect main to raise FileNotFoundError because gaze.tsv is missing
        with pytest.raises(FileNotFoundError, match="VERIFICATION FAILED"):
            main()
