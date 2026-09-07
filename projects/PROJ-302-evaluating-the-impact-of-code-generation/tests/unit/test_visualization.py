import pytest
import pandas as pd
import numpy as np
from analysis.visualization import generate_box_plot, generate_cdf_plot

def test_generate_box_plot():
    """Test box plot generation."""
    data = {
        'group': ['human'] * 50 + ['llm'] * 50,
        'value': np.concatenate([
            np.random.normal(10, 2, 50),
            np.random.normal(8, 2, 50)
        ])
    }
    df = pd.DataFrame(data)
    
    # Should not raise
    fig = generate_box_plot(df, x_col='group', y_col='value')
    assert fig is not None

def test_generate_cdf_plot():
    """Test CDF plot generation."""
    data = {
        'group': ['human'] * 50 + ['llm'] * 50,
        'value': np.concatenate([
            np.random.normal(10, 2, 50),
            np.random.normal(8, 2, 50)
        ])
    }
    df = pd.DataFrame(data)
    
    # Should not raise
    fig = generate_cdf_plot(df, x_col='group', y_col='value')
    assert fig is not None