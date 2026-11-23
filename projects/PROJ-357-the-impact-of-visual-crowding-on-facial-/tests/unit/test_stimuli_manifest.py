import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.stimuli_manifest import extract_metadata_from_filename, load_error_log, generate_manifest

class TestExtractMetadata:
    def test_valid_filename_strict(self):
        filename = "stimulus_angry_flankers_5_eccentricity_10.5.png"
        expected = {
            "emotion": "angry",
            "flanker_count": 5,
            "eccentricity": 10.5
        }
        result = extract_metadata_from_filename(filename)
        assert result == expected

    def test_valid_filename_variations(self):
        # Test with 'flanker' singular
        filename = "stimulus_happy_flanker_3_eccentricity_5.0.png"
        result = extract_metadata_from_filename(filename)
        assert result is not None
        assert result['emotion'] == 'happy'
        assert result['flanker_count'] == 3
        
        # Test with float eccentricity
        filename = "stimulus_neutral_flankers_12_eccentricity_15.75.png"
        result = extract_metadata_from_filename(filename)
        assert result['eccentricity'] == 15.75

    def test_invalid_filename(self):
        filename = "random_image_001.png"
        result = extract_metadata_from_filename(filename)
        assert result is None

class TestLoadErrorLog:
    def test_empty_log(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            result = load_error_log(temp_path)
            assert result == []
        finally:
            os.unlink(temp_path)

    def test_valid_json_log(self):
        log_data = [
            {"filename": "bad_1.png", "reason": "overlap"},
            {"filename": "bad_2.png", "reason": "missing_frame"}
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            for entry in log_data:
                f.write(json.dumps(entry) + "\n")
            temp_path = Path(f.name)
        
        try:
            result = load_error_log(temp_path)
            assert len(result) == 2
            assert result[0]['filename'] == 'bad_1.png'
        finally:
            os.unlink(temp_path)

class TestGenerateManifest:
    def test_full_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stimuli_dir = Path(tmpdir) / "stimuli"
            stimuli_dir.mkdir()
            
            # Create dummy images
            (stimuli_dir / "stimulus_angry_flankers_5_eccentricity_10.0.png").touch()
            (stimuli_dir / "stimulus_happy_flankers_3_eccentricity_5.0.png").touch()
            
            # Create error log
            error_log_path = Path(tmpdir) / "errors.log"
            with open(error_log_path, 'w') as f:
                f.write(json.dumps({"filename": "stimulus_angry_flankers_5_eccentricity_10.0.png", "reason": "overlap"}) + "\n")
            
            output_path = Path(tmpdir) / "manifest.json"
            
            manifest = generate_manifest(stimuli_dir, error_log_path, output_path)
            
            assert output_path.exists()
            assert manifest['total_stimuli'] == 2
            
            # Check entries
            entries = {e['filename']: e for e in manifest['entries']}
            assert 'stimulus_angry_flankers_5_eccentricity_10.0.png' in entries
            assert entries['stimulus_angry_flankers_5_eccentricity_10.0.png']['status'] == 'excluded'
            assert entries['stimulus_happy_flankers_3_eccentricity_5.0.png']['status'] == 'generated'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])