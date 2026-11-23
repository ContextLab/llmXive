import pytest
import pandas as pd
import numpy as np
from code.analysis.meta_analysis import perform_subgroup_analysis, run_random_effects_meta_analysis

def test_perform_subgroup_analysis_communication_vs_peer():
    """
    Test subgroup analysis logic with synthetic but realistic effect sizes.
    Groups studies by 'social_skill_domain' (communication vs peer interaction).
    """
    # Create a mock dataframe
    data = {
        'study_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
        'social_skill_domain': ['communication', 'communication', 'communication', 
                                'peer interaction', 'peer interaction', 'peer interaction'],
        'hedges_g': [0.8, 0.9, 0.7, 0.4, 0.5, 0.3],
        'se': [0.15, 0.16, 0.14, 0.12, 0.13, 0.11]
    }
    df = pd.DataFrame(data)
    
    result = perform_subgroup_analysis(df, 'social_skill_domain')
    
    # Verify overall stats exist
    assert result.overall_stats is not None
    assert result.overall_stats.n_studies == 6 # Note: n_studies is not in overall_stats, checking existence
    
    # Verify subgroup results count
    assert len(result.subgroup_stats) == 2
    
    # Check specific group stats
    comm_stats = next((s for s in result.subgroup_stats if s.domain == 'communication'), None)
    peer_stats = next((s for s in result.subgroup_stats if s.domain == 'peer interaction'), None)
    
    assert comm_stats is not None
    assert peer_stats is not None
    
    assert comm_stats.n_studies == 3
    assert peer_stats.n_studies == 3
    
    # Communication group should have higher effect size than peer interaction
    assert comm_stats.pooled_effect > peer_stats.pooled_effect
    
    # Verify between-group test
    assert result.between_q >= 0
    assert result.between_df == 1 # 2 groups - 1
    assert 0 <= result.between_p_value <= 1

def test_run_random_effects_meta_analysis_single_study():
    """Test that the function handles a single study gracefully."""
    g = [0.5]
    se = [0.1]
    
    stats = run_random_effects_meta_analysis(g, se)
    
    assert stats.pooled_effect == 0.5
    assert stats.pooled_se == 0.1
    assert stats.df == 0
    assert stats.i_squared == 0.0

def test_run_random_effects_meta_analysis_empty():
    """Test that the function raises error on empty input."""
    with pytest.raises(ValueError):
        run_random_effects_meta_analysis([], [])
