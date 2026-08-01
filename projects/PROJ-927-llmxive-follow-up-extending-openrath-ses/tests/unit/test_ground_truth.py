import os
import stat
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the functions we're testing
from generators.workflow_generator import (
    generate_ground_truth_batch,
    calculate_sha256,
    generate_workflow
)


class TestGroundTruthSerialization:
    """Tests for ground truth serialization functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_generate_ground_truth_creates_files(self, temp_output_dir):
        """Test that ground truth files are created with correct naming."""
        workflow_ids = [1, 2, 3]
        hashes = generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        # Check that all files were created
        for wid in workflow_ids:
            expected_file = Path(temp_output_dir) / f"{wid}_ground_truth.json"
            assert expected_file.exists(), f"File {expected_file} was not created"
        
        # Check that hashes were returned
        assert len(hashes) == len(workflow_ids)
        for wid in workflow_ids:
            assert wid in hashes
            assert isinstance(hashes[wid], str)
            assert len(hashes[wid]) == 64  # SHA256 hex string length

    def test_ground_truth_files_are_readonly(self, temp_output_dir):
        """Test that generated ground truth files have read-only permissions."""
        workflow_ids = [1]
        generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        file_path = Path(temp_output_dir) / "1_ground_truth.json"
        file_stat = os.stat(str(file_path))
        
        # Check file permissions (should be read-only: 444 or 400)
        file_mode = file_stat.st_mode
        assert file_mode & stat.S_IWUSR == 0, "File should not be writable by owner"
        assert file_mode & stat.S_IWGRP == 0, "File should not be writable by group"
        assert file_mode & stat.S_IWOTH == 0, "File should not be writable by others"

    def test_directory_permissions_set_readonly(self, temp_output_dir):
        """Test that the output directory has read-only permissions."""
        workflow_ids = [1]
        generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        dir_stat = os.stat(temp_output_dir)
        dir_mode = dir_stat.st_mode
        
        # Directory should be readable and executable but not writable
        # (555 = r-xr-xr-x)
        assert dir_mode & stat.S_IWUSR == 0, "Directory should not be writable by owner"
        assert dir_mode & stat.S_IXUSR != 0, "Directory should be executable by owner"

    def test_ground_truth_content_valid_json(self, temp_output_dir):
        """Test that ground truth files contain valid JSON."""
        workflow_ids = [1, 2]
        generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        for wid in workflow_ids:
            file_path = Path(temp_output_dir) / f"{wid}_ground_truth.json"
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Check required fields
            assert "workflow_id" in data
            assert data["workflow_id"] == wid
            assert "steps" in data
            assert isinstance(data["steps"], list)

    def test_hash_consistency(self, temp_output_dir):
        """Test that the same workflow generates the same hash."""
        workflow_ids = [1]
        
        # Generate twice
        hashes1 = generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        # Clean up and regenerate
        for wid in workflow_ids:
            file_path = Path(temp_output_dir) / f"{wid}_ground_truth.json"
            if file_path.exists():
                os.chmod(str(file_path), stat.S_IWUSR)  # Make writable for deletion
                file_path.unlink()
        
        hashes2 = generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        # Hashes should be identical
        assert hashes1[1] == hashes2[1], "Hashes should be identical for same input"

    def test_calculate_sha256(self, temp_output_dir):
        """Test SHA256 calculation function."""
        test_file = Path(temp_output_dir) / "test.txt"
        test_content = "Hello, World!"
        
        with open(test_file, "w") as f:
            f.write(test_content)
        
        hash1 = calculate_sha256(str(test_file))
        assert len(hash1) == 64
        
        # Verify against known hash
        import hashlib
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
        assert hash1 == expected_hash

    def test_different_seeds_produce_different_workflows(self, temp_output_dir):
        """Test that different seeds produce different ground truth."""
        workflow_ids = [1]
        
        hashes_seed1 = generate_ground_truth_batch(workflow_ids, seed=42, output_dir=temp_output_dir)
        
        # Clean up
        for wid in workflow_ids:
            file_path = Path(temp_output_dir) / f"{wid}_ground_truth.json"
            if file_path.exists():
                os.chmod(str(file_path), stat.S_IWUSR)
                file_path.unlink()
        
        hashes_seed2 = generate_ground_truth_batch(workflow_ids, seed=123, output_dir=temp_output_dir)
        
        # Hashes should be different
        assert hashes_seed1[1] != hashes_seed2[1], "Different seeds should produce different hashes"
