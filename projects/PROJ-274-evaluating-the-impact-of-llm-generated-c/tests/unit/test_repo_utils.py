"""
Unit tests for repo_utils module.
Tests T024: Codebase fetching and commit pinning logic.
"""
import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
import subprocess

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from repo_utils import (
    ensure_dirs,
    clone_or_fetch_repo,
    get_repo_files,
    generate_checksum,
    log_pinned_repo,
    stream_repo_content,
    construct_llm_prompt_stream,
    DataFetchError
)

class TestEnsureDirs:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, 'test', 'nested', 'path')
            ensure_dirs(new_dir)
            assert os.path.isdir(new_dir)
    
    def test_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_dirs(tmpdir)  # Should not raise
            assert os.path.isdir(tmpdir)

class TestGenerateChecksum:
    def test_checksum_generation(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = generate_checksum(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

class TestGetRepoFiles:
    def test_file_count_limit_exceeded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create more than 500 files
            for i in range(501):
                with open(os.path.join(tmpdir, f'file_{i}.txt'), 'w') as f:
                    f.write(f"content {i}")
            
            with pytest.raises(DataFetchError) as exc_info:
                get_repo_files(tmpdir, max_files=500)
            
            assert "exceeding limit" in str(exc_info.value)
    
    def test_returns_correct_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 10 files
            for i in range(10):
                with open(os.path.join(tmpdir, f'file_{i}.txt'), 'w') as f:
                    f.write(f"content {i}")
            
            files, count = get_repo_files(tmpdir, max_files=100)
            assert count == 10
            assert len(files) == 10
    
    def test_skips_binary_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create text and binary files
            with open(os.path.join(tmpdir, 'text.txt'), 'w') as f:
                f.write("text")
            with open(os.path.join(tmpdir, 'image.png'), 'wb') as f:
                f.write(b"fake png")
            
            files, _ = get_repo_files(tmpdir, max_files=100)
            assert len(files) == 1
            assert files[0].endswith('text.txt')

class TestLogPinnedRepo:
    def test_creates_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
          log_file = os.path.join(tmpdir, 'pinned.json')
          log_pinned_repo('https://example.com/repo.git', 'abc123', tmpdir, log_file)
          
          assert os.path.exists(log_file)
          with open(log_file, 'r') as f:
              data = json.load(f)
          
          assert data['repo_url'] == 'https://example.com/repo.git'
          assert data['commit_hash'] == 'abc123'
          assert data['repo_path'] == tmpdir

class TestStreamRepoContent:
    def test_streams_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = os.path.join(tmpdir, 'file1.txt')
            file2 = os.path.join(tmpdir, 'file2.txt')
            with open(file1, 'w') as f:
                f.write("content1")
            with open(file2, 'w') as f:
                f.write("content2")
            
            files = [file1, file2]
            results = list(stream_repo_content(tmpdir, files))
            
            assert len(results) == 2
            assert results[0][0] == 'file1.txt'
            assert results[0][1] == "content1"
            assert results[1][0] == 'file2.txt'
            assert results[1][1] == "content2"

class TestConstructLLMPromptStream:
    def test_constructs_prompt(self):
        file_stream = [
            ('file1.py', 'print("hello")'),
            ('file2.py', 'def foo(): pass')
        ]
        
        prompt = construct_llm_prompt_stream('test_repo', file_stream)
        
        assert 'Repository: test_repo' in prompt
        assert '--- File: file1.py ---' in prompt
        assert 'print("hello")' in prompt
        assert '--- File: file2.py ---' in prompt
    
    def test_respects_token_limit(self):
        # Create a large file content
        large_content = "x = 1\n" * 1000
        file_stream = [
            ('large.py', large_content),
            ('small.py', 'y = 2')
        ]
        
        prompt = construct_llm_prompt_stream('test_repo', file_stream, max_tokens=10)
        
        # Should stop before including the second file
        assert 'large.py' in prompt
        assert 'small.py' not in prompt

class TestDataFetchError:
    def test_error_message(self):
        try:
            raise DataFetchError("Test error message")
        except DataFetchError as e:
            assert str(e) == "Test error message"

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            check=True,
            stdout=MagicMock(strip=MagicMock(return_value='abc123def456')),
            stderr=''
        )
        yield mock_run

class TestCloneOrFetchRepo:
    @patch('subprocess.run')
    def test_clone_and_checkout(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            check=True,
            stdout=MagicMock(strip=MagicMock(return_value='abc123def456')),
            stderr=''
        )
        
        # Create a fake git repo structure
        repo_dir = tmp_path / 'test_repo'
        repo_dir.mkdir()
        git_dir = repo_dir / '.git'
        git_dir.mkdir()
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                result = clone_or_fetch_repo(
                    'https://example.com/repo.git',
                    'abc123def456',
                    str(tmp_path)
                )
        
        # Verify git commands were called
        assert mock_run.call_count >= 3  # fetch, checkout, rev-parse
    
    @patch('subprocess.run')
    def test_commit_hash_mismatch(self, mock_run, tmp_path):
        mock_run.side_effect = [
            MagicMock(check=True, stdout=MagicMock(strip=MagicMock(return_value='abc123')), stderr=''),
            MagicMock(check=True, stdout=MagicMock(strip=MagicMock(return_value='def456')), stderr='')
        ]
        
        repo_dir = tmp_path / 'test_repo'
        repo_dir.mkdir()
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                with pytest.raises(DataFetchError) as exc_info:
                    clone_or_fetch_repo(
                        'https://example.com/repo.git',
                        'abc123',
                        str(tmp_path)
                    )
                
                assert "Commit hash mismatch" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_clone_failure(self, mock_run, tmp_path):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr='Clone failed')
        
        with pytest.raises(DataFetchError) as exc_info:
            clone_or_fetch_repo(
                'https://example.com/repo.git',
                'abc123',
                str(tmp_path)
            )
        
        assert "Failed to clone" in str(exc_info.value)
