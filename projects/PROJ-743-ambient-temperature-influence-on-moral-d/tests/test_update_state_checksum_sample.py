import os
import sys
import tempfile
import hashlib
import yaml
from pathlib import Path
from datetime import datetime, timezone
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from utils import compute_sha256

def test_compute_sha256_correctness():
    """Test that compute_sha256 returns the correct hash for a known file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"test content for checksum"
        tmp.write(content)
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(Path(tmp_path))
        assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"
    finally:
        os.unlink(tmp_path)

def test_state_update_logic():
    """Test the logic of updating the state file with a checksum and timestamp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock sample file
        sample_file = Path(tmpdir) / "era5_sample.h5"
        sample_content = b"mock era5 sample data"
        sample_file.write_bytes(sample_content)

        # Create a mock state file
        state_file = Path(tmpdir) / "state.yaml"
        initial_state = {
            "artifact_hashes": {"era5_full": "some_old_hash"},
            "updated_at": "2023-01-01T00:00:00+00:00"
        }
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)

        # Simulate the logic from update_state_checksum_sample
        checksum = compute_sha256(sample_file)
        expected_hash = hashlib.sha256(sample_content).hexdigest()
        assert checksum == expected_hash

        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)

        state_data['artifact_hashes']['era5_sample'] = checksum
        state_data['updated_at'] = datetime.now(timezone.utc).isoformat()

        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)

        # Verify
        with open(state_file, 'r') as f:
            final_state = yaml.safe_load(f)

        assert final_state['artifact_hashes']['era5_sample'] == expected_hash
        assert 'updated_at' in final_state
        assert final_state['updated_at'] != initial_state['updated_at']
