"""
Unit tests for the annotator module.

Tests stratified sampling logic, bin assignment, and sample selection.
"""

import os
import sys
import tempfile
import json
import random
from pathlib import Path

import pytest
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from dataset.annotator import (
    load_filtered_tasks,
    bin_constraint,
    select_random_sample_stratified,
    save_annotation_sample
)

# Test fixtures
@pytest.fixture
def sample_data():
    """Create a sample dataset with varying constraint counts."""
    data = []
    # Bin 5: 10 tasks
    for i in range(10):
        data.append({
            'task_id': f'task_5_{i}',
            'raw_prompt': f'Prompt for task 5 {i}',
            'progressive_constraints': [f'c{i}_1', f'c{i}_2', f'c{i}_3', f'c{i}_4', f'c{i}_5'],
            'constraint_count': 5
        })
    
    # Bin 6: 15 tasks
    for i in range(15):
        data.append({
            'task_id': f'task_6_{i}',
            'raw_prompt': f'Prompt for task 6 {i}',
            'progressive_constraints': [f'c{i}_1', f'c{i}_2', f'c{i}_3', f'c{i}_4', f'c{i}_5', f'c{i}_6'],
            'constraint_count': 6
        })
    
    # Bin 7+: 25 tasks (mix of 7, 8, 9)
    for i in range(25):
        count = 7 + (i % 3)  # 7, 8, 9, 7, 8, 9...
        constraints = [f'c{i}_{j}' for j in range(count)]
        data.append({
            'task_id': f'task_7plus_{i}',
            'raw_prompt': f'Prompt for task 7+ {i}',
            'progressive_constraints': constraints,
            'constraint_count': count
        })
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_data.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_bin_constraint():
    """Test that bin_constraint correctly assigns bins."""
    assert bin_constraint(5) == '5'
    assert bin_constraint(6) == '6'
    assert bin_constraint(7) == '7+'
    assert bin_constraint(8) == '7+'
    assert bin_constraint(10) == '7+'
    assert bin_constraint(100) == '7+'

def test_load_filtered_tasks(temp_csv_file, sample_data):
    """Test loading of filtered tasks from CSV."""
    df = load_filtered_tasks(temp_csv_file)
    
    assert len(df) == len(sample_data)
    assert 'task_id' in df.columns
    assert 'raw_prompt' in df.columns
    assert 'progressive_constraints' in df.columns
    assert 'constraint_count' in df.columns

def test_load_filtered_tasks_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_filtered_tasks('/nonexistent/path/file.csv')

def test_load_filtered_tasks_missing_columns(temp_output_dir):
    """Test that missing columns raise ValueError."""
    # Create a file with missing columns
    df_incomplete = pd.DataFrame({
        'task_id': ['task1'],
        'raw_prompt': ['prompt1']
    })
    temp_path = os.path.join(temp_output_dir, 'incomplete.csv')
    df_incomplete.to_csv(temp_path, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_filtered_tasks(temp_path)

def test_stratified_sampling_distribution(sample_data):
    """Test that stratified sampling produces approximately equal distribution across bins."""
    # Use a small sample size to test logic
    sample_size = 30
    seed = 42
    
    result = select_random_sample_stratified(sample_data, sample_size=sample_size, seed=seed)
    
    # Check total size
    assert len(result) == sample_size
    
    # Check bin distribution
    result['bin'] = result['constraint_count'].apply(bin_constraint)
    bin_counts = result['bin'].value_counts()
    
    # All three bins should be represented (unless a bin is empty in source)
    assert '5' in bin_counts.index
    assert '6' in bin_counts.index
    assert '7+' in bin_counts.index
    
    # Check that no bin exceeds its original size
    original_counts = sample_data['constraint_count'].apply(bin_constraint).value_counts()
    for bin_label, count in bin_counts.items():
        assert count <= original_counts.get(bin_label, 0)

def test_stratified_sampling_all_available(sample_data):
    """Test sampling when requested size exceeds available tasks."""
    # Request more than available
    large_sample_size = 1000
    seed = 42
    
    result = select_random_sample_stratified(sample_data, sample_size=large_sample_size, seed=seed)
    
    # Should return all available tasks
    assert len(result) == len(sample_data)

def test_stratified_sampling_small_dataset():
    """Test sampling with a very small dataset."""
    small_data = pd.DataFrame([
        {'task_id': 't1', 'raw_prompt': 'p1', 'progressive_constraints': ['c1']*5, 'constraint_count': 5},
        {'task_id': 't2', 'raw_prompt': 'p2', 'progressive_constraints': ['c2']*6, 'constraint_count': 6},
        {'task_id': 't3', 'raw_prompt': 'p3', 'progressive_constraints': ['c3']*7, 'constraint_count': 7},
    ])
    
    # Request 50 (minimum) but only 3 available
    result = select_random_sample_stratified(small_data, sample_size=50, seed=42)
    
    # Should return all available
    assert len(result) == 3

def test_save_annotation_sample(sample_data, temp_output_dir):
    """Test saving the annotation sample to CSV."""
    # Select a sample
    sample_df = select_random_sample_stratified(sample_data, sample_size=20, seed=42)
    
    # Save to file
    output_path = os.path.join(temp_output_dir, 'annotation_sample.csv')
    save_annotation_sample(sample_df, output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Load and verify schema
    saved_df = pd.read_csv(output_path)
    
    required_columns = ['task_id', 'raw_prompt', 'constraint_list', 'constraint_count']
    for col in required_columns:
        assert col in saved_df.columns
    
    # Verify row count matches
    assert len(saved_df) == len(sample_df)

def test_stratified_sampling_reproducibility(sample_data):
    """Test that same seed produces same result."""
    seed = 123
    sample_size = 25
    
    result1 = select_random_sample_stratified(sample_data, sample_size=sample_size, seed=seed)
    result2 = select_random_sample_stratified(sample_data, sample_size=sample_size, seed=seed)
    
    # Should be identical
    assert len(result1) == len(result2)
    assert list(result1['task_id']) == list(result2['task_id'])

def test_minimum_sample_size_enforcement(sample_data):
    """Test that sample size is enforced to minimum of 50."""
    # Request less than minimum
    result = select_random_sample_stratified(sample_data, sample_size=10, seed=42)
    
    # Should be at least 50 (or all available if less)
    assert len(result) >= 50 or len(result) == len(sample_data)