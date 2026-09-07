import pytest
import pandas as pd
from feature_extraction.complexity import calculate_snippet_complexity, process_dataset

def test_calculate_snippet_complexity_simple():
    """Test complexity calculation for simple code."""
    code = "def hello():\n    print('Hello')\n"
    metrics = calculate_snippet_complexity(code)
    
    assert metrics['lines_of_code'] == 2
    assert metrics['cyclomatic_complexity'] >= 1  # At least 1 for the function

def test_calculate_snippet_complexity_branches():
    """Test complexity calculation with branches."""
    code = """
    def check(x):
        if x > 0:
            return True
        else:
            return False
    """
    metrics = calculate_snippet_complexity(code)
    
    assert metrics['lines_of_code'] == 5
    assert metrics['cyclomatic_complexity'] >= 2  # if + else

def test_process_dataset_empty():
    """Test process_dataset with empty dataframe."""
    df = pd.DataFrame(columns=['snippet_id', 'code'])
    result = process_dataset(df)
    
    assert len(result) == 0

def test_process_dataset_single_row():
    """Test process_dataset with single row."""
    df = pd.DataFrame([
        {'snippet_id': '1', 'code': 'def x(): pass'}
    ])
    
    result = process_dataset(df)
    
    assert len(result) == 1
    assert 'complexity_metrics' in result.columns