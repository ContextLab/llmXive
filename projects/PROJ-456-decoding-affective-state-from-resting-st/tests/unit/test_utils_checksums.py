import os
import json
import hashlib
import tempfile
from pathlib import Path

from code.utils import record_checksums, compute_sha256

def test_record_checksums_creates_file():
    # Create a temporary directory to hold a fake EEG file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a small file with known content
        eeg_file = tmp_path / "subject1_eeg.fif"
        content = b"test content for checksum"
        with open(eeg_file, "wb") as f:
            f.write(content)

        # Compute expected SHA‑256 directly
        expected_hash = hashlib.sha256(content).hexdigest()

        # Build a minimal manifest JSON structure
        manifest = [
            {
                "dataset_id": "dummy_ds",
                "verification_status": "ready",
                "eeg_files": [str(eeg_file)],
                "questionnaire_files": [],
                "file_paths": {"root": str(tmp_path)}
            }
        ]

        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # Output path for checksums
        checksums_path = tmp_path / "checksums.json"

        # Run the checksum recording function
        record_checksums(str(manifest_path), str(checksums_path))

        # Verify the output file exists and contains the correct hash
        assert checksums_path.is_file()
        with open(checksums_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # The key should be the exact file path string we supplied
        assert str(eeg_file) in data
        assert data[str(eeg_file)] == expected_hash