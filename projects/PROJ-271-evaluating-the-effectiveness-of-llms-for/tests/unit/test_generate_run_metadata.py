"""
Tests for generate_run_metadata.py (T052).
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from code.generate_run_metadata import (
    get_environment_hash,
    get_random_seed,
    generate_run_metadata,
    save_metadata
)


class TestGetEnvironmentHash:
    def test_get_environment_hash_returns_hex_string(self):
        """Test that environment hash is a valid hex string."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="numpy==1.21.0\npandas==1.3.0\n",
                check=True
            )
            hash_result = get_environment_hash()
            
            assert isinstance(hash_result, str)
            assert len(hash_result) == 16  # Truncated to 16 chars
            # Verify it's a valid hex string
            int(hash_result, 16)  # Should not raise


class TestGetRandomSeed:
    def test_get_random_seed_returns_int(self):
        """Test that random seed is an integer."""
        seed = get_random_seed()
        assert isinstance(seed, int)

    def test_get_random_seed_uses_config_value(self):
        """Test that random seed uses value from config."""
        with patch('code.generate_run_metadata.RANDOM_SEED', 12345):
            seed = get_random_seed()
            assert seed == 12345


class TestGenerateRunMetadata:
    def test_generate_run_metadata_contains_required_fields(self):
        """Test that metadata contains all required fields."""
        with patch('code.generate_run_metadata.get_environment_hash', return_value="abc123"):
            with patch('code.generate_run_metadata.get_dataset_commit_id', return_value="def456"):
                with patch('code.generate_run_metadata.get_random_seed', return_value=42):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(stdout="2023-01-01T00:00:00Z")
                        
                        metadata = generate_run_metadata()
                        
                        assert "environment_hash" in metadata
                        assert "dataset_commit_id" in metadata
                        assert "random_seed" in metadata
                        assert "generated_at" in metadata

    def test_generate_run_metadata_values_are_correct(self):
        """Test that metadata values are correctly populated."""
        with patch('code.generate_run_metadata.get_environment_hash', return_value="test_hash"):
            with patch('code.generate_run_metadata.get_dataset_commit_id', return_value="test_commit"):
                with patch('code.generate_run_metadata.get_random_seed', return_value=999):
                    with patch('subprocess.run') as mock_run:
                        mock_run.return_value = MagicMock(stdout="2023-01-01T00:00:00Z")
                        
                        metadata = generate_run_metadata()
                        
                        assert metadata["environment_hash"] == "test_hash"
                        assert metadata["dataset_commit_id"] == "test_commit"
                        assert metadata["random_seed"] == 999


class TestSaveMetadata:
    def test_save_metadata_creates_json_file(self):
        """Test that save_metadata creates a valid JSON file."""
        metadata = {
            "environment_hash": "abc123",
            "dataset_commit_id": "def456",
            "random_seed": 42,
            "generated_at": "2023-01-01T00:00:00Z"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            result_path = save_metadata(metadata, temp_path)
            
            assert result_path == temp_path
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                loaded_metadata = json.load(f)
            
            assert loaded_metadata == metadata
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_metadata_with_default_path(self):
        """Test that save_metadata uses default path when not specified."""
        metadata = {"test": "data"}
        
        with patch('code.generate_run_metadata.get_results_path', return_value='/tmp/results'):
            with patch('builtins.open') as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = lambda s, *args: None
                
                result_path = save_metadata(metadata)
                
                assert result_path == '/tmp/results/run_metadata.json'