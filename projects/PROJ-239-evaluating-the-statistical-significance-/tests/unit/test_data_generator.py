import pytest
import pandas as pd
import numpy as np
from code.data_generator import generate_data
from code.config import set_seed

def test_generate_data_h0_true():
    """
    Test that generated data under H0 (no treatment effect) has equal means
    between treatment groups and preserves cluster IDs.
    """
    n_clusters = 100
    n_obs_per_cluster = 10
    icc = 0.1
    seed = 42
    
    set_seed(seed)
    df = generate_data(
        n_clusters=n_clusters,
        n_obs_per_cluster=n_obs_per_cluster,
        icc=icc,
        seed=seed
    )
    
    # Verify cluster IDs are preserved and not null
    assert 'cluster_id' in df.columns
    assert df['cluster_id'].notna().all()
    assert len(df['cluster_id'].unique()) == n_clusters
    
    # Verify treatment groups have equal means (within tolerance) under H0
    # H0 is true by construction in generate_data (no treatment effect added)
    group_0 = df[df['treatment'] == 0]['outcome']
    group_1 = df[df['treatment'] == 1]['outcome']
    
    mean_diff = abs(group_0.mean() - group_1.mean())
    # Allow some tolerance due to random sampling
    # With 100 clusters and 10 obs each, standard error is small
    # but we allow a reasonable tolerance for random variation
    assert mean_diff < 0.5, f"Mean difference {mean_diff} is too large for H0"
    
    # Additional check: verify treatment assignment is at cluster level
    # Each cluster should be entirely in one treatment group
    cluster_treatment_mapping = df.groupby('cluster_id')['treatment'].nunique()
    assert (cluster_treatment_mapping == 1).all(), \
        "Treatment assignment is not at cluster level"
