import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.data_setup import (
    compute_file_checksum,
    load_checksums,
    save_checksums,
    update_checksum_for_file,
    verify_file_integrity,
    setup_data_environment
)
from config import get_data_root

class TestDataSetup:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Create a temporary directory to act as data root for testing
        self.test_data_root = Path(tempfile.mkdtemp())
        # Mock get_data_root by monkeypatching
        self.original_get_data_root = get_data_root
        import config
        config.get_data_root = lambda: self.test_data_root
        yield
        # Cleanup
        shutil.rmtree(self.test_data_root)
        config.get_data_root = self.original_get_data_root

    def test_setup_creates_directories(self):
        paths = setup_data_environment()
        assert 'raw' in paths
        assert 'processed' in paths
        assert 'results' in paths
        assert paths['raw'].exists()
        assert paths['processed'].exists()
        assert paths['results'].exists()
        assert paths['raw'].is_dir()
        assert paths['processed'].is_dir()
        assert paths['results'].is_dir()

    def test_setup_creates_checksum_manifest(self):
        setup_data_environment()
        checksum_file = self.test_data_root / '.checksums.json'
        assert checksum_file.exists()
        with open(checksum_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_compute_file_checksum(self):
        test_file = self.test_data_root / 'raw' / 'test.txt'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Hello, World!")

        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

        # Verify determinism
        checksum2 = compute_file_checksum(test_file)
        assert checksum == checksum2

    def test_save_and_load_checksums(self):
        test_checksums = {
            'raw/file1.txt': 'abc123',
            'processed/file2.txt': 'def456'
        }
        checksum_file = self.test_data_root / '.checksums.json'
        save_checksums(test_checksums, checksum_file)

        loaded = load_checksums(checksum_file)
        assert loaded == test_checksums

    def test_update_checksum_for_file(self):
        test_file = self.test_data_root / 'raw' / 'update_test.txt'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Update me")

        checksums = {}
        checksum_file = self.test_data_root / '.checksums.json'
        save_checksums({}, checksum_file)

        update_checksum_for_file(test_file, checksums, checksum_file)

        assert 'raw/update_test.txt' in checksums
        assert len(checksums['raw/update_test.txt']) == 64

    def test_verify_file_integrity_success(self):
        test_file = self.test_data_root / 'raw' / 'verify_test.txt'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Verify me")

        checksums = {}
        checksum_file = self.test_data_root / '.checksums.json'
        save_checksums({}, checksum_file)

        # First update to store the correct checksum
        update_checksum_for_file(test_file, checksums, checksum_file)

        # Now verify
        assert verify_file_integrity(test_file, checksums, checksum_file) is True

    def test_verify_file_integrity_failure(self):
        test_file = self.test_data_root / 'raw' / 'verify_fail_test.txt'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Original")

        checksums = {}
        checksum_file = self.test_data_root / '.checksums.json'
        save_checksums({}, checksum_file)

        # Update with original content
        update_checksum_for_file(test_file, checksums, checksum_file)

        # Modify file
        test_file.write_text("Modified")

        # Verify should fail
        assert verify_file_integrity(test_file, checksums, checksum_file) is False

    def test_verify_missing_file(self):
        test_file = self.test_data_root / 'raw' / 'nonexistent.txt'
        checksums = {}
        checksum_file = self.test_data_root / '.checksums.json'
        save_checksums({}, checksum_file)

        assert verify_file_integrity(test_file, checksums, checksum_file) is False
