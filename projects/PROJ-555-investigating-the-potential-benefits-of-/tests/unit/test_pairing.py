import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock the imports if necessary, but here we assume they are available
# We will test the logic of pairing and filtering
from preprocessing import pair_sites_and_filter

def create_test_data():
    # Create a mock timeseries dataframe
    dates = pd.date_range('2020-01-01', periods=12, freq='M')
    data = []
    
    # Site A (Ecotourism, Biome: Forest, Initial NDVI: 0.6)
    for d in dates:
        data.append({'site_id': 'site_A', 'date': d, 'ndvi_value': 0.6, 'pixel_count': 1000, 'valid_pixel_ratio': 0.9})
    
    # Site B (Control, Biome: Forest, Initial NDVI: 0.58) - Good pair
    for d in dates:
        data.append({'site_id': 'site_B', 'date': d, 'ndvi_value': 0.58, 'pixel_count': 1000, 'valid_pixel_ratio': 0.9})
    
    # Site C (Ecotourism, Biome: Desert, Initial NDVI: 0.2)
    for d in dates:
        data.append({'site_id': 'site_C', 'date': d, 'ndvi_value': 0.2, 'pixel_count': 1000, 'valid_pixel_ratio': 0.9})
    
    # Site D (Control, Biome: Desert, Initial NDVI: 0.15) - Good pair (diff ~25%, >10%? wait 0.05/0.2 = 25%)
    # Let's make D closer: 0.18 (diff 0.02/0.2 = 10%)
    for d in dates:
        data.append({'site_id': 'site_D', 'date': d, 'ndvi_value': 0.18, 'pixel_count': 1000, 'valid_pixel_ratio': 0.9})
    
    # Site E (Ecotourism, Biome: Forest, Initial NDVI: 0.1) - No pair
    for d in dates:
        data.append({'site_id': 'site_E', 'date': d, 'ndvi_value': 0.1, 'pixel_count': 1000, 'valid_pixel_ratio': 0.9})
    
    # Site F (Bad data, >50% gaps)
    for d in dates:
        data.append({'site_id': 'site_F', 'date': d, 'ndvi_value': 0.5, 'pixel_count': 100, 'valid_pixel_ratio': 0.3})
    
    ts_df = pd.DataFrame(data)
    
    # Create metadata
    meta_data = [
        {'site_id': 'site_A', 'site_type': 'ecotourism', 'biome': 'Forest'},
        {'site_id': 'site_B', 'site_type': 'control', 'biome': 'Forest'},
        {'site_id': 'site_C', 'site_type': 'ecotourism', 'biome': 'Desert'},
        {'site_id': 'site_D', 'site_type': 'control', 'biome': 'Desert'},
        {'site_id': 'site_E', 'site_type': 'ecotourism', 'biome': 'Forest'},
        {'site_id': 'site_F', 'site_type': 'ecotourism', 'biome': 'Forest'},
    ]
    meta_df = pd.DataFrame(meta_data)
    
    return ts_df, meta_df

def test_pairing_and_filtering():
    ts_df, meta_df = create_test_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        meta_path = os.path.join(tmpdir, 'meta.csv')
        ndvi_path = os.path.join(tmpdir, 'ndvi.parquet')
        
        # Save meta
        meta_df.to_csv(meta_path, index=False)
        
        # Run pairing
        pair_sites_and_filter(ts_df, meta_path, ndvi_path, meta_path.replace('meta', 'pairs'))
        
        # Load results
        pairs = pd.read_csv(meta_path.replace('meta', 'pairs'))
        final_ndvi = pd.read_parquet(ndvi_path)
        
        # Assertions
        assert len(pairs) == 2, f"Expected 2 pairs, got {len(pairs)}"
        assert 'site_F' not in final_ndvi['site_id'].values, "Site F should be excluded due to data gaps"
        assert 'site_E' not in final_ndvi['site_id'].values, "Site E should have no pair"
        
        # Check pair 1 (A-B)
        pair_1 = pairs[pairs['ecotourism_site_id'] == 'site_A']
        assert len(pair_1) == 1
        assert pair_1.iloc[0]['control_site_id'] == 'site_B'
        
        # Check pair 2 (C-D)
        pair_2 = pairs[pairs['ecotourism_site_id'] == 'site_C']
        assert len(pair_2) == 1
        assert pair_2.iloc[0]['control_site_id'] == 'site_D'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
