import json
import os
import tempfile
from pathlib import Path
import pytest

# Adjust import based on how tests are run (usually from project root)
# If running from tests/unit, we might need to add parent to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.stimuli_manifest import (
    load_error_log,
    extract_metadata_from_filename,
    generate_manifest,
    get_stimuli_files
)

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        stimuli_dir = base / "data" / "interim" / "stimuli"
        stimuli_dir.mkdir(parents=True)
        error_log_path = base / "data" / "interim" / "generation_errors.log"
        output_path = base / "data" / "interim" / "stimuli_manifest.json"
        yield {
            "base": base,
            "stimuli_dir": stimuli_dir,
            "error_log_path": error_log_path,
            "output_path": output_path
        }

def test_extract_metadata_from_filename_valid():
    filename = "stimulus_001_anger_3flank_10ecc.png"
    metadata = extract_metadata_from_filename(filename)
    
    assert metadata is not None
    assert metadata['id'] == '001'
    assert metadata['emotion'] == 'anger'
    assert metadata['flanker_count'] == 3
    assert metadata['eccentricity'] == 10
    assert metadata['status'] == 'generated'

def test_extract_metadata_from_filename_invalid():
    filename = "random_image.jpg"
    metadata = extract_metadata_from_filename(filename)
    assert metadata is None

def test_load_error_log(temp_dirs):
    error_log_path = temp_dirs['error_log_path']
    
    # Create a mock error log
    with open(error_log_path, 'w') as f:
        f.write("ERROR: stimulus_002_happy_5flank_20ecc - Overlapping flankers detected\n")
        f.write("ERROR: stimulus_003_sad_2flank_15ecc - Invalid frame\n")
    
    excluded = load_error_log(error_log_path)
    
    assert len(excluded) == 2
    assert 'stimulus_002_happy_5flank_20ecc' in excluded
    assert excluded['stimulus_002_happy_5flank_20ecc'] == 'Overlapping flankers detected'
    assert 'stimulus_003_sad_2flank_15ecc' in excluded

def test_generate_manifest(temp_dirs):
    stimuli_dir = temp_dirs['stimuli_dir']
    error_log_path = temp_dirs['error_log_path']
    output_path = temp_dirs['output_path']

    # Create mock stimulus files
    files_to_create = [
        "stimulus_001_anger_3flank_10ecc.png",
        "stimulus_002_happy_5flank_20ecc.png", # This one will be in error log
        "stimulus_003_sad_2flank_15ecc.png"
    ]
    
    for fname in files_to_create:
        (stimuli_dir / fname).touch()

    # Create mock error log
    with open(error_log_path, 'w') as f:
        f.write("ERROR: stimulus_002_happy_5flank_20ecc - Overlapping flankers detected\n")

    manifest = generate_manifest(stimuli_dir, error_log_path, output_path)

    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'stimuli' in data
    assert len(data['stimuli']) == 3 # All 3 files should be in manifest

    # Check specific entries
    entries_by_id = {e['id']: e for e in data['stimuli']}
    
    # Entry 1: Normal
    assert entries_by_id['001']['status'] == 'generated'
    assert entries_by_id['001']['flanker_count'] == 3
    
    # Entry 2: Excluded (should still be in manifest but marked as excluded if file exists, or just logged if not)
    # In our logic, if the file exists, it's marked as excluded.
    assert entries_by_id['002']['status'] == 'excluded'
    assert entries_by_id['002']['exclusion_reason'] == 'Overlapping flankers detected'

    # Entry 3: Normal
    assert entries_by_id['003']['status'] == 'generated'

def test_generate_manifest_empty_stimuli_dir(temp_dirs):
    stimuli_dir = temp_dirs['stimuli_dir']
    error_log_path = temp_dirs['error_log_path']
    output_path = temp_dirs['output_path']
    
    # No files in stimuli_dir
    with open(error_log_path, 'w') as f:
        f.write("")

    manifest = generate_manifest(stimuli_dir, error_log_path, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['total_items'] == 0
    assert len(data['stimuli']) == 0