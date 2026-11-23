import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock
from derive_demographics import (
    get_country_code_from_coords,
    fetch_world_bank_indicator,
    merge_demographics_to_data,
    log_gap,
    ensure_directories
)

def test_get_country_code_from_coords_invalid():
    # Test with NaN values
    assert get_country_code_from_coords(np.nan, 10.0, MagicMock()) is None
    assert get_country_code_from_coords(10.0, np.nan, MagicMock()) is None

def test_merge_demographics_to_data_no_demo():
    moral_df = pd.DataFrame({'country': ['US', 'UK'], 'value': [1, 2]})
    demo_df = pd.DataFrame()
    result = merge_demographics_to_data(moral_df, demo_df)
    assert 'population_age_sex_pct' in result.columns
    assert result['population_age_sex_pct'].isna().all()

def test_merge_demographics_to_data_with_demo():
    moral_df = pd.DataFrame({'country': ['US', 'UK'], 'value': [1, 2]})
    demo_df = pd.DataFrame({
        'country_code': ['US', 'UK'],
        'population_age_sex_pct': [50.0, 60.0],
        'life_expectancy': [78.0, 80.0]
    })
    result = merge_demographics_to_data(moral_df, demo_df)
    assert result['population_age_sex_pct'].tolist() == [50.0, 60.0]
    assert result['life_expectancy'].tolist() == [78.0, 80.0]

def test_log_gap(tmp_path):
    log_path = tmp_path / "log.json"
    log_gap(['US', 'UK'], log_path)
    assert log_path.exists()
    import json
    with open(log_path) as f:
        data = json.load(f)
    assert data['status'] == 'partial_missing'
    assert 'US' in data['missing_countries']

def test_ensure_directories(tmp_path):
    # Mock base path
    with patch('derive_demographics.Path', return_value=tmp_path):
        ensure_directories(tmp_path)
    assert (tmp_path / "data" / "processed").exists()
    assert (tmp_path / "results" / "logs").exists()