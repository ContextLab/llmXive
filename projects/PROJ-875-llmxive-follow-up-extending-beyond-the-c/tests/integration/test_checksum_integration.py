"""
Integration tests for checksum functionality.

Tests the integration of checksum generation with the data pipeline,
including interaction with data/processed/ and state/ directories.
"""
import os
import sys
import json
from pathlib import Path
import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "utils"))
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from checksum import generate_checksum_manifest, save_manifest, load_manifest, verify_checksums
from state_manager import update_checksum_manifest, get_checksum_manifest, verify_data_integrity, create_state_snapshot

class TestChecksumIntegration:
    """Integration tests for checksum functionality."""
    
    @pytest.fixture
    def setup_test_data(self, tmp_path):
        """Set up test data structure."""
        # Create data/processed directory with test files
        data_processed = tmp_path / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Create sample files
        (data_processed / "test1.json").write_text(json.dumps({"event": "test1"}))
        (data_processed / "test2.ascii").write_text("#.#\n###\n.#.")
        (data_processed / "subdir" / "test3.csv").write_text("a,b,c\n1,2,3")
        (data_processed / "subdir").mkdir(parents=True, exist_ok=True)
        (data_processed / "subdir" / "test3.csv").write_text("a,b,c\n1,2,3")
        
        # Create state directory
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        
        # Store paths for tests
        return {
            "root": tmp_path,
            "data_processed": data_processed,
            "state_dir": state_dir
        }
    
    def test_generate_checksums_for_processed_data(self, setup_test_data, monkeypatch):
        """Test generating checksums for data/processed/ directory."""
        tmp_path = setup_test_data["root"]
        data_processed = setup_test_data["data_processed"]
        
        # Monkeypatch DATA_PROCESSED_DIR
        import checksum
        original_dir = checksum.DATA_PROCESSED_DIR
        checksum.DATA_PROCESSED_DIR = data_processed
        
        try:
            manifest = generate_checksum_manifest(data_processed)
            
            assert manifest["file_count"] == 2  # test1.json and test2.ascii
            assert "test1.json" in manifest["checksums"]
            assert "test2.ascii" in manifest["checksums"]
            
            # Verify all required fields
            for path, info in manifest["checksums"].items():
                assert "sha256" in info
                assert "size_bytes" in info
                assert "last_modified" in info
                assert len(info["sha256"]) == 64  # SHA-256 hex length
        finally:
            checksum.DATA_PROCESSED_DIR = original_dir
    
    def test_save_and_load_manifest_integration(self, setup_test_data):
        """Test saving and loading manifest in state directory."""
        tmp_path = setup_test_data["root"]
        state_dir = setup_test_data["state_dir"]
        data_processed = setup_test_data["data_processed"]
        
        # Generate manifest
        manifest = generate_checksum_manifest(data_processed)
        
        # Save to state directory
        manifest_path = state_dir / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        assert manifest_path.exists()
        
        # Load and verify
        loaded = load_manifest(manifest_path)
        assert loaded == manifest
    
    def test_verify_checksums_integration(self, setup_test_data):
        """Test verification workflow."""
        tmp_path = setup_test_data["root"]
        state_dir = setup_test_data["state_dir"]
        data_processed = setup_test_data["data_processed"]
        
        # Generate and save manifest
        manifest = generate_checksum_manifest(data_processed)
        manifest_path = state_dir / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        # Verify
        results = verify_checksums(manifest_path)
        
        assert results["status"] == "success"
        assert results["verified"] == manifest["file_count"]
        assert results["failed"] == 0
        assert results["missing"] == 0
    
    def test_detect_modification_integration(self, setup_test_data):
        """Test that file modification is detected in integration."""
        tmp_path = setup_test_data["root"]
        state_dir = setup_test_data["state_dir"]
        data_processed = setup_test_data["data_processed"]
        
        # Generate and save manifest
        manifest = generate_checksum_manifest(data_processed)
        manifest_path = state_dir / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        # Modify a file
        test_file = data_processed / "test1.json"
        original_content = test_file.read_text()
        test_file.write_text(json.dumps({"event": "modified"}))
        
        # Verify should detect modification
        results = verify_checksums(manifest_path)
        
        assert results["status"] == "warning"
        assert results["failed"] == 1
        assert results["verified"] == manifest["file_count"] - 1
    
    def test_detect_missing_file_integration(self, setup_test_data):
        """Test that missing files are detected in integration."""
        tmp_path = setup_test_data["root"]
        state_dir = setup_test_data["state_dir"]
        data_processed = setup_test_data["data_processed"]
        
        # Generate and save manifest
        manifest = generate_checksum_manifest(data_processed)
        manifest_path = state_dir / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        # Delete a file
        test_file = data_processed / "test1.json"
        test_file.unlink()
        
        # Verify should detect missing file
        results = verify_checksums(manifest_path)
        
        assert results["status"] == "warning"
        assert results["missing"] == 1
        assert results["verified"] == manifest["file_count"] - 1
    
    def test_state_manager_integration(self, setup_test_data, monkeypatch):
        """Test state manager functions."""
        tmp_path = setup_test_data["root"]
        state_dir = setup_test_data["state_dir"]
        data_processed = setup_test_data["data_processed"]
        
        # Monkeypatch paths
        import state_manager
        original_state_dir = state_manager.STATE_DIR
        original_checksum_path = state_manager.CHECKSUM_MANIFEST_PATH
        
        state_manager.STATE_DIR = state_dir
        state_manager.CHECKSUM_MANIFEST_PATH = state_dir / "checksums.yaml"
        
        # Also monkeypatch checksum module
        import checksum
        original_data_dir = checksum.DATA_PROCESSED_DIR
        checksum.DATA_PROCESSED_DIR = data_processed
        
        try:
            # Test update_checksum_manifest
            path = update_checksum_manifest()
            assert path.exists()
            assert "checksums.yaml" in path.name
            
            # Test get_checksum_manifest
            manifest = get_checksum_manifest()
            assert manifest is not None
            assert "checksums" in manifest
            assert manifest["file_count"] > 0
            
            # Test verify_data_integrity
            results = verify_data_integrity()
            assert results["status"] == "success"
            
            # Test create_state_snapshot
            snapshot_path = create_state_snapshot("test_snapshot", {"test": "data"})
            assert snapshot_path.exists()
            
            # Load and verify snapshot
            from state_manager import load_state_snapshot
            snapshot = load_state_snapshot("test_snapshot")
            assert snapshot is not None
            assert snapshot["snapshot_name"] == "test_snapshot"
            assert "checksum_manifest" in snapshot
            assert snapshot["metadata"]["test"] == "data"
        finally:
            state_manager.STATE_DIR = original_state_dir
            state_manager.CHECKSUM_MANIFEST_PATH = original_checksum_path
            checksum.DATA_PROCESSED_DIR = original_data_dir
    
    def test_empty_data_directory(self, setup_test_data):
        """Test handling of empty data/processed/ directory."""
        tmp_path = setup_test_data["root"]
        state_dir = setup_test_data["state_dir"]
        data_processed = setup_test_data["data_processed"]
        
        # Remove all files
        for file_path in data_processed.rglob("*"):
            if file_path.is_file():
                file_path.unlink()
        
        # Generate manifest for empty directory
        manifest = generate_checksum_manifest(data_processed)
        
        assert manifest["file_count"] == 0
        assert manifest["checksums"] == {}
        
        # Save and verify
        manifest_path = state_dir / "checksums.yaml"
        save_manifest(manifest, manifest_path)
        
        results = verify_checksums(manifest_path)
        assert results["status"] == "success"
        assert results["verified"] == 0
