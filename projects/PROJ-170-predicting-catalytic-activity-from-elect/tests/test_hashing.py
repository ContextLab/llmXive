"""
Tests for the hashing module (code/utils/hashing.py).

These tests verify the content hashing mechanism for state/ artifacts
(Constitution Principle V).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.hashing import (
    compute_file_hash,
    compute_string_hash,
    compute_dict_hash,
    save_hash,
    load_hash,
    verify_file_hash,
    hash_state_artifact,
    verify_state_artifact,
    HASH_ALGORITHM,
    HASH_FILE_SUFFIX,
    STATE_DIR
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""
    
    def test_hash_of_known_file(self, tmp_path):
        """Test hashing a file with known content."""
        file_path = tmp_path / "test.txt"
        content = "Hello, World!"
        file_path.write_text(content)
        
        hash_value = compute_file_hash(file_path)
        
        # SHA-256 of "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_value == expected_hash
    
    def test_hash_of_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        
        hash_value = compute_file_hash(file_path)
        
        # SHA-256 of empty string
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_value == expected_hash
    
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        file_path = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_hash(file_path)
    
    def test_hash_of_directory(self, tmp_path):
        """Test that IOError is raised for directory."""
        with pytest.raises(IOError):
            compute_file_hash(tmp_path)


class TestComputeStringHash:
    """Tests for compute_string_hash function."""
    
    def test_hash_of_known_string(self):
        """Test hashing a string with known content."""
        content = "Hello, World!"
        hash_value = compute_string_hash(content)
        
        # SHA-256 of "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_value == expected_hash
    
    def test_hash_of_empty_string(self):
        """Test hashing an empty string."""
        hash_value = compute_string_hash("")
        
        # SHA-256 of empty string
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_value == expected_hash
    
    def test_hash_determinism(self):
        """Test that the same string always produces the same hash."""
        content = "Test content for determinism"
        hash1 = compute_string_hash(content)
        hash2 = compute_string_hash(content)
        
        assert hash1 == hash2


class TestComputeDictHash:
    """Tests for compute_dict_hash function."""
    
    def test_hash_of_known_dict(self):
        """Test hashing a dictionary with known content."""
        data = {"key": "value", "number": 42}
        hash_value = compute_dict_hash(data)
        
        # The hash should be deterministic
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hex length
    
    def test_hash_order_independence(self):
        """Test that dictionary order doesn't affect hash."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "b": 2, "a": 1}
        
        hash1 = compute_dict_hash(data1)
        hash2 = compute_dict_hash(data2)
        
        assert hash1 == hash2
    
    def test_hash_of_empty_dict(self):
        """Test hashing an empty dictionary."""
        hash_value = compute_dict_hash({})
        
        # SHA-256 of "{}"
        expected_hash = "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
        assert hash_value == expected_hash


class TestSaveAndLoadHash:
    """Tests for save_hash and load_hash functions."""
    
    def test_save_and_load_hash(self, tmp_path):
        """Test saving and loading a hash."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        hash_value = compute_file_hash(file_path)
        hash_file_path = save_hash(file_path, hash_value)
        
        assert hash_file_path.exists()
        assert hash_file_path.suffix == ".txt" + HASH_FILE_SUFFIX
        
        loaded_data = load_hash(hash_file_path)
        
        assert loaded_data["file"] == "test.txt"
        assert loaded_data["algorithm"] == HASH_ALGORITHM
        assert loaded_data["hash"] == hash_value
    
    def test_save_hash_with_metadata(self, tmp_path):
        """Test saving a hash with metadata."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        hash_value = compute_file_hash(file_path)
        metadata = {"created_by": "test", "version": "1.0"}
        hash_file_path = save_hash(file_path, hash_value, metadata)
        
        loaded_data = load_hash(hash_file_path)
        
        assert "metadata" in loaded_data
        assert loaded_data["metadata"]["created_by"] == "test"
        assert loaded_data["metadata"]["version"] == "1.0"


