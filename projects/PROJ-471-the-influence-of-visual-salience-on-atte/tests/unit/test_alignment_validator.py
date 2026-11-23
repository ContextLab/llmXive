"""
Unit tests for code/processing/alignment_validator.py (T025).
"""
import os
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
import pytest
from PIL import Image

# Import the module under test
# Note: We assume the module is importable from the project root context
# In a real run, PYTHONPATH would include the project root.
from processing.alignment_validator import (
    load_aligned_dataset,
    load_salience_maps_index,
    load_face_masks_index,
    validate_alignment,
    write_validation_report
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

@pytest.fixture
def sample_aligned_df():
    """Create a sample aligned dataframe."""
    data = {
        'trial_id': ['T001', 'T002', 'T003', 'T004'],
        'dwell_time': [100.5, 200.0, 150.2, 300.1],
        'first_fixation_prob': [0.8, 0.6, 0.9, 0.7],
        'salience_score': [0.5, 0.6, 0.55, 0.65]
    }
    return pd.DataFrame(data)

def test_load_aligned_dataset_missing_file(temp_dir):
    """Test that loading a missing file raises FileNotFoundError."""
    non_existent = temp_dir / "missing.csv"
    with pytest.raises(FileNotFoundError):
        load_aligned_dataset(non_existent)

def test_load_aligned_dataset_success(temp_dir, sample_aligned_df):
    """Test successful loading of aligned dataset."""
    csv_path = temp_dir / "aligned.csv"
    sample_aligned_df.to_csv(csv_path, index=False)
    
    df = load_aligned_dataset(csv_path)
    assert len(df) == 4
    assert 'trial_id' in df.columns

def test_load_salience_maps_index_empty_dir(temp_dir):
    """Test loading salience index from empty directory."""
    salience_dir = temp_dir / "salience"
    salience_dir.mkdir(parents=True, exist_ok=True)
    
    index = load_salience_maps_index(salience_dir)
    assert len(index) == 0

def test_load_salience_maps_index_with_files(temp_dir):
    """Test loading salience index with .npy files."""
    salience_dir = temp_dir / "salience"
    salience_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy .npy files
    (salience_dir / "T001.npy").touch()
    (salience_dir / "T002.npy").touch()
    
    index = load_salience_maps_index(salience_dir)
    assert len(index) == 2
    assert set(index['trial_id']) == {'T001', 'T002'}

def test_load_face_masks_index_valid_and_invalid(temp_dir):
    """Test loading face masks and detecting empty ones."""
    masks_dir = temp_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    
    # Valid mask (non-zero area)
    valid_img = Image.new('L', (10, 10), color=255)
    valid_img.save(masks_dir / "T001.png")
    
    # Empty mask (zero area)
    empty_img = Image.new('L', (10, 10), color=0)
    empty_img.save(masks_dir / "T002.png")
    
    # Corrupted file (simulate invalid)
    (masks_dir / "T003.npy").write_text("not a numpy file")
    
    index = load_face_masks_index(masks_dir)
    
    # T001 should be valid, T002 empty, T003 invalid
    t001 = index[index['trial_id'] == 'T001'].iloc[0]
    t002 = index[index['trial_id'] == 'T002'].iloc[0]
    t003 = index[index['trial_id'] == 'T003'].iloc[0]
    
    assert t001['is_valid'] == True
    assert t001['mask_area'] > 0
    
    assert t002['is_valid'] == False
    assert t002['mask_area'] == 0
    
    assert t003['is_valid'] == False

def test_validate_alignment_no_issues(temp_dir, sample_aligned_df):
    """Test validation when all data is present and valid."""
    # Setup directories
    salience_dir = temp_dir / "salience"
    salience_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = temp_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    
    # Create matching files
    for tid in sample_aligned_df['trial_id']:
        (salience_dir / f"{tid}.npy").touch()
        # Create a valid mask
        img = Image.new('L', (10, 10), color=255)
        img.save(masks_dir / f"{tid}.png")
    
    salience_idx = load_salience_maps_index(salience_dir)
    mask_idx = load_face_masks_index(masks_dir)
    
    validated_df, report = validate_alignment(sample_aligned_df, salience_idx, mask_idx)
    
    assert report['missing_salience'] == []
    assert report['missing_masks'] == []
    assert report['empty_masks'] == []
    assert report['flagged_for_review'] == 0
    assert 'needs_manual_review' in validated_df.columns
    assert validated_df['needs_manual_review'].sum() == 0

def test_validate_alignment_missing_salience(temp_dir, sample_aligned_df):
    """Test validation when salience maps are missing for some trials."""
    salience_dir = temp_dir / "salience"
    salience_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = temp_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    
    # Only create salience for T001 and T002
    (salience_dir / "T001.npy").touch()
    (salience_dir / "T002.npy").touch()
    
    # Create masks for all
    for tid in sample_aligned_df['trial_id']:
        img = Image.new('L', (10, 10), color=255)
        img.save(masks_dir / f"{tid}.png")
    
    salience_idx = load_salience_maps_index(salience_dir)
    mask_idx = load_face_masks_index(masks_dir)
    
    validated_df, report = validate_alignment(sample_aligned_df, salience_idx, mask_idx)
    
    assert set(report['missing_salience']) == {'T003', 'T004'}
    assert report['flagged_for_review'] == 2

def test_validate_alignment_empty_masks(temp_dir, sample_aligned_df):
    """Test validation when masks are empty for some trials."""
    salience_dir = temp_dir / "salience"
    salience_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = temp_dir / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    
    # Create salience for all
    for tid in sample_aligned_df['trial_id']:
        (salience_dir / f"{tid}.npy").touch()
    
    # Create masks: T001 valid, T002 empty
    valid_img = Image.new('L', (10, 10), color=255)
    valid_img.save(masks_dir / "T001.png")
    
    empty_img = Image.new('L', (10, 10), color=0)
    empty_img.save(masks_dir / "T002.png")
    
    # Others valid
    for tid in ['T003', 'T004']:
        img = Image.new('L', (10, 10), color=255)
        img.save(masks_dir / f"{tid}.png")
    
    salience_idx = load_salience_maps_index(salience_dir)
    mask_idx = load_face_masks_index(masks_dir)
    
    validated_df, report = validate_alignment(sample_aligned_df, salience_idx, mask_idx)
    
    assert set(report['empty_masks']) == {'T002'}
    assert report['flagged_for_review'] == 1

def test_write_validation_report(temp_dir, sample_aligned_df):
    """Test writing the validation report to JSON."""
    report = {
        'total_trials': 4,
        'missing_salience': [],
        'missing_masks': [],
        'empty_masks': [],
        'valid_trials': 4,
        'flagged_for_review': 0,
        'issues': []
    }
    
    report_path = temp_dir / "validation_report.json"
    write_validation_report(report, report_path)
    
    assert report_path.exists()
    with open(report_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded['total_trials'] == 4
    assert loaded['flagged_for_review'] == 0
