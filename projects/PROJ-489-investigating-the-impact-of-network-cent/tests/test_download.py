import os
import json
from pathlib import Path

from download import download_sleep_edf

def test_download_creates_log_and_files(tmp_path, monkeypatch):
    """
    Integration test for the download script.

    - Uses a temporary directory to avoid polluting the repository.
    - Calls ``download_sleep_edf`` with a small number of recordings (2)
      to keep the test fast.
    - Checks that the log file is created and contains a checksum entry
      for each successfully downloaded file.
    - Verifies that corrupted files are logged with the ``ERROR`` prefix
      (simulated by monkey‑patching ``mne.io.read_raw_edf`` to raise).
    """
    # Use a tiny subset to keep runtime low; the real dataset is large.
    # The function will still attempt a real download, but only for two
    # recordings which fit within the CI time limits.
    output_dir = tmp_path / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Monkey‑patch MNE's EDF reader to simulate a corrupted file for the
    # first download while allowing the second to succeed.
    import mne.io

    original_reader = mne.io.read_raw_edf

    def fake_reader(path, *args, **kwargs):
        if "sleep-edfx-01-00" in str(path):
            raise IOError("Simulated corruption")
        return original_reader(path, *args, **kwargs)

    monkeypatch.setattr(mne.io, "read_raw_edf", fake_reader)

    # Run the download (requesting exactly 2 recordings)
    successful, errors = download_sleep_edf(output_dir=str(output_dir), n_subjects=2)

    # Verify log file exists
    log_path = output_dir / "download_log.txt"
    assert log_path.is_file(), "download_log.txt should be created"

    # Load log contents
    with open(log_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Should contain one SUCCESS line and one ERROR line
    assert any("\t" in line and not line.startswith("ERROR") for line in lines), "At least one successful checksum line expected"
    assert any(line.startswith("ERROR") for line in lines), "At least one error line expected"

    # The function should return matching lists
    assert isinstance(successful, list)
    assert isinstance(errors, list)
    assert len(successful) + len(errors) == 2

    # Clean up monkey‑patch
    monkeypatch.setattr(mne.io, "read_raw_edf", original_reader)