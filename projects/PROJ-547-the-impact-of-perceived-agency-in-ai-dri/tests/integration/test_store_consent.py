"""
Integration test for the ``store_consent`` script (Task T060).

The test verifies that:
1. The consent PDF is downloaded to ``data/consent/consent_document.pdf``.
2. Its SHA‑256 checksum is recorded in ``data/metadata.yaml`` under the
   key ``consent_checksum``.
3. A log entry with ``event == "consent_stored"`` exists in the most recent
   run log and contains the same checksum.
"""
import json
import pathlib
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

# The script under test
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "code" / "logging" / "store_consent.py"

# Helper to compute SHA‑256 of a file
def file_checksum(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

@pytest.fixture(autouse=True)
def clean_environment(tmp_path_factory):
    """
    Ensure a clean ``data`` and ``logs`` directory for each test run.
    The fixture runs before each test and restores the original state after.
    """
    project_root = Path(__file__).resolve().parents[2]

    # Backup existing data/ and logs/ if they exist
    backup_dir = tmp_path_factory.mktemp("backup")
    data_dir = project_root / "data"
    logs_dir = project_root / "logs"

    if data_dir.is_dir():
        shutil.move(str(data_dir), backup_dir / "data")
    if logs_dir.is_dir():
        shutil.move(str(logs_dir), backup_dir / "logs")

    # Ensure fresh empty directories
    (project_root / "data" / "consent").mkdir(parents=True, exist_ok=True)
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    yield  # run the test

    # Restore original directories
    if (backup_dir / "data").exists():
        if data_dir.exists():
            shutil.rmtree(data_dir)
        shutil.move(str(backup_dir / "data"), data_dir)
    if (backup_dir / "logs").exists():
        if logs_dir.exists():
            shutil.rmtree(logs_dir)
        shutil.move(str(backup_dir / "logs"), logs_dir)

def test_store_consent_creates_files_and_logs():
    # Run the script as a subprocess to emulate real execution
    result = subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    project_root = Path(__file__).resolve().parents[2]

    consent_path = project_root / "data" / "consent" / "consent_document.pdf"
    metadata_path = project_root / "data" / "metadata.yaml"

    # 1. Consent PDF exists
    assert consent_path.is_file(), "Consent PDF was not created."

    # 2. Checksum recorded in metadata.yaml
    import yaml

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)
    assert "consent_checksum" in metadata, "Checksum key missing in metadata.yaml."

    expected_checksum = file_checksum(consent_path)
    assert metadata["consent_checksum"] == expected_checksum, "Checksum in metadata does not match file."

    # 3. Log entry exists
    logs_dir = project_root / "logs"
    log_files = sorted(logs_dir.glob("run_*.log"))
    assert log_files, "No log files created."

    # Read the most recent log file
    latest_log = log_files[-1]
    with latest_log.open("r", encoding="utf-8") as f:
        log_entries = [json.loads(line) for line in f if line.strip()]

    consent_logs = [e for e in log_entries if e.get("event") == "consent_stored"]
    assert consent_logs, "No consent_stored event logged."

    # Verify the logged checksum matches the computed checksum
    logged_checksum = consent_logs[0].get("checksum")
    assert logged_checksum == expected_checksum, "Logged checksum does not match computed checksum."