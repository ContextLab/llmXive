"""
Tests for src/metrics/verify_stimuli.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code root to path for imports
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.metrics.verify_stimuli import verify_stimuli
from src.lib.utils import compute_file_checksum


@pytest.fixture
def temp_archive_environment():
    """
    Creates a temporary directory structure mimicking the stimuli archive
    with a valid manifest and a few dummy image files.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create directory structure
        stimuli_dir = tmp_path / "data" / "stimuli" / "raw"
        stimuli_dir.mkdir(parents=True)
        
        # Create dummy image files
        img1_path = stimuli_dir / "img_001.png"
        img2_path = stimuli_dir / "img_002.png"
        img3_path = stimuli_dir / "img_003_bad.png" # Will have bad checksum
        
        # Write dummy content
        content1 = b"fake_image_content_1"
        content2 = b"fake_image_content_2"
        content3 = b"fake_image_content_3"
        
        img1_path.write_bytes(content1)
        img2_path.write_bytes(content2)
        img3_path.write_bytes(content3)
        
        # Compute real checksums for valid ones
        checksum1 = compute_file_checksum(img1_path)
        checksum2 = compute_file_checksum(img2_path)
        checksum3_correct = compute_file_checksum(img3_path)
        
        # Create manifest with one WRONG checksum for img3
        manifest = {
            "items": [
                {"filename": "img_001.png", "sha256": checksum1},
                {"filename": "img_002.png", "sha256": checksum2},
                {"filename": "img_003_bad.png", "sha256": "0000000000000000000000000000000000000000000000000000000000000000"}
            ]
        }
        
        manifest_path = stimuli_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
        
        # Temporarily override global paths
        # We cannot easily override the global constants in src.config without reloading,
        # so we will test the logic by patching the specific file paths used in the function
        # OR we assume the test runner sets up the environment correctly.
        # However, the function `verify_stimuli` relies on `DATA_DIR` from `src.config`.
        # To make this test robust, we will mock the `src.metrics.verify_stimuli` module's
        # imports of `DATA_DIR` and `STATE_DIR` or simply test the core logic if refactored.
        # Given the constraint to extend existing files, we assume the test environment
        # might need to mock the config or we rely on the fact that `verify_stimuli`
        # is designed to run in the project root.
        
        # For the purpose of this specific test task, we will test the function
        # by temporarily swapping the config values if possible, or by mocking.
        # A cleaner approach for a unit test in this structure:
        
        yield {
            "base_dir": tmp_path,
            "stimuli_dir": stimuli_dir,
            "manifest_path": manifest_path,
            "img1": img1_path,
            "img2": img2_path,
            "img3": img3_path,
            "expected_checksums": {
                "img_001.png": checksum1,
                "img_002.png": checksum2,
                "img_003_bad.png": "0000..."
            }
        }


def test_checksum_match(temp_archive_environment, monkeypatch):
    """
    Test that verify_stimuli correctly identifies matching checksums.
    This test uses the temp environment but patches the global paths.
    """
    import src.config
    import src.metrics.verify_stimuli as verify_module
    
    base_dir = temp_archive_environment["base_dir"]
    stimuli_dir = temp_archive_environment["stimuli_dir"]
    
    # Monkeypatch the DATA_DIR used by the module
    # We need to patch it in the module where it is used
    monkeypatch.setattr(verify_module, "DATA_DIR", base_dir / "data")
    monkeypatch.setattr(verify_module, "STATE_DIR", base_dir / "state")
    
    # Ensure state dir exists
    (base_dir / "state").mkdir(parents=True)
    
    # Run verification
    total, passed, results = verify_stimuli()
    
    # Assertions
    assert total == 3
    assert passed == 2  # img1 and img2 match, img3 fails
    
    # Check specific results
    result_map = {r["image_id"]: r for r in results}
    
    assert result_map["img_001.png"]["status"] == "PASS"
    assert result_map["img_002.png"]["status"] == "PASS"
    assert result_map["img_003_bad.png"]["status"] == "FAIL"
    
    # Verify the output file was created
    state_dir = base_dir / "state"
    output_file = state_dir / "artifact_hashes.json"
    assert output_file.exists()
    
    with open(output_file) as f:
        data = json.load(f)
    
    assert data["verification_status"] == "FAILED"
    assert data["failed_count"] == 1
    assert data["total_images"] == 3


def test_missing_file_handling(temp_archive_environment, monkeypatch):
    """
    Test that verify_stimuli handles missing files gracefully.
    """
    import src.metrics.verify_stimuli as verify_module
    
    base_dir = temp_archive_environment["base_dir"]
    stimuli_dir = temp_archive_environment["stimuli_dir"]
    
    # Monkeypatch
    monkeypatch.setattr(verify_module, "DATA_DIR", base_dir / "data")
    monkeypatch.setattr(verify_module, "STATE_DIR", base_dir / "state")
    (base_dir / "state").mkdir(parents=True)
    
    # Delete one of the files
    temp_archive_environment["img2"].unlink()
    
    total, passed, results = verify_stimuli()
    
    assert total == 3
    # img1: PASS, img2: FILE_MISSING, img3: FAIL
    # passed count should be 1 (only img1)
    assert passed == 1
    
    result_map = {r["image_id"]: r for r in results}
    assert result_map["img_002.png"]["status"] == "FILE_MISSING"