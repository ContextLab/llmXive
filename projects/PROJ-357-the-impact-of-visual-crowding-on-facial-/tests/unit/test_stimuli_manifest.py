"""
Unit tests for T014: Stimuli Manifest Generation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.stimuli_manifest import extract_metadata_from_filename, load_error_log, generate_manifest
from config import ensure_directories

class TestMetadataExtraction:
    def test_valid_filename(self):
        filename = "happy_flankers5_eccentricity10.png"
        result = extract_metadata_from_filename(filename)
        assert result is not None
        assert result['emotion'] == 'happy'
        assert result['flanker_count'] == 5
        assert result['eccentricity'] == 10.0
        assert result['filename'] == filename

    def test_valid_filename_float_eccentricity(self):
        filename = "sad_flankers3_eccentricity12.5.png"
        result = extract_metadata_from_filename(filename)
        assert result is not None
        assert result['emotion'] == 'sad'
        assert result['flanker_count'] == 3
        assert result['eccentricity'] == 12.5

    def test_invalid_filename(self):
        filename = "random_image.jpg"
        result = extract_metadata_from_filename(filename)
        assert result is None

    def test_missing_extension(self):
        filename = "angry_flankers2_eccentricity8"
        result = extract_metadata_from_filename(filename)
        assert result is None

class TestErrorLogParsing:
    def test_parse_log_line(self, tmp_path):
        log_content = "WARNING: Overlap detected | File: overlap_test.png | Reason: Flankers overlap with target"
        log_file = tmp_path / "generation_errors.log"
        log_file.write_text(log_content)
        
        # Temporarily override the global path for testing
        import utils.stimuli_manifest as sm
        original_path = sm.ERRORS_LOG
        sm.ERRORS_LOG = log_file
        
        try:
            result = load_error_log()
            assert "overlap_test.png" in result
            assert "Flankers overlap with target" in result["overlap_test.png"]
        finally:
            sm.ERRORS_LOG = original_path

class TestManifestGeneration:
    def test_manifest_structure(self, tmp_path):
        # Setup temporary directories
        stimuli_dir = tmp_path / "data" / "interim" / "stimuli"
        stimuli_dir.mkdir(parents=True)
        
        # Create dummy images
        (stimuli_dir / "happy_flankers5_eccentricity10.png").touch()
        (stimuli_dir / "sad_flankers3_eccentricity12.png").touch()
        
        # Create dummy error log
        error_log = tmp_path / "data" / "interim" / "generation_errors.log"
        error_log.write_text("WARNING: Overlap | File: bad.png | Reason: Overlap")
        
        # Temporarily override paths
        import utils.stimuli_manifest as sm
        original_stimuli = sm.STIMULI_DIR
        original_log = sm.ERRORS_LOG
        original_manifest = sm.MANIFEST_PATH
        
        sm.STIMULI_DIR = stimuli_dir
        sm.ERRORS_LOG = error_log
        sm.MANIFEST_PATH = tmp_path / "manifest.json"
        
        try:
            manifest = generate_manifest()
            
            assert "metadata" in manifest
            assert "stimuli" in manifest
            assert len(manifest["stimuli"]) == 2 # 2 valid images
            
            # Check entries
            filenames = [e["file_path"].split('/')[-1] for e in manifest["stimuli"]]
            assert "happy_flankers5_eccentricity10.png" in filenames
            assert "sad_flankers3_eccentricity12.png" in filenames
            
            # Check metadata extraction
            happy_entry = next(e for e in manifest["stimuli"] if "happy" in e["file_path"])
            assert happy_entry["status"] == "generated"
            assert happy_entry["emotion"] == "happy"
            assert happy_entry["flanker_count"] == 5
            assert happy_entry["eccentricity"] == 10.0
            
        finally:
            sm.STIMULI_DIR = original_stimuli
            sm.ERRORS_LOG = original_log
            sm.MANIFEST_PATH = original_manifest

    def test_excluded_items_in_manifest(self, tmp_path):
        # Setup
        stimuli_dir = tmp_path / "data" / "interim" / "stimuli"
        stimuli_dir.mkdir(parents=True)
        
        # No images created, but log says one was excluded
        error_log = tmp_path / "data" / "interim" / "generation_errors.log"
        error_log.write_text("WARNING: Overlap | File: excluded.png | Reason: Overlap")
        
        import utils.stimuli_manifest as sm
        original_stimuli = sm.STIMULI_DIR
        original_log = sm.ERRORS_LOG
        original_manifest = sm.MANIFEST_PATH
        
        sm.STIMULI_DIR = stimuli_dir
        sm.ERRORS_LOG = error_log
        sm.MANIFEST_PATH = tmp_path / "manifest.json"
        
        try:
            manifest = generate_manifest()
            
            # Should have 1 entry for the excluded item
            assert len(manifest["stimuli"]) == 1
            entry = manifest["stimuli"][0]
            assert entry["status"] == "excluded"
            assert "exclusion_reason" in entry
        finally:
            sm.STIMULI_DIR = original_stimuli
            sm.ERRORS_LOG = original_log
            sm.MANIFEST_PATH = original_manifest
