import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

# Import the function to test
# Assuming the module is code/cluster_analysis.py
import sys
sys.path.insert(0, 'code')
from cluster_analysis import flag_high_variance_regions, calculate_cluster_correlations

class TestHighVarianceFlagging:
    """
    Contract test for T034: Flag regions where prediction variance exceeds threshold.
    """

    def test_flag_high_variance_cluster(self):
        """
        Verify that a cluster with high variance is correctly flagged.
        """
        # Create synthetic data (for testing logic only, not real data ingestion)
        # Cluster 0: Low variance
        # Cluster 1: High variance
        data = {
            'bulk_modulus': [100, 102, 98, 200, 500, 100], 
            'shear_modulus': [50, 52, 48, 300, 700, 100],
            'cluster_id': [0, 0, 0, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        
        # Threshold between low (var ~ 4) and high (var ~ 30000)
        threshold = 1000.0
        
        result = flag_high_variance_regions(df, threshold)
        
        # Cluster 0 should NOT be flagged
        assert not result[result['cluster_id'] == 0]['high_variance_flag'].any()
        
        # Cluster 1 SHOULD be flagged
        assert result[result['cluster_id'] == 1]['high_variance_flag'].all()

    def test_no_high_variance_clusters(self):
        """
        Verify that no clusters are flagged if all variances are below threshold.
        """
        data = {
            'bulk_modulus': [100, 101, 102, 200, 201, 202],
            'shear_modulus': [50, 51, 52, 100, 101, 102],
            'cluster_id': [0, 0, 0, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        
        # High threshold
        threshold = 10000.0
        
        result = flag_high_variance_regions(df, threshold)
        
        # No flags expected
        assert not result['high_variance_flag'].any()

    def test_missing_cluster_id(self):
        """
        Verify that the function raises an error if cluster_id is missing.
        """
        data = {
            'bulk_modulus': [100, 101, 102],
            'shear_modulus': [50, 51, 52],
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="DataFrame must contain 'cluster_id' column"):
            flag_high_variance_regions(df, 100.0)

    def test_various_targets(self):
        """
        Verify that the function checks multiple target columns.
        """
        # Cluster 0: Low Bulk Var, Low Shear Var
        # Cluster 1: Low Bulk Var, HIGH Shear Var
        data = {
            'bulk_modulus': [100, 101, 102, 200, 201, 202],
            'shear_modulus': [50, 51, 52, 300, 700, 100], 
            'cluster_id': [0, 0, 0, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        
        # Threshold is higher than Bulk variance but lower than Shear variance of Cluster 1
        threshold = 1000.0 
        
        result = flag_high_variance_regions(df, threshold)
        
        # Cluster 1 has high shear variance, so it should be flagged
        assert result[result['cluster_id'] == 1]['high_variance_flag'].all()
        # Cluster 0 has low variance for both, should not be flagged
        assert not result[result['cluster_id'] == 0]['high_variance_flag'].any()
