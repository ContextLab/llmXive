"""
Unit tests for importance_profile schema and serialization.
"""
import pytest
from contracts.importance_profile import ImportanceProfile, ImportanceScore, ImportanceMethod

def test_importance_profile_creation():
    """Test creating an ImportanceProfile."""
    scores = [
        ImportanceScore(feature_name='f1', score=0.5, std_dev=0.1),
        ImportanceScore(feature_name='f2', score=0.3, std_dev=0.05),
    ]
    
    profile = ImportanceProfile(
        window_id=1,
        window_start='2020-01-01',
        window_end='2020-01-30',
        method=ImportanceMethod.PERMUTATION,
        scores=scores,
        model_r_squared=0.85
    )

    assert profile.window_id == 1
    assert profile.method == ImportanceMethod.PERMUTATION
    assert len(profile.scores) == 2

def test_get_ranked_features():
    """Test ranking features by importance."""
    scores = [
        ImportanceScore(feature_name='low', score=0.1),
        ImportanceScore(feature_name='high', score=0.9),
        ImportanceScore(feature_name='mid', score=0.5),
    ]
    
    profile = ImportanceProfile(
        window_id=1,
        window_start='2020-01-01',
        window_end='2020-01-30',
        method=ImportanceMethod.PERMUTATION,
        scores=scores
    )

    ranked = profile.get_ranked_features()
    assert ranked == ['high', 'mid', 'low']

def test_to_csv_row():
    """Test flattening profile to CSV row."""
    scores = [
        ImportanceScore(feature_name='f1', score=0.5),
        ImportanceScore(feature_name='f2', score=0.3),
    ]
    
    profile = ImportanceProfile(
        window_id=1,
        window_start='2020-01-01',
        window_end='2020-01-30',
        method=ImportanceMethod.PERMUTATION,
        scores=scores,
        model_r_squared=0.9
    )

    row = profile.to_csv_row()
    
    assert row['window_id'] == 1
    assert row['method'] == 'permutation'
    assert row['importance_f1'] == 0.5
    assert row['importance_f2'] == 0.3
