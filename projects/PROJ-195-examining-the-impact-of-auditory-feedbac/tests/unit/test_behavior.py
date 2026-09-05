import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from behavior import (
    extract_trial_rts,
    calculate_learning_rate_slope,
    process_subject_behavior,
    load_valid_subjects,
    find_event_tsv
)

@pytest.fixture
def sample_events_df():
    """Create a sample events DataFrame with realistic trial data."""
    data = {
        'trial': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'onset': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45],
        'duration': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'trial_type': ['normal', 'delayed', 'pitch-shifted', 'normal', 'delayed',
                     'pitch-shifted', 'normal', 'delayed', 'pitch-shifted', 'normal'],
        'response': [500, 520, 510, 490, 530, 515, 480, 540, 505, 470]  # RT in ms
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_events_with_misses():
    """Create sample events with some misses (response=0)."""
    data = {
        'trial': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'onset': [0, 5, 10, 15, 20, 25, 30, 35, 40, 45],
        'duration': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        'trial_type': ['normal', 'delayed', 'pitch-shifted', 'normal', 'delayed',
                     'pitch-shifted', 'normal', 'delayed', 'pitch-shifted', 'normal'],
        'response': [500, 0, 510, 0, 530, 515, 0, 540, 505, 470]  # Some misses
    }
    return pd.DataFrame(data)

def test_extract_trial_rts_valid(sample_events_df):
    """Test extraction of reaction times from valid events."""
    import logging
    logger = logging.getLogger("test")
    
    rt_df = extract_trial_rts(sample_events_df, logger)
    
    assert len(rt_df) == 10
    assert 'rt' in rt_df.columns
    assert 'trial' in rt_df.columns
    assert all(rt_df['rt'] > 0)
    assert all(rt_df['rt'] <= 5000)

def test_extract_trial_rts_with_misses(sample_events_with_misses):
    """Test that misses are filtered out when response is binary."""
    import logging
    logger = logging.getLogger("test")
    
    rt_df = extract_trial_rts(sample_events_with_misses, logger)
    
    # Should filter out trials with response=0
    assert len(rt_df) < 10
    assert all(rt_df['rt'] > 0)

def test_extract_trial_rts_with_rt_column():
    """Test extraction when 'rt' column exists."""
    data = {
        'trial': [1, 2, 3, 4, 5],
        'onset': [0, 5, 10, 15, 20],
        'duration': [2, 2, 2, 2, 2],
        'rt': [500, 520, 510, 490, 530]
    }
    df = pd.DataFrame(data)
    import logging
    logger = logging.getLogger("test")
    
    rt_df = extract_trial_rts(df, logger)
    
    assert len(rt_df) == 5
    assert all(rt_df['rt'] == [500, 520, 510, 490, 530])

def test_calculate_learning_rate_slope_independence():
    """
    Test that slope is calculated over ALL trials and is independent of condition labels.
    This verifies the global learning rate proxy implementation per T011 amendment.
    """
    # Create data where RT decreases linearly with trial number
    # but condition labels are mixed
    np.random.seed(42)
    trials = np.arange(1, 101)  # 100 trials
    # Linear decrease: RT = 600 - 1.5 * trial + noise
    rts = 600 - 1.5 * trials + np.random.normal(0, 20, 100)
    
    df = pd.DataFrame({
        'trial': trials,
        'rt': rts,
        'trial_type': np.random.choice(['normal', 'delayed', 'pitch-shifted'], 100)
    })
    
    slope, intercept, stats = calculate_learning_rate_slope(df)
    
    # Slope should be approximately -1.5 (negative = learning)
    assert -2.0 < slope < -1.0, f"Slope {slope} not in expected range"
    assert stats['n_trials'] == 100
    assert stats['p_value'] < 0.05  # Should be significant
    assert stats['r_squared'] > 0.8  # Strong linear relationship

def test_calculate_learning_rate_slope_empty():
    """Test that empty dataframe raises error."""
    df = pd.DataFrame(columns=['trial', 'rt'])
    
    with pytest.raises(ValueError, match="Cannot calculate slope from empty dataframe"):
        calculate_learning_rate_slope(df)

def test_calculate_learning_rate_slope_noisy():
    """Test slope calculation with noisy data."""
    np.random.seed(123)
    trials = np.arange(1, 51)
    # Flat trend with noise
    rts = 500 + np.random.normal(0, 50, 50)
    
    df = pd.DataFrame({
        'trial': trials,
        'rt': rts
    })
    
    slope, intercept, stats = calculate_learning_rate_slope(df)
    
    # Slope should be close to 0
    assert -5 < slope < 5, f"Slope {slope} not close to 0 for flat data"
    assert stats['n_trials'] == 50

def test_process_subject_behavior(tmp_path):
    """Test full subject behavior processing pipeline."""
    # Create mock subject directory structure
    subject_dir = tmp_path / "sub-01"
    func_dir = subject_dir / "func"
    func_dir.mkdir(parents=True)
    
    # Create events.tsv
    events_data = {
        'trial': list(range(1, 21)),
        'onset': list(range(0, 100, 5)),
        'duration': [2] * 20,
        'response': [500 - i * 2 + np.random.randint(-10, 10) for i in range(20)]
    }
    events_df = pd.DataFrame(events_data)
    events_file = func_dir / "sub-01_task-motor_events.tsv"
    events_df.to_csv(events_file, sep='\t', index=False)
    
    # Create output path
    output_csv = tmp_path / "output.csv"
    
    import logging
    logger = logging.getLogger("test")
    
    result = process_subject_behavior(subject_dir, output_csv, logger)
    
    assert result is not None
    assert 'slope' in result
    assert 'subject' in result
    assert result['subject'] == 'sub-01'
    assert output_csv.exists()
    
    # Verify CSV content
    saved_df = pd.read_csv(output_csv)
    assert len(saved_df) == 1
    assert saved_df.iloc[0]['slope'] == result['slope']

def test_load_valid_subjects(tmp_path):
    """Test loading valid subjects from file."""
    subjects_file = tmp_path / "valid_subjects.txt"
    subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-05']
    with open(subjects_file, 'w') as f:
        f.write('\n'.join(subjects))
    
    loaded = load_valid_subjects(subjects_file)
    assert loaded == subjects

def test_find_event_tsv(tmp_path):
    """Test finding events.tsv file."""
    subject_dir = tmp_path / "sub-01"
    func_dir = subject_dir / "func"
    func_dir.mkdir(parents=True)
    
    # Create events file
    events_file = func_dir / "sub-01_task-motor_events.tsv"
    pd.DataFrame({'trial': [1]}).to_csv(events_file, sep='\t', index=False)
    
    found = find_event_tsv(subject_dir)
    assert found == events_file

def test_learning_rate_slope_calculation_order():
    """Test that slope is calculated in correct trial order regardless of input order."""
    # Create data in reverse order
    trials = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    rts = [500, 510, 520, 530, 540, 550, 560, 570, 580, 590]  # Increasing RT = negative learning
    
    df = pd.DataFrame({
        'trial': trials,
        'rt': rts
    })
    
    slope, intercept, stats = calculate_learning_rate_slope(df)
    
    # Slope should be positive (RT increases with trial number)
    assert slope > 0
    assert stats['n_trials'] == 10