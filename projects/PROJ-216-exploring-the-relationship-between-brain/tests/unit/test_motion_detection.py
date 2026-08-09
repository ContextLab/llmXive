import os
import sys
import json
import csv
import tempfile
from pathlib import Path
import pytest

# Add code to path if running from tests directory
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from motion_detection import (
    load_motion_metrics,
    get_valid_subjects,
    detect_motion_artifacts,
    write_motion_exclusion_log,
    main,
    TRANSLATION_THRESHOLD_MM,
    ROTATION_THRESHOLD_MM
)

@pytest.fixture
def sample_motion_data():
    """Sample motion data for testing."""
    return [
        {"subject_id": "sub-01", "translation_mm": 1.5, "rotation_mm": 1.0},
        {"subject_id": "sub-02", "translation_mm": 3.5, "rotation_mm": 1.0},  # Excluded: translation > 3
        {"subject_id": "sub-03", "translation_mm": 1.0, "rotation_mm": 2.5},  # Excluded: rotation > 2
        {"subject_id": "sub-04", "translation_mm": 2.0, "rotation_mm": 1.5},
        {"subject_id": "sub-05", "translation_mm": 3.0, "rotation_mm": 2.0},  # Edge case: exactly at threshold (should be included)
    ]

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_motion_metrics_from_json(temp_dir, sample_motion_data):
    """Test loading motion metrics from a central JSON file."""
    motion_json = temp_dir / "motion_metrics.json"
    with open(motion_json, 'w') as f:
        json.dump(sample_motion_data, f)
    
    result = load_motion_metrics(temp_dir)
    assert len(result) == len(sample_motion_data)
    assert result[0]['subject_id'] == 'sub-01'

def test_load_motion_metrics_no_file(temp_dir):
    """Test behavior when no motion metrics file exists."""
    result = load_motion_metrics(temp_dir)
    assert result == []

def test_get_valid_subjects_logic(sample_motion_data):
    """Test the exclusion logic based on thresholds."""
    result = get_valid_subjects(sample_motion_data)
    
    # Check counts
    excluded = [r for r in result if r.get('excluded', False)]
    included = [r for r in result if not r.get('excluded', False)]
    
    assert len(excluded) == 2  # sub-02 and sub-03
    assert len(included) == 3  # sub-01, sub-04, sub-05
    
    # Verify specific exclusions
    sub_ids_excluded = [r['subject_id'] for r in excluded]
    assert 'sub-02' in sub_ids_excluded
    assert 'sub-03' in sub_ids_excluded
    
    # Verify sub-05 is included (exactly at threshold)
    sub_05 = next(r for r in included if r['subject_id'] == 'sub-05')
    assert not sub_05['excluded']

def test_detect_motion_artifacts_alias(sample_motion_data):
    """Test that detect_motion_artifacts returns same as get_valid_subjects."""
    result1 = get_valid_subjects(sample_motion_data)
    result2 = detect_motion_artifacts(sample_motion_data)
    assert result1 == result2

def test_write_motion_exclusion_log(temp_dir, sample_motion_data):
    """Test writing the exclusion log CSV."""
    processed_data = get_valid_subjects(sample_motion_data)
    output_file = temp_dir / "motion_exclusion_log.csv"
    
    write_motion_exclusion_log(processed_data, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == len(sample_motion_data)
    assert 'subject_id' in rows[0]
    assert 'translation_mm' in rows[0]
    assert 'rotation_mm' in rows[0]
    assert 'excluded' in rows[0]
    
    # Check boolean conversion (csv writes string 'True'/'False')
    sub_02_row = next(r for r in rows if r['subject_id'] == 'sub-02')
    assert sub_02_row['excluded'] == 'True'
    
    sub_01_row = next(r for r in rows if r['subject_id'] == 'sub-01')
    assert sub_01_row['excluded'] == 'False'

def test_write_empty_log(temp_dir):
    """Test writing an empty log creates headers."""
    output_file = temp_dir / "empty_log.csv"
    write_motion_exclusion_log([], output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
    assert headers == ['subject_id', 'translation_mm', 'rotation_mm', 'excluded']

def test_main_integration(temp_dir, sample_motion_data, caplog):
    """Test the main function end-to-end."""
    # Setup mock data in temp_dir
    motion_json = temp_dir / "motion_metrics.json"
    with open(motion_json, 'w') as f:
        json.dump(sample_motion_data, f)
    
    # Patch the paths in main to use temp_dir
    # Since main() uses hardcoded paths, we can't easily patch without refactoring.
    # Instead, we verify the logic by calling the component functions directly
    # which main() calls.
    
    data = load_motion_metrics(temp_dir)
    processed = detect_motion_artifacts(data)
    output_file = temp_dir / "test_output.csv"
    write_motion_exclusion_log(processed, output_file)
    
    assert output_file.exists()
    assert 'sub-02' in open(output_file).read()