"""
Unit tests for dataset registry functionality.
"""
import pytest
import yaml
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.dataset_registry import compute_sha256, verify_checksum, REGISTRY_PATH

class TestChecksumComputation:
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test checksum computation on empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        checksum = compute_sha256(test_file)
        # SHA256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected

    def test_compute_sha256_content(self, tmp_path):
        """Test checksum computation on file with content."""
        test_file = tmp_path / "content.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_sha256(test_file)
        # SHA256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

class TestRegistryVerification:
    def test_verify_checksum_missing_registry(self):
        """Test verification when registry doesn't exist."""
        with pytest.raises(ValueError, match="Registry file not found"):
            verify_checksum("nonexistent")

    def test_verify_checksum_missing_dataset(self, tmp_path):
        """Test verification when dataset not in registry."""
        # Create a temporary registry
        registry_content = {
            "version": "1.0",
            "datasets": [
                {
                    "name": "existing_dataset",
                    "file_path": "data/raw/existing.csv",
                    "checksum": "abc123",
                    "verified": True
                }
            ]
        }
        
        # Save to temp location
        temp_registry = tmp_path / "registry.yaml"
        with open(temp_registry, "w") as f:
            yaml.dump(registry_content, f)
        
        # Temporarily override REGISTRY_PATH
        import code.data.dataset_registry as module
        original_path = module.REGISTRY_PATH
        module.REGISTRY_PATH = temp_registry
        
        try:
            with pytest.raises(ValueError, match="Dataset nonexistent not found in registry"):
                verify_checksum("nonexistent")
        finally:
            module.REGISTRY_PATH = original_path
