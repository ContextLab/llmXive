"""
Unit tests for dataset stratification logic (T009).
"""
import pandas as pd
import pytest
from code.dataset import stratify_tasks
from code.config import config

@pytest.fixture
def sample_df():
    """Create a synthetic DataFrame with known strata for testing."""
    # Create a dataframe with 4 strata:
    # 1. Easy, Math, Python (10 rows)
    # 2. Easy, Math, Rust (5 rows)
    # 3. Hard, Math, Python (20 rows)
    # 4. Hard, Algo, Rust (15 rows)
    data = []
    for i in range(10):
        data.append({'problem': f'p{i}', 'solution': 's', 'language': 'Python', 'difficulty': 'Easy', 'topic': 'Math'})
    for i in range(5):
        data.append({'problem': f'p{i+10}', 'solution': 's', 'language': 'Rust', 'difficulty': 'Easy', 'topic': 'Math'})
    for i in range(20):
        data.append({'problem': f'p{i+15}', 'solution': 's', 'language': 'Python', 'difficulty': 'Hard', 'topic': 'Math'})
    for i in range(15):
        data.append({'problem': f'p{i+35}', 'solution': 's', 'language': 'Rust', 'difficulty': 'Hard', 'topic': 'Algo'})
    
    return pd.DataFrame(data)

def test_stratify_proportional(sample_df):
    """Test that stratification maintains proportional representation."""
    # Total rows: 50. Target: 10.
    # Expected approx:
    # Easy/Math/Python: 10/50 * 10 = 2
    # Easy/Math/Rust: 5/50 * 10 = 1
    # Hard/Math/Python: 20/50 * 10 = 4
    # Hard/Algo/Rust: 15/50 * 10 = 3
    # Sum = 10.
    
    result = stratify_tasks(sample_df, target_n=10)
    
    assert len(result) == 10
    
    # Check distribution
    counts = result.groupby(['difficulty', 'topic', 'language']).size()
    
    # Verify counts match expected proportions (allowing for integer rounding)
    # We check that we didn't exceed available and roughly match ratio
    assert counts[('Easy', 'Math', 'Python')] >= 1
    assert counts[('Easy', 'Math', 'Rust')] >= 1
    assert counts[('Hard', 'Math', 'Python')] >= 3
    assert counts[('Hard', 'Algo', 'Rust')] >= 2

def test_stratify_target_larger_than_available(sample_df):
    """Test behavior when target_n > total rows."""
    result = stratify_tasks(sample_df, target_n=100)
    
    # Should return all rows (50)
    assert len(result) == len(sample_df)

def test_stratify_empty_df():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['problem', 'solution', 'language', 'difficulty', 'topic'])
    result = stratify_tasks(df, target_n=10)
    assert len(result) == 0

def test_stratify_single_stratum():
    """Test stratification with only one stratum."""
    data = [
        {'problem': 'p1', 'solution': 's', 'language': 'Python', 'difficulty': 'Easy', 'topic': 'Math'},
        {'problem': 'p2', 'solution': 's', 'language': 'Python', 'difficulty': 'Easy', 'topic': 'Math'},
    ]
    df = pd.DataFrame(data)
    result = stratify_tasks(df, target_n=1)
    assert len(result) == 1
    assert result.iloc[0]['language'] == 'Python'

def test_stratify_columns_exist(sample_df):
    """Verify that the function uses the correct column names."""
    # Rename columns to custom names
    df_renamed = sample_df.rename(columns={
        'difficulty': 'diff',
        'topic': 'cat',
        'language': 'lang'
    })
    
    result = stratify_tasks(
        df_renamed, 
        difficulty_col='diff', 
        topic_col='cat', 
        language_col='lang', 
        target_n=5
    )
    
    assert len(result) == 5
    # Verify original column names are preserved in result
    assert 'diff' in result.columns
    assert 'cat' in result.columns
    assert 'lang' in result.columns