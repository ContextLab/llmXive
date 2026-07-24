"""
Unit tests for checksum_utils.py (T010).

Tests cover:
- calculate_sha256: Correct hash generation
- generate_checksums: Batch processing and file output
- validate_checksums: Matching and mismatching scenarios
- Error handling: Missing files, invalid data
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksum_utils import (
    calculate_sha256,
    generate_checksums,
    validate_checksums,
    load_checksums,
    main
)


class TestCalculateSha256:
    """Tests for calculate_sha256 function."""
    
    def test_calculate_sha256_known_file(self):
        """Test SHA-256 calculation on a known file content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name
            
        try:
            # Known SHA-256 for "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            actual = calculate_sha256(temp_path)
            assert actual == expected
        finally:
            os.unlink(temp_path)
            
    def test_calculate_sha256_empty_file(self):
        """Test SHA-256 calculation on an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            
        try:
            # SHA-256 for empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            actual = calculate_sha256(temp_path)
            assert actual == expected
        finally:
            os.unlink(temp_path)
            
    def test_calculate_sha256_binary_file(self):
        """Test SHA-256 calculation on binary content."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"\x00\x01\x02\x03\x04")
            temp_path = f.name
            
        try:
            actual = calculate_sha256(temp_path)
            assert len(actual) == 64  # SHA-256 hex string length
            assert all(c in '0123456789abcdef' for c in actual)
        finally:
            os.unlink(temp_path)
            
    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")


class TestGenerateChecksums:
    """Tests for generate_checksums function."""
    
    def test_generate_checksums_single_file(self):
        """Test checksum generation for a single file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
            
        try:
            checksums = generate_checksums([temp_path])
            assert len(checksums) == 1
            assert temp_path in checksums
            assert len(checksums[temp_path]) == 64
        finally:
            os.unlink(temp_path)
            
    def test_generate_checksums_multiple_files(self):
        """Test checksum generation for multiple files."""
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(f"Content {i}")
                files.append(f.name)
                
        try:
            checksums = generate_checksums(files)
            assert len(checksums) == 3
            for file_path in files:
                assert file_path in checksums
        finally:
            for f in files:
                os.unlink(f)
                
    def test_generate_checksums_with_output(self):
        """Test checksum generation with JSON output file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test")
            temp_path = f.name
            
        output_file = tempfile.mktemp(suffix='.json')
        
        try:
            checksums = generate_checksums([temp_path], output_file)
            assert os.path.exists(output_file)
            
            with open(output_file, 'r') as f:
                saved_checksums = json.load(f)
                
            assert temp_path in saved_checksums
            assert saved_checksums[temp_path] == checksums[temp_path]
        finally:
            os.unlink(temp_path)
            if os.path.exists(output_file):
                os.unlink(output_file)
                
    def test_generate_checksums_skips_missing(self):
        """Test that missing files are skipped without raising error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test")
            temp_path = f.name
            
        try:
            checksums = generate_checksums([temp_path, "/nonexistent/file.txt"])
            assert len(checksums) == 1
            assert temp_path in checksums
        finally:
            os.unlink(temp_path)


class TestValidateChecksums:
    """Tests for validate_checksums function."""
    
    def test_validate_checksums_all_valid(self):
        """Test validation when all checksums match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Valid content")
            temp_path = f.name
            
        try:
            checksum = calculate_sha256(temp_path)
            checksums = {temp_path: checksum}
            
            all_valid, valid, invalid = validate_checksums(checksums)
            
            assert all_valid is True
            assert len(valid) == 1
            assert len(invalid) == 0
        finally:
            os.unlink(temp_path)
            
    def test_validate_checksums_mismatch(self):
        """Test validation when checksums do not match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Original content")
            temp_path = f.name
            
        try:
            # Create a different checksum
            checksums = {temp_path: "a" * 64}
            
            all_valid, valid, invalid = validate_checksums(checksums)
            
            assert all_valid is False
            assert len(valid) == 0
            assert len(invalid) == 1
            assert temp_path in invalid
        finally:
            os.unlink(temp_path)
            
    def test_validate_checksums_missing_file(self):
        """Test validation when file is missing."""
        checksums = {"/nonexistent/file.txt": "a" * 64}
        
        all_valid, valid, invalid = validate_checksums(checksums)
        
        assert all_valid is False
        assert len(valid) == 0
        assert len(invalid) == 1
        
    def test_validate_checksums_strict_missing(self):
        """Test that strict mode raises error for missing file."""
        checksums = {"/nonexistent/file.txt": "a" * 64}
        
        with pytest.raises(FileNotFoundError):
            validate_checksums(checksums, strict=True)
            
    def test_validate_checksums_mixed_results(self):
        """Test validation with mix of valid and invalid files."""
        files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(f"Content {i}")
                files.append(f.name)
                
        try:
            checksums = {}
            for i, file_path in enumerate(files):
                if i == 0:
                    checksums[file_path] = calculate_sha256(file_path)  # Valid
                else:
                    checksums[file_path] = "b" * 64  # Invalid
                    
            all_valid, valid, invalid = validate_checksums(checksums)
            
            assert all_valid is False
            assert len(valid) == 1
            assert len(invalid) == 1
        finally:
            for f in files:
                os.unlink(f)


class TestLoadChecksums:
    """Tests for load_checksums function."""
    
    def test_load_checksums_valid_file(self):
        """Test loading checksums from a valid JSON file."""
        checksums_data = {
            "/path/to/file1.txt": "abc123...",
            "/path/to/file2.txt": "def456..."
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(checksums_data, f)
            temp_path = f.name
            
        try:
            loaded = load_checksums(temp_path)
            assert loaded == checksums_data
        finally:
            os.unlink(temp_path)
            
    def test_load_checksums_file_not_found(self):
        """Test that FileNotFoundError is raised for missing checksum file."""
        with pytest.raises(FileNotFoundError):
            load_checksums("/nonexistent/checksums.json")
            
    def test_load_checksums_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Not valid JSON {")
            temp_path = f.name
            
        try:
            with pytest.raises(json.JSONDecodeError):
                load_checksums(temp_path)
        finally:
            os.unlink(temp_path)


class TestMain:
    """Tests for the main CLI function."""
    
    def test_main_generate_command(self, capsys):
        """Test main function with generate command."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("CLI test")
            temp_path = f.name
            
        try:
            # Simulate CLI arguments
            original_argv = sys.argv
            sys.argv = ['checksum_utils.py', 'generate', temp_path]
            
            try:
                main()
                captured = capsys.readouterr()
                assert "Generated" in captured.out
            finally:
                sys.argv = original_argv
        finally:
            os.unlink(temp_path)
            
    def test_main_validate_command(self, capsys):
        """Test main function with validate command."""
        # Create a file and its checksum
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Validate test")
            temp_path = f.name
            
        checksum = calculate_sha256(temp_path)
        checksums = {temp_path: checksum}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(checksums, f)
            checksum_file = f.name
            
        try:
            original_argv = sys.argv
            sys.argv = ['checksum_utils.py', 'validate', checksum_file]
            
            try:
                main()
                captured = capsys.readouterr()
                assert "validated successfully" in captured.out
            finally:
                sys.argv = original_argv
        finally:
            os.unlink(temp_path)
            os.unlink(checksum_file)
            
    def test_main_invalid_command(self, capsys):
        """Test main function with invalid command."""
        original_argv = sys.argv
        sys.argv = ['checksum_utils.py', 'invalid_command']
        
        try:
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            assert "Unknown command" in captured.out
        finally:
            sys.argv = original_argv
