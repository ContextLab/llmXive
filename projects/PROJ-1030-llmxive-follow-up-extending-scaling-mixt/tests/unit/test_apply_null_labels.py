import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from apply_null_labels import (
    load_temp_labels,
    process_labels_and_exclusions,
    save_labels_csv,
    save_excluded_log,
    CONFIDENCE_THRESHOLD
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

def test_process_labels_low_confidence(temp_dir):
    """Test that samples with confidence < 0.9 are marked as null."""
    # Create sample data
    temp_labels = [
        {'clip_id': 'clip_001', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.95, 'perturbation_type': 0},
        {'clip_id': 'clip_002', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.85, 'perturbation_type': 0},
        {'clip_id': 'clip_003', 'label': 'invalid', 'reason': 'gravity_defied', 'confidence_score': 0.92, 'perturbation_type': 1},
    ]
    
    processed, excluded = process_labels_and_exclusions(temp_labels)
    
    # clip_001 should remain valid
    assert processed[0]['label'] == 'valid'
    assert processed[0]['clip_id'] == 'clip_001'
    
    # clip_002 should become null
    assert processed[1]['label'] == 'null'
    assert processed[1]['clip_id'] == 'clip_002'
    
    # clip_003 should remain invalid (confidence > 0.9)
    assert processed[2]['label'] == 'invalid'
    
    # Check excluded list
    assert len(excluded) == 1
    assert excluded[0]['clip_id'] == 'clip_002'

def test_process_labels_simulation_failure(temp_dir):
    """Test that samples with simulation failure in reason are marked as null."""
    temp_labels = [
        {'clip_id': 'clip_001', 'label': 'valid', 'reason': 'simulation_failed', 'confidence_score': 0.95, 'perturbation_type': 0},
        {'clip_id': 'clip_002', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.95, 'perturbation_type': 0},
    ]
    
    processed, excluded = process_labels_and_exclusions(temp_labels)
    
    # clip_001 should become null due to failure reason
    assert processed[0]['label'] == 'null'
    assert processed[0]['reason'] == 'simulation_failed'
    
    # clip_002 should remain valid
    assert processed[1]['label'] == 'valid'
    
    assert len(excluded) == 1

def test_process_labels_already_null(temp_dir):
    """Test that samples already labeled 'null' are not re-added to excluded."""
    temp_labels = [
        {'clip_id': 'clip_001', 'label': 'null', 'reason': 'previous_failure', 'confidence_score': 0.5, 'perturbation_type': 0},
    ]
    
    processed, excluded = process_labels_and_exclusions(temp_labels)
    
    # Should remain null
    assert processed[0]['label'] == 'null'
    # Should NOT be in excluded list (logic: is_already_null prevents re-exclusion)
    # Note: The current logic in process_labels_and_exclusions adds to excluded ONLY if needs_null_assignment is True.
    # needs_null_assignment is False if is_already_null is True.
    assert len(excluded) == 0

def test_save_labels_csv(temp_dir):
    """Test saving labels to CSV."""
    labels = [
        {'clip_id': 'clip_001', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.95, 'perturbation_type': 0},
        {'clip_id': 'clip_002', 'label': 'null', 'reason': 'low_conf', 'confidence_score': 0.85, 'perturbation_type': 0},
    ]
    output_path = os.path.join(temp_dir, 'labels.csv')
    
    save_labels_csv(labels, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['clip_id'] == 'clip_001'
        assert rows[1]['label'] == 'null'

def test_save_excluded_log_empty(temp_dir):
    """Test that excluded log is created even if empty."""
    excluded = []
    output_path = os.path.join(temp_dir, 'excluded_samples.log')
    
    save_excluded_log(excluded, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0
        # Check header exists
        assert 'clip_id' in reader.fieldnames

def test_save_excluded_log_with_data(temp_dir):
    """Test saving excluded samples."""
    excluded = [
        {'clip_id': 'clip_002', 'reason': 'low_conf', 'confidence_score': 0.85},
    ]
    output_path = os.path.join(temp_dir, 'excluded_samples.log')
    
    save_excluded_log(excluded, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['clip_id'] == 'clip_002'