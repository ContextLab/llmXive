import os
import sys
import json
import tempfile
import shutil
import hashlib
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from doc_generation import (
    ensure_dirs,
    calculate_checksum,
    update_checksum_file,
    save_generated_docs,
    log_config_and_checksum
)

class TestDocGenerationUtils:

    def setup_method(self):
        """Create a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Create necessary subdirectories
        os.makedirs('data/raw/llm_docs', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('data/reports', exist_ok=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_ensure_dirs_creates_directories(self):
        """Test that ensure_dirs creates the required directory structure."""
        # Remove a directory to test creation
        if os.path.exists('data/raw/llm_docs'):
            shutil.rmtree('data/raw/llm_docs')
        
        ensure_dirs()
        assert os.path.isdir('data/raw/llm_docs')
        assert os.path.isdir('data/processed')
        assert os.path.isdir('data/reports')
        assert os.path.isdir('logs')

    def test_calculate_checksum_string(self):
        """Test checksum calculation for string content."""
        content = "Hello, World!"
        expected = hashlib.sha256(content.encode('utf-8')).hexdigest()
        assert calculate_checksum(content) == expected

    def test_calculate_checksum_bytes(self):
        """Test checksum calculation for bytes content."""
        content = b"Hello, World!"
        expected = hashlib.sha256(content).hexdigest()
        assert calculate_checksum(content) == expected

    def test_update_checksum_file(self):
        """Test that update_checksum_file appends a record correctly."""
        checksum_file = 'data/checksums.txt'
        checksum = 'abc123'
        artifact = 'test_artifact'
        
        update_checksum_file(checksum, artifact)
        
        assert os.path.exists(checksum_file)
        with open(checksum_file, 'r') as f:
            content = f.read()
        assert checksum in content
        assert artifact in content
        assert ' | ' in content

    def test_save_generated_docs(self):
        """Test saving generated documentation to file."""
        content = "# Test Doc\n\nThis is a test."
        repo_name = "test-repo"
        version = "v1.0"
        
        filepath = save_generated_docs(content, repo_name, version)
        
        assert os.path.exists(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        assert saved_content == content
        
        # Check filename format
        expected_filename = f"{repo_name}_{version}.md"
        assert expected_filename in filepath

    def test_log_config_and_checksum(self):
        """Test logging config and saving checksum."""
        content = "Test content for logging."
        model = "test-model"
        temp = 0.7
        artifact = "test-logging-artifact"
        
        checksum = log_config_and_checksum(model, temp, "hash123", content, artifact)
        
        # Verify checksum matches content
        assert checksum == calculate_checksum(content)
        
        # Verify config file exists
        config_path = 'data/llm_config.yaml'
        assert os.path.exists(config_path)
        
        # Verify checksum file exists
        checksum_path = 'data/checksums.txt'
        assert os.path.exists(checksum_path)
        with open(checksum_path, 'r') as f:
            assert checksum in f.read()

    def test_save_generated_docs_empty_content(self):
        """Test that save_generated_docs handles empty content gracefully (or fails if intended)."""
        # Based on main() logic, empty content should be caught, but save_generated_docs itself just writes.
        # We test that it writes an empty file if called directly.
        content = ""
        filepath = save_generated_docs(content, "empty-repo", "v0")
        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            assert f.read() == ""

    def test_checksum_file_appends_multiple_entries(self):
        """Test that update_checksum_file appends multiple entries without overwriting."""
        update_checksum_file('checksum1', 'artifact1')
        update_checksum_file('checksum2', 'artifact2')
        
        with open('data/checksums.txt', 'r') as f:
            lines = f.readlines()
        
        assert len(lines) >= 2
        assert 'checksum1' in lines[0]
        assert 'checksum2' in lines[1]