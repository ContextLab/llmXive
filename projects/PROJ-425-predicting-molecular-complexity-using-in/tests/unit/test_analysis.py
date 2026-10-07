import pytest
import pandas as pd
import numpy as np
from code.analysis import enforce_memory_limit_bootstrap

class TestEnforceMemoryLimit:
    def test_no_subsample_small_data(self):
        """Test that small data is returned unchanged."""
        df = pd.DataFrame({
            'atom_count': [10, 20, 30],
            'val': [1, 2, 3]
        })
        result_df, was_subsampled = enforce_memory_limit_bootstrap(df, memory_limit_gb=0.001) # Force check but data is tiny
        # Note: memory_usage is in bytes. 0.001GB is huge. This should not subsample.
        # Let's test with a very low limit to force the check, but our data is tiny so it won't trigger > limit unless limit is tiny.
        # Actually, let's just check the logic: if mem <= limit, no subsample.
        # We'll mock the limit to be smaller than the actual usage to trigger the logic, but since we can't easily mock memory_usage,
        # we rely on the fact that 3 rows is tiny.
        
        # Better approach: Test with a limit that is definitely smaller than 3 rows (impossible) or larger.
        # Let's just verify the function runs and returns (df, False) for tiny data with a normal limit.
        result_df, was_subsampled = enforce_memory_limit_bootstrap(df, memory_limit_gb=4.0)
        assert was_subsampled == False
        assert len(result_df) == 3

    def test_subsample_large_data(self):
        """Test that large data is subsampled to 5000 rows."""
        # Create a large synthetic dataframe
        n_rows = 100000
        df = pd.DataFrame({
            'atom_count': np.random.randint(10, 100, size=n_rows),
            'val': np.random.rand(n_rows)
        })
        
        # Force subsampling by setting a very low limit (e.g., 0.0001 GB which is ~100KB)
        # A 100k row dataframe is definitely larger than 100KB.
        result_df, was_subsampled = enforce_memory_limit_bootstrap(df, memory_limit_gb=0.0001)
        
        assert was_subsampled == True
        assert len(result_df) == 5000
        
        # Verify stratification preserved distribution roughly (optional but good)
        # We check that the result has the same columns
        assert 'atom_count' in result_df.columns
        assert 'val' in result_df.columns