class TestVerifyFileHash:
    """Tests for verify_file_hash function."""
    
    def test_verify_valid_hash(self, tmp_path):
        """Test verifying a file with a valid hash."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        hash_value = compute_file_hash(file_path)
        save_hash(file_path, hash_value)
        
        assert verify_file_hash(file_path) is True
    
    def test_verify_invalid_hash(self, tmp_path):
        """Test verifying a file with an invalid hash."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        # Save a wrong hash
        wrong_hash = "a" * 64
        save_hash(file_path, wrong_hash)
        
        # Modify the file
        file_path.write_text("Modified content")
        
        assert verify_file_hash(file_path) is False
    
    def test_verify_missing_hash_file(self, tmp_path):
        """Test verifying a file without a hash file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        with pytest.raises(FileNotFoundError):
            verify_file_hash(file_path)


class TestHashStateArtifact:
    """Tests for hash_state_artifact function."""
    
    def test_hash_state_artifact_success(self, tmp_path):
        """Test successfully hashing a state artifact."""
        # Create a fake state directory structure
        state_dir = tmp_path / STATE_DIR
        state_dir.mkdir()
        artifact_path = state_dir / "artifact.json"
        artifact_path.write_text('{"data": "test"}')
        
        # Change to tmp_path so STATE_DIR is relative
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = hash_state_artifact(artifact_path)
            
            assert result["success"] is True
            assert result["file"] == "artifact.json"
            assert "hash" in result
            assert "hash_file" in result
            assert Path(result["hash_file"]).exists()
        finally:
            os.chdir(original_cwd)
    
    def test_hash_state_artifact_not_in_state_dir(self, tmp_path):
        """Test that ValueError is raised for artifacts outside state directory."""
        artifact_path = tmp_path / "outside.txt"
        artifact_path.write_text("Test content")
        
        with pytest.raises(ValueError):
            hash_state_artifact(artifact_path)
    
    def test_hash_state_artifact_with_metadata(self, tmp_path):
        """Test hashing a state artifact with metadata."""
        state_dir = tmp_path / STATE_DIR
        state_dir.mkdir()
        artifact_path = state_dir / "artifact.json"
        artifact_path.write_text('{"data": "test"}')
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            metadata = {"source": "test_source", "version": "1.0"}
            result = hash_state_artifact(artifact_path, metadata)
            
            assert result["success"] is True
            
            # Verify metadata was saved
            hash_file_path = Path(result["hash_file"])
            hash_data = load_hash(hash_file_path)
            
            assert "metadata" in hash_data
            assert hash_data["metadata"]["source"] == "test_source"
        finally:
            os.chdir(original_cwd)


class TestVerifyStateArtifact:
    """Tests for verify_state_artifact function."""
    
    def test_verify_state_artifact_valid(self, tmp_path):
        """Test verifying a valid state artifact."""
        state_dir = tmp_path / STATE_DIR
        state_dir.mkdir()
        artifact_path = state_dir / "artifact.json"
        artifact_path.write_text('{"data": "test"}')
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # First hash the artifact
            hash_state_artifact(artifact_path)
            
            # Then verify it
            result = verify_state_artifact(artifact_path)
            
            assert result["success"] is True
            assert result["valid"] is True
            assert result["stored_hash"] == result["computed_hash"]
        finally:
            os.chdir(original_cwd)
    
    def test_verify_state_artifact_invalid(self, tmp_path):
        """Test verifying an invalid state artifact."""
        state_dir = tmp_path / STATE_DIR
        state_dir.mkdir()
        artifact_path = state_dir / "artifact.json"
        artifact_path.write_text('{"data": "test"}')
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Hash the artifact
            hash_state_artifact(artifact_path)
            
            # Modify the artifact
            artifact_path.write_text('{"data": "modified"}')
            
            # Verify should fail
            result = verify_state_artifact(artifact_path)
            
            assert result["success"] is True
            assert result["valid"] is False
            assert result["stored_hash"] != result["computed_hash"]
        finally:
            os.chdir(original_cwd)


class TestMain:
    """Tests for the main function CLI."""
    
    def test_main_hash_command(self, tmp_path, capsys):
        """Test the hash command in main."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Mock sys.argv
            import sys
            original_argv = sys.argv
            sys.argv = ["hashing.py", "hash", str(file_path)]
            
            try:
                from utils.hashing import main
                main()
                
                captured = capsys.readouterr()
                output = json.loads(captured.out)
                
                assert output["success"] is True
                assert output["hash"] == compute_file_hash(file_path)
            finally:
                sys.argv = original_argv
        finally:
            os.chdir(original_cwd)
    
    def test_main_verify_command(self, tmp_path, capsys):
        """Test the verify command in main."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # First hash the file
            hash_state_artifact(file_path)
            
            # Mock sys.argv
            import sys
            original_argv = sys.argv
            sys.argv = ["hashing.py", "verify", str(file_path)]
            
            try:
                from utils.hashing import main
                main()
                
                captured = capsys.readouterr()
                output = json.loads(captured.out)
                
                assert output["success"] is True
                assert output["valid"] is True
            finally:
                sys.argv = original_argv
        finally:
            os.chdir(original_cwd)
