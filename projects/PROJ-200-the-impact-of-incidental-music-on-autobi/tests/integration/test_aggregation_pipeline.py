"""
Integration test for the full aggregation pipeline:
1. Create synthetic matched cues
2. Create synthetic exposure data
3. Join them (join_exposure_data)
4. Aggregate to User-Track pairs (aggregate_to_user_track)

This verifies the end-to-end flow required for User Story 2.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from aggregation import join_exposure_data, aggregate_to_user_track

@pytest.fixture
def synthetic_cues():
    """Generate synthetic matched cues data."""
    data = {
        'user_id': ['U1', 'U1', 'U1', 'U2', 'U2'],
        'track_id': ['T1', 'T1', 'T2', 'T1', 'T2'],
        'vividness': [5.0, 4.0, 3.0, 5.0, 4.0],
        'valence': [1.0, 2.0, 3.0, 1.0, 2.0],
        'cue_text': ['Song A', 'Song A', 'Song B', 'Song A', 'Song B']
    }
    return pd.DataFrame(data)

@pytest.fixture
def synthetic_exposure():
    """Generate synthetic exposure data."""
    data = {
        'track_id': ['T1', 'T2', 'T3'],
        'adolescent_exposure_score': [0.8, 0.2, 0.5],
        'residualized_exposure_score': [0.1, -0.1, 0.0],
        'overall_popularity_score': [100, 50, 75]
    }
    return pd.DataFrame(data)

def test_full_aggregation_pipeline(synthetic_cues, synthetic_exposure):
    """Test the full pipeline from raw inputs to aggregated output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cues_path = os.path.join(tmpdir, 'cues.parquet')
        exposure_path = os.path.join(tmpdir, 'exposure.parquet')
        joined_path = os.path.join(tmpdir, 'joined.parquet')
        aggregated_path = os.path.join(tmpdir, 'aggregated.parquet')
        
        # Write inputs
        synthetic_cues.to_parquet(cues_path)
        synthetic_exposure.to_parquet(exposure_path)
        
        # Step 1: Join
        joined_df = join_exposure_data(cues_path, exposure_path, joined_path)
        
        # Verify join results
        assert len(joined_df) == 5  # T3 has no cues, so inner join excludes it
        assert 'mean_vividness' not in joined_df.columns  # Not aggregated yet
        
        # Step 2: Aggregate
        aggregated_df = aggregate_to_user_track(joined_path, aggregated_path)
        
        # Verify aggregation results
        assert len(aggregated_df) == 4  # U1-T1, U1-T2, U2-T1, U2-T2
        assert 'mean_vividness' in aggregated_df.columns
        assert 'cue_count' in aggregated_df.columns
        
        # Verify specific values
        # U1-T1: 2 cues, vividness 5,4 -> mean 4.5
        u1_t1 = aggregated_df[(aggregated_df['user_id'] == 'U1') & (aggregated_df['track_id'] == 'T1')]
        assert len(u1_t1) == 1
        assert u1_t1['mean_vividness'].values[0] == 4.5
        assert u1_t1['cue_count'].values[0] == 2
        
        # Verify file was written to disk
        assert os.path.exists(aggregated_path)
