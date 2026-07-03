import pytest
import pandas as pd
import numpy as np
from code.preprocess import detect_outliers_iqr, clean_data, normalize_rt, extract_features

@pytest.fixture
def sample_data():
    """
    Create a sample DataFrame with known outliers.
    Group A: Normal distribution around 500ms
    Group B: Normal distribution around 600ms
    """
    data = {
        'ParticipantID': [f'P{i}' for i in range(100)],
        'Condition': ['A'] * 50 + ['B'] * 50,
        'Reaction Time': [500] * 48 + [1500] + [100] + [600] * 48 + [2000] + [200],
        'Mood': [5.0] * 100
    }
    # Intentional outliers:
    # Group A: 1500 (very high), 100 (very low)
    # Group B: 2000 (very high), 200 (very low)
    return pd.DataFrame(data)

def test_outlier_detection_iqr(sample_data):
    """
    Test that detect_outliers_iqr correctly flags outliers per group.
    """
    # The IQR for Group A (mostly 500) will be 0 or very small.
    # Q1=500, Q3=500, IQR=0. Bounds: 500 +/- 0 => [500, 500].
    # 1500 and 100 should be flagged.
    # Same logic for Group B (mostly 600).
    
    result = detect_outliers_iqr(sample_data, group_col='Condition', rt_col='Reaction Time')
    
    # Check that the column exists
    assert 'is_outlier' in result.columns
    
    # Count outliers
    outlier_count = result['is_outlier'].sum()
    
    # We expect 4 outliers: 1500, 100 in A; 2000, 200 in B
    assert outlier_count == 4, f"Expected 4 outliers, found {outlier_count}"
    
    # Verify specific rows
    # Find rows where RT is 1500, 100, 2000, 200
    outliers = result[result['is_outlier']]
    outlier_values = outliers['Reaction Time'].tolist()
    
    assert 1500 in outlier_values
    assert 100 in outlier_values
    assert 2000 in outlier_values
    assert 200 in outlier_values

def test_clean_data_removes_na():
    """
    Test that clean_data removes rows with missing critical fields.
    """
    data = {
        'Condition': ['A', 'A', 'B', None],
        'Reaction Time': [500, None, 600, 700],
        'Mood': [5.0, 5.0, None, 5.0]
    }
    df = pd.DataFrame(data)
    
    cleaned = clean_data(df)
    
    # Original had 4 rows.
    # Row 0: Valid
    # Row 1: RT is None -> Dropped
    # Row 2: Mood is None -> Dropped
    # Row 3: Condition is None -> Dropped
    # Expected 1 row remaining.
    assert len(cleaned) == 1

def test_normalize_rt_zscore():
    """
    Test that normalize_rt produces z-scores with mean ~0 and std ~1 per group.
    """
    data = {
        'Condition': ['A'] * 10 + ['B'] * 10,
        'Reaction Time': [100, 100, 100, 100, 100, 200, 200, 200, 200, 200] * 1 + [300] * 10
    }
    df = pd.DataFrame(data)
    
    normalized = normalize_rt(df)
    
    # Check Group A
    group_a = normalized[normalized['Condition'] == 'A']
    mean_a = group_a['rt_zscore'].mean()
    std_a = group_a['rt_zscore'].std()
    
    # Check Group B
    group_b = normalized[normalized['Condition'] == 'B']
    mean_b = group_b['rt_zscore'].mean()
    std_b = group_b['rt_zscore'].std()
    
    # Allow small floating point errors
    assert abs(mean_a) < 1e-5
    assert abs(std_a - 1.0) < 1e-5
    assert abs(mean_b) < 1e-5
    assert abs(std_b - 1.0) < 1e-5

def test_extract_features_aggregation():
    """
    Test that extract_features correctly aggregates mean RT and Mood per participant.
    """
    data = {
        'ParticipantID': ['P1', 'P1', 'P2', 'P2'],
        'Condition': ['A', 'B', 'A', 'B'],
        'Reaction Time': [100, 200, 150, 250],
        'Mood': [1.0, 2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    
    features = extract_features(df)
    
    # P1 in A: mean_rt = 100, avg_mood = 1.0
    p1_a = features[(features['ParticipantID'] == 'P1') & (features['Condition'] == 'A')]
    assert p1_a['mean_rt'].iloc[0] == 100
    assert p1_a['avg_mood'].iloc[0] == 1.0
    
    # P2 in B: mean_rt = 250, avg_mood = 4.0
    p2_b = features[(features['ParticipantID'] == 'P2') & (features['Condition'] == 'B')]
    assert p2_b['mean_rt'].iloc[0] == 250
    assert p2_b['avg_mood'].iloc[0] == 4.0