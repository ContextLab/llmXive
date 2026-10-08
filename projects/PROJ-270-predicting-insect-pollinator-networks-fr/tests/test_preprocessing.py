import pytest
import pandas as pd
import numpy as np
import logging
import io
import sys
from preprocessing import (
    define_sample, 
    check_temporal_metadata, 
    generate_negative_samples, 
    validate_negative_samples,
    median_imputation,
    flag_missingness,
    winsorize_outliers,
    z_score_normalize,
    one_hot_encode,
    assemble_feature_matrix
)

# Configure logging to capture warnings
@pytest.fixture
def log_capture():
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger('preprocessing')
    logger.addHandler(handler)
    yield log_stream
    logger.removeHandler(handler)

def test_sample_definition_first_n():
    """
    Test that define_sample with method='first_n' selects the first N rows
    and logs the limitation explicitly.
    """
    data = {'val': range(100), 'id': range(100, 200)}
    df = pd.DataFrame(data)
    
    sample_size = 10
    sampled_df, meta = define_sample(df, sample_size=sample_size, method='first_n')
    
    assert len(sampled_df) == sample_size
    assert meta['sampled'] is True
    assert meta['original_size'] == 100
    assert meta['final_size'] == 10
    assert meta['method'] == 'first_n'
    assert 'truncated to first' in meta['limitation']
    assert 'bias if the data is ordered' in meta['limitation']

def test_sample_definition_random():
    """
    Test that define_sample with method='random' selects N rows deterministically
    with a fixed seed and logs the limitation.
    """
    data = {'val': range(100), 'id': range(100, 200)}
    df = pd.DataFrame(data)
    
    sample_size = 10
    seed = 42
    
    # Run twice to ensure determinism
    sampled_df_1, _ = define_sample(df, sample_size=sample_size, method='random', seed=seed)
    sampled_df_2, _ = define_sample(df, sample_size=sample_size, method='random', seed=seed)
    
    pd.testing.assert_frame_equal(sampled_df_1, sampled_df_2)
    
    assert len(sampled_df_1) == sample_size
    assert 'randomly sampled' in _[1]['limitation']
    assert 'seed: 42' in _[1]['limitation']

def test_sample_definition_no_sampling():
    """
    Test that define_sample returns the full dataframe when sample_size is None.
    """
    data = {'val': range(10), 'id': range(10, 20)}
    df = pd.DataFrame(data)
    
    sampled_df, meta = define_sample(df, sample_size=None)
    
    assert len(sampled_df) == 10
    assert meta['sampled'] is False
    assert 'No sampling applied' in meta['limitation']

def test_sample_definition_invalid_method():
    """
    Test that define_sample raises ValueError for unknown method.
    """
    df = pd.DataFrame({'val': [1, 2, 3]})
    with pytest.raises(ValueError):
        define_sample(df, sample_size=2, method='invalid_method')

def test_temporal_metadata_check():
    """Test temporal metadata validation."""
    meta_good = {'start_date': '2020-01-01', 'end_date': '2020-12-31'}
    meta_bad = {'start_date': '2020-01-01'}
    
    assert check_temporal_metadata(meta_good) is True
    assert check_temporal_metadata(meta_bad) is False

def test_negative_sample_generation():
    """Test negative sample generation via spatial co-occurrence."""
    # Positive data
    df_pos = pd.DataFrame({
        'plant_species': ['A', 'B', 'C'],
        'pollinator_species': ['X', 'Y', 'Z'],
        'link_label': [1, 1, 1]
    })
    
    # Generate negatives
    df_neg = generate_negative_samples(df_pos)
    
    # Should not contain A-X, B-Y, C-Z
    assert not ((df_neg['plant_species'] == 'A') & (df_neg['pollinator_species'] == 'X')).any()
    assert len(df_neg) > 0

def test_negative_sample_validation():
    """Test validation of negative samples."""
    df_pos = pd.DataFrame({
        'plant_species': ['A', 'B'],
        'pollinator_species': ['X', 'Y'],
        'link_label': [1, 1]
    })
    df_neg = pd.DataFrame({
        'plant_species': ['A', 'C'],
        'pollinator_species': ['Y', 'X'],
        'link_label': [0, 0]
    })
    
    assert validate_negative_samples(df_neg, df_pos) is True
    
    # Add a positive link to negatives
    df_neg_bad = pd.concat([df_neg, pd.DataFrame({'plant_species': ['A'], 'pollinator_species': ['X'], 'link_label': [0]})])
    assert validate_negative_samples(df_neg_bad, df_pos) is False

def test_median_imputation():
    df = pd.DataFrame({'A': [1.0, 2.0, np.nan, 4.0]})
    result = median_imputation(df, ['A'])
    assert not result['A'].isnull().any()
    assert result['A'].iloc[2] == 2.5 # Median of 1, 2, 4

def test_flag_missingness():
    df_high = pd.DataFrame({'A': [1.0, np.nan, np.nan, np.nan]}) # 75% missing
    df_low = pd.DataFrame({'A': [1.0, 2.0, 3.0, np.nan]}) # 25% missing
    
    assert flag_missingness(df_high, threshold=0.15) is True
    assert flag_missingness(df_low, threshold=0.50) is False

def test_winsorize_outliers():
    df = pd.DataFrame({'A': [1, 2, 3, 4, 100]})
    result = winsorize_outliers(df, ['A'], limits=(0.1, 0.9))
    assert result['A'].max() < 100

def test_z_score_normalize():
    df = pd.DataFrame({'A': [10, 20, 30]})
    result = z_score_normalize(df, ['A'])
    assert np.isclose(result['A'].mean(), 0.0)
    assert np.isclose(result['A'].std(), 1.0)

def test_one_hot_encode():
    df = pd.DataFrame({'cat': ['A', 'B', 'A']})
    result = one_hot_encode(df, ['cat'])
    assert 'cat_A' in result.columns
    assert 'cat_B' in result.columns

def test_assemble_feature_matrix():
    pos = pd.DataFrame({'plant': ['A'], 'pollinator': ['X'], 'trait': [1.0]})
    neg = pd.DataFrame({'plant': ['A'], 'pollinator': ['Y'], 'trait': [2.0]})
    result = assemble_feature_matrix(pos, neg, ['trait'])
    assert len(result) == 2
    assert result['link_label'].sum() == 1
    assert result['link_label'].min() == 0
    assert result['link_label'].max() == 1