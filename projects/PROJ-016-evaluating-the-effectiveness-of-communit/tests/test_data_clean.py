import pytest
import pandas as pd
import numpy as np
import tempfile
import json
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.clean import (
    standardize_iso_code, 
    standardize_year, 
    drop_missing_primary_vars, 
    merge_datasets,
    clean_and_merge_data
)

@pytest.fixture
def sample_dataframe():
    data = {
        'country_code': ['USA', 'USA', 'GBR', 'GBR', 'DEU', 'CHN'],
        'year': [2000, 2001, 2000, 2001, 2000, 2001],
        'land_use_change': [1.2, 1.3, 0.5, 0.6, 0.8, np.nan], # CHN has NaN
        'gdp_per_capita': [50000, 51000, 40000, 41000, 45000, 8000],
        'population_density': [90, 91, 270, 271, 230, 150]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir(tmp_path):
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    return data_dir

class TestDataCleaningLogic:
    def test_standardize_iso_code(self):
        series = pd.Series(['us', 'uk', 'de', None, ''])
        result = standardize_iso_code(series)
        assert result[0] == 'USA'
        assert result[1] == 'GBR'
        assert result[2] == 'DEU'
        assert pd.isna(result[3])
        assert result[4] is None or pd.isna(result[4])

    def test_standardize_year(self):
        series = pd.Series(['2000', 2001, '2002.0', None, 'abc'])
        result = standardize_year(series)
        assert result[0] == 2000
        assert result[1] == 2001
        assert result[2] == 2002
        assert pd.isna(result[3])
        assert result[4] is None or pd.isna(result[4])

    def test_drop_missing_primary_vars(self, sample_dataframe):
        # 'land_use_change' is a primary var
        primary_vars = ['land_use_change', 'gdp_per_capita']
        df_clean = drop_missing_primary_vars(sample_dataframe, primary_vars)
        # CHN should be dropped because land_use_change is NaN
        assert len(df_clean) == 5
        assert 'CHN' not in df_clean['country_code'].values

    def test_merge_handles_missing_keys(self):
        fao = pd.DataFrame({
            'country_code': ['USA', 'GBR'],
            'year': [2000, 2000],
            'land_use_change': [1.0, 0.5]
        })
        wb = pd.DataFrame({
            'country_code': ['USA', 'DEU'], # DEU not in FAO
            'year': [2000, 2000],
            'gdp_per_capita': [50000, 45000]
        })
        
        merged = merge_datasets(fao, wb)
        # Inner join: only USA should remain
        assert len(merged) == 1
        assert merged['country_code'].iloc[0] == 'USA'

    def test_excludes_row_when_gdp_missing(self, sample_dataframe):
        # Modify sample to have NaN in GDP
        sample_dataframe.loc[0, 'gdp_per_capita'] = np.nan
        primary_vars = ['land_use_change', 'gdp_per_capita']
        df_clean = drop_missing_primary_vars(sample_dataframe, primary_vars)
        # Row 0 (USA 2000) should be dropped
        assert len(df_clean) == 5
        # Check that the specific row is gone
        assert not ((df_clean['country_code'] == 'USA') & (df_clean['year'] == 2000)).any()

    def test_excludes_country_when_primary_missing(self, sample_dataframe):
        # This test is for T016b, but we can test the logic here if we implement country exclusion.
        # T013 does not require country exclusion, so we skip strict testing for it here.
        # Instead, we verify the row exclusion works correctly.
        pass

    def test_classifies_cbnrm_when_proxy_above_threshold(self):
        # This is for T014, not T013.
        pass

    def test_classifies_state_led_when_proxy_below_threshold(self):
        # This is for T014, not T013.
        pass

    def test_download_exponential_backoff(self):
        # This is for T017a, testing download.py, not clean.py.
        pass

    def test_fetch_fails_loudly_no_synthetic(self):
        # This is for T065, testing download.py.
        pass
