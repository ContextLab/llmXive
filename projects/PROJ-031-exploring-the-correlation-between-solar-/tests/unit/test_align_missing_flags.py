import pytest
import pandas as pd
import os
import tempfile
from datetime import datetime, timedelta
from code.align import match_solar_events, align_events, find_dst_minima

@pytest.fixture
def sample_storms():
    return pd.DataFrame({
        'storm_id': [1, 2],
        'timestamp': [datetime(2023, 1, 10), datetime(2023, 6, 15)],
        'dst_min_value': [-80.0, -120.0]
    })

@pytest.fixture
def sample_flares():
    return pd.DataFrame({
        'peak_time': [datetime(2023, 1, 9), datetime(2023, 6, 10)],
        'flux_class': ['M1.0', 'X2.0'],
        'peak_flux': [1.0e-5, 1.0e-4]
    })

@pytest.fixture
def sample_cmes():
    return pd.DataFrame({
        'date': [datetime(2023, 1, 8)],
        'speed': [800.0],
        'width': [120.0],
        'halo': [1]
    })

def test_match_solar_events_missing_flare(sample_storms, sample_cmes):
    """
    Test that missing flares are flagged as null (NaN) and not excluded.
    Storm 2 (June) has no matching flare in the dataset.
    """
    # No flares provided
    empty_flare_df = pd.DataFrame(columns=['peak_time', 'flux_class', 'peak_flux'])
    
    result = match_solar_events(sample_storms, empty_flare_df, sample_cmes)
    
    # Check that result has 2 rows (no exclusion)
    assert len(result) == 2
    
    # Storm 1 should have CME, no flare
    assert result.iloc[0]['has_flare'] == 0
    assert pd.isna(result.iloc[0]['flare_peak_time'])
    assert pd.isna(result.iloc[0]['flare_flux_class'])
    assert pd.isna(result.iloc[0]['flare_peak_flux'])
    
    # Storm 2 should have no flare, no CME (since CME is only Jan)
    assert result.iloc[1]['has_flare'] == 0
    assert result.iloc[1]['has_cme'] == 0
    assert result.iloc[1]['no_match_found'] == 1

def test_match_solar_events_missing_cme(sample_storms, sample_flares):
    """
    Test that missing CMEs are flagged as null (NaN) and not excluded.
    Storm 2 (June) has no matching CME.
    """
    empty_cme_df = pd.DataFrame(columns=['date', 'speed', 'width', 'halo'])
    
    result = match_solar_events(sample_storms, sample_flares, empty_cme_df)
    
    assert len(result) == 2
    
    # Storm 1 has flare, no CME
    assert result.iloc[0]['has_cme'] == 0
    assert pd.isna(result.iloc[0]['cme_speed'])
    assert result.iloc[0]['no_match_found'] == 0 # Has flare, so not "no match"
    
    # Storm 2 has flare, no CME
    assert result.iloc[1]['has_cme'] == 0
    assert pd.isna(result.iloc[1]['cme_speed'])

def test_no_match_found_flag(sample_storms):
    """
    Test that 'no_match_found' is 1 when both flare and CME are missing.
    """
    empty_flare = pd.DataFrame(columns=['peak_time', 'flux_class', 'peak_flux'])
    empty_cme = pd.DataFrame(columns=['date', 'speed', 'width', 'halo'])
    
    result = match_solar_events(sample_storms, empty_flare, empty_cme)
    
    assert len(result) == 2
    assert all(result['no_match_found'] == 1)
    assert all(result['has_flare'] == 0)
    assert all(result['has_cme'] == 0)

def test_align_events_writes_file(sample_storms, sample_flares, sample_cmes):
    """
    Test the full alignment pipeline writes a CSV with correct columns.
    """
    # Create temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        dst_file = os.path.join(tmpdir, "dst.csv")
        flare_file = os.path.join(tmpdir, "flares.csv")
        cme_file = os.path.join(tmpdir, "cmes.csv")
        out_file = os.path.join(tmpdir, "aligned.csv")
        
        # Write inputs
        sample_storms[['timestamp', 'dst_min_value']].to_csv(dst_file, index=False)
        sample_flares.to_csv(flare_file, index=False)
        sample_cmes.to_csv(cme_file, index=False)
        
        # Run alignment
        df = align_events(
            dst_filepath=dst_file,
            flare_filepath=flare_file,
            cme_filepath=cme_file,
            output_filepath=out_file
        )
        
        # Verify file exists
        assert os.path.exists(out_file)
        
        # Verify columns
        expected_cols = [
            'storm_id', 'storm_time', 'dst_min_value',
            'flare_peak_time', 'flare_flux_class', 'flare_peak_flux',
            'cme_date', 'cme_speed', 'cme_width', 'cme_halo',
            'has_flare', 'has_cme', 'no_match_found'
        ]
        assert list(df.columns) == expected_cols
        
        # Verify row count (no exclusion)
        assert len(df) == len(sample_storms)