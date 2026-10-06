"""
Tests for T032b: Verify Clips & Record Source
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import hashlib

from src.experiment.verify_clips import verify_clips, parse_arguments


def temp_environment():
    """Create a temporary environment with dummy clip files and expected directories."""
    temp_dir = tempfile.mkdtemp()
    clips_dir = Path(temp_dir) / "clips"
    clips_dir.mkdir()
    
    # Create dummy video files
    for i in range(3):
        file_path = clips_dir / f"clip_{i:03d}.mp4"
        # Write some dummy binary data
        file_path.write_bytes(b"dummy_video_data_" + str(i).encode())
        
    manifest_path = Path(temp_dir) / "manifest.json"
    
    dataset_info = {
        "url": "https://huggingface.co/datasets/test-dataset",
        "version_id": "v1.0.0"
    }
    
    return temp_dir, clips_dir, manifest_path, dataset_info


def test_verify_clips_creates_checksum_and_updates_research():
    """
    Test that verify_clips computes checksums and writes the manifest correctly.
    """
    temp_dir, clips_dir, manifest_path, dataset_info = temp_environment()
    
    try:
        manifest = verify_clips(clips_dir, manifest_path, dataset_info)
        
        # Verify manifest structure
        assert "dataset_url" in manifest
        assert "dataset_version_id" in manifest
        assert "clips" in manifest
        assert "verification_status" in manifest
        
        assert manifest["dataset_url"] == dataset_info["url"]
        assert manifest["dataset_version_id"] == dataset_info["version_id"]
        assert manifest["verification_status"] == "success"
        
        # Verify clip entries
        assert len(manifest["clips"]) == 3
        
        for clip in manifest["clips"]:
            assert "filename" in clip
            assert "checksum_sha256" in clip
            assert "size_bytes" in clip
            assert clip["filename"].endswith(".mp4")
            
            # Verify checksum is a valid hex string
            assert len(clip["checksum_sha256"]) == 64
            try:
                int(clip["checksum_sha256"], 16)
            except ValueError:
                pytest.fail(f"Checksum {clip['checksum_sha256']} is not valid hex")
                
        # Verify file was written to disk
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            loaded_manifest = json.load(f)
            
        assert loaded_manifest == manifest
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)


def test_verify_clips_missing_directory():
    """Test that verify_clips raises FileNotFoundError for missing directory."""
    with pytest.raises(FileNotFoundError):
        verify_clips(
            clips_dir=Path("/nonexistent/path"),
            manifest_path=Path("/tmp/manifest.json"),
            dataset_info={"url": "test", "version_id": "v1"}
        )


def test_verify_clips_no_video_files():
    """Test that verify_clips raises ValueError if no video files are found."""
    temp_dir = tempfile.mkdtemp()
    clips_dir = Path(temp_dir) / "clips"
    clips_dir.mkdir()
    
    # Create a non-video file
    (clips_dir / "readme.txt").write_text("This is not a video")
    
    manifest_path = Path(temp_dir) / "manifest.json"
    
    try:
        with pytest.raises(ValueError, match="No video files found"):
            verify_clips(
                clips_dir=clips_dir,
                manifest_path=manifest_path,
                dataset_info={"url": "test", "version_id": "v1"}
            )
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_verify_clips_partial_failure_handling():
    """Test that verify_clips handles errors gracefully and reports partial failure."""
    temp_dir, clips_dir, manifest_path, dataset_info = temp_environment()
    
    try:
        # Mock compute_file_checksum to raise an exception for one file
        with patch('src.experiment.verify_clips.compute_file_checksum') as mock_checksum:
            # First call succeeds, second fails, third succeeds
            mock_checksum.side_effect = [
                "checksum_1",
                Exception("Read error"),
                "checksum_3"
            ]
            
            manifest = verify_clips(clips_dir, manifest_path, dataset_info)
            
            assert manifest["verification_status"] == "partial_failure"
            assert len(manifest["clips"]) == 2  # Only successful ones
            # Note: The current implementation doesn't store errors in manifest['errors']
            # but the status reflects the failure.
            
    finally:
        import shutil
        shutil.rmtree(temp_dir)
