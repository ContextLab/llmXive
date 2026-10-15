import os
import pytest
from pathlib import Path
from download import download_sleep_edf

@pytest.mark.timeout(300)
def test_download_small_subset(tmp_path, monkeypatch):
    """
    Verify that the download function can retrieve a small subset (2 recordings)
    without raising and that the log file is created.
    """
    # Use a temporary directory to avoid polluting the repository.
    out_dir = tmp_path / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Patch the configuration loader to avoid reading the real config file.
    monkeypatch.setattr("config_utils.load_config", lambda: {})

    # Request only 2 recordings to keep the test fast.
    successful, errors = download_sleep_edf(output_dir=str(out_dir), n_subjects=2)

    # At least one file should be successfully downloaded.
    assert len(successful) >= 1, "No files were downloaded successfully."

    # The log file must exist and contain the same number of lines as
    # successful + error entries.
    log_path = out_dir / "download_log.txt"
    assert log_path.is_file(), "download_log.txt was not created."

    with open(log_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    assert len(lines) == len(successful) + len(errors), "Log line count mismatch."