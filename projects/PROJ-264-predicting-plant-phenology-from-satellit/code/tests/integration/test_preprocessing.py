import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from src.data.preprocessing import run_preprocessing
from src.config import get_config

@pytest.fixture
def full_pipeline_data():
    """
    Creates a dataset that tests the full pipeline:
    - Multicollinear feature (gdd)
    - Single gap (interpolatable)
    - Double gap (excluded)
    - Low coverage site (excluded)
    - Zero obs site (excluded)
    """
    dates = pd.date_range(start='2020-01-01', periods=10, freq='10D')
    
    # Site A: Good data, 1 gap
    # Site B: Bad coverage
    # Site C: Zero obs
    # Site D: Double gap (should be dropped rows)
    
    data = []
    # Site A
    for i, d in enumerate(dates):
        data.append({
            'site_id': 'A', 'date': d, 'temperature': 10.0 + i, 'cloud_free_coverage': 0.9,
            'observation_count': 1, 'gdd_cumulative': 100 + i*10
        })
    # Inject single gap at index 2
    data[2]['temperature'] = np.nan
    
    # Site B: Low coverage
    for i, d in enumerate(dates):
        data.append({
            'site_id': 'B', 'date': d, 'temperature': 15.0 + i, 'cloud_free_coverage': 0.3,
            'observation_count': 1, 'gdd_cumulative': 200 + i*10
        })
    
    # Site C: Zero obs
    for i, d in enumerate(dates):
        data.append({
            'site_id': 'C', 'date': d, 'temperature': 20.0 + i, 'cloud_free_coverage': 0.9,
            'observation_count': 0, 'gdd_cumulative': 300 + i*10
        })
        
    # Site D: Double gap (rows 2 and 3 are NaN)
    for i, d in enumerate(dates):
        val = 25.0 + i
        if i in [2, 3]:
            val = np.nan
        data.append({
            'site_id': 'D', 'date': d, 'temperature': val, 'cloud_free_coverage': 0.9,
            'observation_count': 1, 'gdd_cumulative': 400 + i*10
        })

    return pd.DataFrame(data)

def test_run_preprocessing_full_pipeline(full_pipeline_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        full_pipeline_data.to_csv(input_path, index=False)
        
        results = run_preprocessing(input_path, output_path)
        
        assert results['status'] == 'success'
        assert output_path.exists()
        
        out_df = pd.read_csv(output_path)
        
        # Check exclusions
        assert 'B' not in out_df['site_id'].values # Coverage < 80%
        assert 'C' not in out_df['site_id'].values # Zero obs
        assert 'gdd_cumulative' not in out_df.columns # Multicollinear
        
        # Check interpolation
        # Site A should have no NaN
        site_a = out_df[out_df['site_id'] == 'A']
        assert site_a['temperature'].isna().sum() == 0
        
        # Site D: Rows with double gap should be dropped
        # Original Site D had 10 rows. Double gap at 2,3.
        # If those rows are dropped, we should have 8 rows for D (if D wasn't filtered entirely)
        # But wait, if rows are dropped, does the site stay?
        # The function filter_insufficient_data checks site-level aggregates.
        # If Site D has 8 rows left, it's fine.
        site_d = out_df[out_df['site_id'] == 'D']
        # Original 10 rows, 2 dropped -> 8 rows.
        # Unless the double gap made the site invalid? No, only coverage and obs count.
        assert len(site_d) == 8
        
        # Check stats
        assert results['filtering_stats']['excluded_coverage'] > 0
        assert results['filtering_stats']['excluded_obs'] > 0
        assert results['interpolation_stats']['temperature'] == 0 # Only 1 gap, no exclusion