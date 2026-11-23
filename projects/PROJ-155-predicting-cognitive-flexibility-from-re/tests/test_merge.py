"""
Tests for the merge functionality (T014).
"""

import os
import tempfile
import pandas as pd
import pytest

from code.data.merge import load_neuro_features, load_behavioral_scores, merge_datasets

@pytest.fixture
def temp_neuro_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Subject_ID,Mean_FD,Other_Feature\n")
        f.write("1001,0.15,1.2\n")
        f.write("1002,0.25,1.3\n")
        f.write("1003,0.10,1.4\n")
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_behavioral_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Subject,NIH_DCCS_TotalScore,Age\n")
        f.write("1001,10.5,25\n")
        f.write("1002,12.0,30\n")
        f.write("1004,11.0,28\n") # 1004 is in behavioral but not neuro
    path = f.name
    yield path
    os.unlink(path)

def test_load_neuro_features(temp_neuro_csv):
    df = load_neuro_features(temp_neuro_csv)
    assert len(df) == 3
    assert 'Subject_ID' in df.columns
    assert 'Mean_FD' in df.columns
    assert df['Subject_ID'].dtype == 'object'

def test_load_behavioral_scores(temp_behavioral_csv):
    df = load_behavioral_scores(temp_behavioral_csv)
    assert len(df) == 3
    assert 'Subject_ID' in df.columns
    assert 'Flexibility_Score' in df.columns
    assert 'Subject_ID' in df.columns
    assert df['Flexibility_Score'].dtype in ['float64', 'int64']

def test_merge_datasets(temp_neuro_csv, temp_behavioral_csv):
    neuro_df = load_neuro_features(temp_neuro_csv)
    behav_df = load_behavioral_scores(temp_behavioral_csv)

    merged = merge_datasets(neuro_df, behav_df)

    # Inner join: 1001 and 1002 should be present. 1003 (neuro only) and 1004 (behav only) excluded.
    assert len(merged) == 2
    assert set(merged['Subject_ID']) == {'1001', '1002'}
    assert 'Flexibility_Score' in merged.columns

def test_merge_empty_neuro(temp_behavioral_csv):
    empty_neuro = pd.DataFrame(columns=['Subject_ID', 'Mean_FD'])
    behav_df = load_behavioral_scores(temp_behavioral_csv)
    with pytest.raises(ValueError, match="Neuro features DataFrame is empty"):
        merge_datasets(empty_neuro, behav_df)

def test_merge_empty_behavioral(temp_neuro_csv):
    neuro_df = load_neuro_features(temp_neuro_csv)
    empty_behav = pd.DataFrame(columns=['Subject_ID', 'Flexibility_Score'])
    with pytest.raises(ValueError, match="Behavioral scores DataFrame is empty"):
        merge_datasets(neuro_df, empty_behav)
