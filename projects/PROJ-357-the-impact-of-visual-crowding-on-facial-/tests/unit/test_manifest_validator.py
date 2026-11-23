import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.manifest_validator import (
    load_manifest,
    get_stimuli_files,
    validate_manifest_completeness,
    generate_validation_report
)

@pytest.fixture
def temp_directories():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        stimuli_dir = tmpdir / "stimuli"
        stimuli_dir.mkdir()
        
        # Create some dummy image files
        for i in range(5):
            (stimuli_dir / f"stimulus_{i}.png").touch()
        
        yield {
            'base': tmpdir,
            'stimuli': stimuli_dir
        }

def test_load_manifest_success(temp_directories):
    """Test loading a valid manifest file."""
    manifest_path = temp_directories['base'] / "manifest.json"
    test_manifest = [
        {"file": "stimulus_0.png", "emotion": "happy", "flanker_count": 4, "eccentricity": 5},
        {"file": "stimulus_1.png", "emotion": "sad", "flanker_count": 6, "eccentricity": 10}
    ]
    
    with open(manifest_path, 'w') as f:
        json.dump(test_manifest, f)
    
    loaded = load_manifest(manifest_path)
    assert len(loaded) == 2
    assert loaded[0]['file'] == "stimulus_0.png"

def test_load_manifest_not_found():
    """Test loading a non-existent manifest file raises error."""
    with pytest.raises(FileNotFoundError):
        load_manifest(Path("/nonexistent/path/manifest.json"))

def test_get_stimuli_files(temp_directories):
    """Test getting list of stimuli files."""
    files = get_stimuli_files(temp_directories['stimuli'])
    assert len(files) == 5
    assert all(f.endswith('.png') for f in files)

def test_get_stimuli_files_not_found():
    """Test getting files from non-existent directory raises error."""
    with pytest.raises(FileNotFoundError):
        get_stimuli_files(Path("/nonexistent/directory"))

def test_validate_manifest_completeness_complete(temp_directories):
    """Test validation when all files are present and valid."""
    manifest = [
        {"file": "stimulus_0.png", "emotion": "happy", "flanker_count": 4, "eccentricity": 5},
        {"file": "stimulus_1.png", "emotion": "sad", "flanker_count": 6, "eccentricity": 10},
        {"file": "stimulus_2.png", "emotion": "angry", "flanker_count": 3, "eccentricity": 8},
        {"file": "stimulus_3.png", "emotion": "fear", "flanker_count": 5, "eccentricity": 12},
        {"file": "stimulus_4.png", "emotion": "neutral", "flanker_count": 7, "eccentricity": 15}
    ]
    
    files = ["stimulus_0.png", "stimulus_1.png", "stimulus_2.png", "stimulus_3.png", "stimulus_4.png"]
    
    is_valid, missing, invalid = validate_manifest_completeness(manifest, files)
    
    assert is_valid is True
    assert len(missing) == 0
    assert len(invalid) == 0

def test_validate_manifest_completeness_missing_files(temp_directories):
    """Test validation when some files are missing from manifest."""
    manifest = [
        {"file": "stimulus_0.png", "emotion": "happy", "flanker_count": 4, "eccentricity": 5}
    ]
    
    files = ["stimulus_0.png", "stimulus_1.png", "stimulus_2.png"]
    
    is_valid, missing, invalid = validate_manifest_completeness(manifest, files)
    
    assert is_valid is False
    assert len(missing) == 2
    assert "stimulus_1.png" in missing
    assert "stimulus_2.png" in missing
    assert len(invalid) == 0

def test_validate_manifest_completeness_invalid_entries(temp_directories):
    """Test validation when manifest entries have missing parameters."""
    manifest = [
        {"file": "stimulus_0.png", "emotion": "happy"},  # Missing flanker_count and eccentricity
        {"file": "stimulus_1.png", "flanker_count": 4},  # Missing emotion and eccentricity
        {"file": "stimulus_2.png", "emotion": "sad", "flanker_count": 3, "eccentricity": 8}  # Valid
    ]
    
    files = ["stimulus_0.png", "stimulus_1.png", "stimulus_2.png"]
    
    is_valid, missing, invalid = validate_manifest_completeness(manifest, files)
    
    assert is_valid is False
    assert len(missing) == 0
    assert len(invalid) == 2

def test_generate_validation_report(temp_directories):
    """Test generating a complete validation report."""
    manifest_path = temp_directories['base'] / "manifest.json"
    error_log_path = temp_directories['base'] / "errors.log"
    output_path = temp_directories['base'] / "validation_report.json"
    
    # Create manifest
    manifest = [
        {"file": "stimulus_0.png", "emotion": "happy", "flanker_count": 4, "eccentricity": 5},
        {"file": "stimulus_1.png", "emotion": "sad", "flanker_count": 6, "eccentricity": 10}
    ]
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    
    # Create empty error log
    error_log_path.touch()
    
    report = generate_validation_report(manifest_path, temp_directories['stimuli'], error_log_path, output_path)
    
    assert report['status'] == 'incomplete'  # Only 2 in manifest, 5 on disk
    assert 'manifest_entries' in report['summary']
    assert 'stimuli_files_on_disk' in report['summary']
    assert 'missing_files' in report
    assert 'invalid_entries' in report
    
    # Verify file was written
    assert output_path.exists()
    with open(output_path, 'r') as f:
        written_report = json.load(f)
    assert written_report['status'] == report['status']
