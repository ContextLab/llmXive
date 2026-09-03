import pytest
import pandas as pd
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.derive_demographics import (
    fetch_world_bank_indicator,
    fetch_demographic_data,
    log_gap,
    merge_demographics_to_data,
    main,
    COVARIATE_STATUS_LOG,
    COVARIATES_OUTPUT
)


@patch('code.derive_demographics.requests.get')
def test_fetch_world_bank_indicator_success(mock_get):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {},
        [
            {"countryiso3code": "USA", "value": 330.0, "date": "2020"},
            {"countryiso3code": "USA", "value": 320.0, "date": "2019"},
            {"countryiso3code": "GBR", "value": 67.0, "date": "2020"}
        ]
    ]
    mock_get.return_value = mock_response

    logger = MagicMock()
    result = fetch_world_bank_indicator("SP.POP.TOTL", logger)

    assert result is not None
    assert "USA" in result
    assert result["USA"]["value"] == 330.0 # Latest date
    assert "GBR" in result
    logger.error.assert_not_called()


@patch('code.derive_demographics.requests.get')
def test_fetch_world_bank_indicator_failure(mock_get):
    mock_get.side_effect = Exception("Network Error")
    logger = MagicMock()
    result = fetch_world_bank_indicator("SP.POP.TOTL", logger)
    assert result is None
    logger.error.assert_called()


def test_merge_demographics_to_data():
    mm_df = pd.DataFrame({
        "participant_id": [1, 2, 3],
        "country": ["USA", "GBR", "FRA"],
        "response_time": [100, 200, 300]
    })
    
    cov_df = pd.DataFrame({
        "country_code": ["USA", "GBR"],
        "population": [330, 67],
        "urban_pct": [82, 83]
    })

    logger = MagicMock()
    merged = merge_demographics_to_data(mm_df, cov_df, logger)

    assert len(merged) == 3
    assert merged.loc[0, "population"] == 330
    assert merged.loc[1, "population"] == 67
    assert pd.isna(merged.loc[2, "population"]) # FRA missing
    assert "population" in merged.columns


def test_log_gap_creates_file(tmp_path):
    # Override global paths for test
    import code.derive_demographics as mod
    original_log_path = mod.COVARIATE_STATUS_LOG
    mod.COVARIATE_STATUS_LOG = tmp_path / "covariate_status.json"

    mm_countries = {"USA", "GBR", "FRA"}
    cov_countries = {"USA", "GBR"}

    log_gap(mm_countries, cov_countries, MagicMock())

    assert mod.COVARIATE_STATUS_LOG.exists()
    with open(mod.COVARIATE_STATUS_LOG) as f:
        data = json.load(f)
    
    assert "FRA" in data["missing_countries"]
    assert data["status"] == "partial_match"

    # Restore
    mod.COVARIATE_STATUS_LOG = original_log_path