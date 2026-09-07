import pytest
import pandas as pd
from analysis.sensitivity import stratify_by_stars

def test_stratify_by_stars():
    """Test stratification by star count."""
    data = pd.DataFrame({
        'pr_id': range(10),
        'stars': [100, 500, 1000, 5000, 10000, 20000, 50, 200, 300, 400],
        'review_time': range(10)
    })
    
    strata = stratify_by_stars(data, star_col='stars')
    
    assert len(strata) == 4  # 4 quartiles
    assert all(len(v) > 0 for v in strata.values())

def test_stratify_by_stars_empty():
    """Test stratification with empty dataframe."""
    data = pd.DataFrame(columns=['pr_id', 'stars', 'review_time'])
    
    strata = stratify_by_stars(data, star_col='stars')
    
    assert len(strata) == 4
    assert all(len(v) == 0 for v in strata.values())