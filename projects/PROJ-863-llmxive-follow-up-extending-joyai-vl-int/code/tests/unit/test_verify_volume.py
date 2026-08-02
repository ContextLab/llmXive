import json
import tempfile
from pathlib import Path
import pytest
from src.data_synthesis.verify_volume import (
    load_manifest,
    calculate_total_duration,
    verify_volume,
    NON_CI_TARGET_SECONDS,
    CI_SUBSET_SECONDS
)

class TestLoadManifest:
    def test_load_valid_manifest(self, temp_data_dir):
        """Test loading a valid manifest.jsonl file."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create valid manifest
        entries = [
            {"id": "1", "duration_seconds": 100.0, "path": "chunk1.jsonl"},
            {"id": "2", "duration_seconds": 200.0, "path": "chunk2.jsonl"}
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = load_manifest(manifest_path)
        
        assert len(result) == 2
        assert result[0]['id'] == '1'
        assert result[1]['duration_seconds'] == 200.0

    def test_load_empty_manifest(self, temp_data_dir):
        """Test loading an empty manifest file."""
        manifest_path = temp_data_dir / "empty.jsonl"
        manifest_path.touch()
        
        result = load_manifest(manifest_path)
        assert result == []

    def test_load_missing_file(self, temp_data_dir):
        """Test that loading a non-existent file raises FileNotFoundError."""
        missing_path = temp_data_dir / "nonexistent.jsonl"
        
        with pytest.raises(FileNotFoundError):
            load_manifest(missing_path)

    def test_load_invalid_json(self, temp_data_dir):
        """Test that loading invalid JSON raises JSONDecodeError."""
        manifest_path = temp_data_dir / "invalid.jsonl"
        
        with open(manifest_path, 'w') as f:
            f.write('{"id": "1", invalid json}\n')
        
        with pytest.raises(json.JSONDecodeError):
            load_manifest(manifest_path)

class TestCalculateTotalDuration:
    def test_calculate_with_duration_seconds(self):
        """Test duration calculation with 'duration_seconds' key."""
        entries = [
            {"duration_seconds": 100.0},
            {"duration_seconds": 200.0},
            {"duration_seconds": 50.0}
        ]
        
        total = calculate_total_duration(entries)
        assert total == 350.0

    def test_calculate_with_duration_key(self):
        """Test duration calculation with 'duration' key (fallback)."""
        entries = [
            {"duration": 100.0},
            {"duration": 200.0}
        ]
        
        total = calculate_total_duration(entries)
        assert total == 300.0

    def test_calculate_mixed_keys(self):
        """Test duration calculation with mixed key names."""
        entries = [
            {"duration_seconds": 100.0},
            {"duration": 200.0}
        ]
        
        total = calculate_total_duration(entries)
        assert total == 300.0

    def test_calculate_empty_list(self):
        """Test duration calculation with empty list."""
        total = calculate_total_duration([])
        assert total == 0.0

    def test_calculate_missing_keys(self):
        """Test duration calculation when keys are missing."""
        entries = [
            {"id": "1"},
            {"name": "test"}
        ]
        
        total = calculate_total_duration(entries)
        assert total == 0.0

class TestVerifyVolume:
    def test_verify_passes_non_ci(self, temp_data_dir):
        """Test verification passes when non-CI target is met."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create manifest with 60 hours of data (>= 50 hours)
        entries = [
            {"id": str(i), "duration_seconds": 36000.0}  # 10 hours each
            for i in range(6)  # 60 hours total
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = verify_volume(manifest_path, is_ci_mode=False)
        
        assert result['success'] is True
        assert result['total_seconds'] == 216000.0  # 60 hours
        assert result['expected_seconds'] == NON_CI_TARGET_SECONDS
        assert 'PASSED' in result['message']

    def test_verify_fails_non_ci(self, temp_data_dir):
        """Test verification fails when non-CI target is not met."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create manifest with 40 hours of data (< 50 hours)
        entries = [
            {"id": str(i), "duration_seconds": 36000.0}  # 10 hours each
            for i in range(4)  # 40 hours total
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = verify_volume(manifest_path, is_ci_mode=False)
        
        assert result['success'] is False
        assert result['total_seconds'] == 144000.0  # 40 hours
        assert result['expected_seconds'] == NON_CI_TARGET_SECONDS
        assert 'FAILED' in result['message']

    def test_verify_passes_ci_mode(self, temp_data_dir):
        """Test verification passes in CI mode when subset target is met."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create manifest with 2 hours of data (>= 1 hour CI target)
        entries = [
            {"id": "1", "duration_seconds": 7200.0}  # 2 hours
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = verify_volume(manifest_path, is_ci_mode=True)
        
        assert result['success'] is True
        assert result['total_seconds'] == 7200.0
        assert result['expected_seconds'] == CI_SUBSET_SECONDS
        assert 'CI subset' in result['message']

    def test_verify_fails_ci_mode(self, temp_data_dir):
        """Test verification fails in CI mode when subset target is not met."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create manifest with 30 minutes of data (< 1 hour CI target)
        entries = [
            {"id": "1", "duration_seconds": 1800.0}  # 30 minutes
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = verify_volume(manifest_path, is_ci_mode=True)
        
        assert result['success'] is False
        assert result['total_seconds'] == 1800.0
        assert result['expected_seconds'] == CI_SUBSET_SECONDS
        assert 'FAILED' in result['message']

    def test_verify_empty_manifest_raises(self, temp_data_dir):
        """Test that empty manifest raises ValueError."""
        manifest_path = temp_data_dir / "empty.jsonl"
        manifest_path.touch()
        
        with pytest.raises(ValueError, match="Manifest file is empty"):
            verify_volume(manifest_path)

    def test_verify_missing_file_raises(self, temp_data_dir):
        """Test that missing file raises FileNotFoundError."""
        missing_path = temp_data_dir / "missing.jsonl"
        
        with pytest.raises(FileNotFoundError):
            verify_volume(missing_path)

    def test_verify_exact_threshold_non_ci(self, temp_data_dir):
        """Test verification passes at exact 50-hour threshold."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create manifest with exactly 50 hours
        entries = [
            {"id": "1", "duration_seconds": NON_CI_TARGET_SECONDS}
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = verify_volume(manifest_path, is_ci_mode=False)
        
        assert result['success'] is True
        assert result['total_seconds'] == NON_CI_TARGET_SECONDS

    def test_verify_exact_threshold_ci(self, temp_data_dir):
        """Test verification passes at exact 1-hour CI threshold."""
        manifest_path = temp_data_dir / "manifest.jsonl"
        
        # Create manifest with exactly 1 hour
        entries = [
            {"id": "1", "duration_seconds": CI_SUBSET_SECONDS}
        ]
        
        with open(manifest_path, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        result = verify_volume(manifest_path, is_ci_mode=True)
        
        assert result['success'] is True
        assert result['total_seconds'] == CI_SUBSET_SECONDS