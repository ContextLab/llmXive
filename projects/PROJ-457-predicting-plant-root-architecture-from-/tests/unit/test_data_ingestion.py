import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import logging
from pathlib import Path

# Mock the config module if necessary, or assume it's available in test env
# For this test, we'll mock the config loading
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import filter_by_missing_nutrients


@pytest.fixture
def sample_df_with_nans():
    data = {
        "species": ["A", "B", "C", "D", "E"],
        "root_length": [10, 20, 30, 40, 50],
        "phosphorus": [1.0, None, 3.0, None, 5.0],
        "nitrogen": [2.0, 4.0, None, 6.0, 8.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_df_complete():
    data = {
        "species": ["A", "B", "C"],
        "root_length": [10, 20, 30],
        "phosphorus": [1.0, 2.0, 3.0],
        "nitrogen": [4.0, 5.0, 6.0],
    }
    return pd.DataFrame(data)


def test_filter_by_missing_nutrients_with_nans(sample_df_with_nans, caplog):
    """
    Test that rows with missing phosphorus or nitrogen are excluded.
    """
    caplog.set_level(logging.INFO)
    df = sample_df_with_nans.copy()

    filtered_df, excluded_count = filter_by_missing_nutrients(
        df, p_n_available=True, logger=caplog
    )

    # Expected: Only rows A and E have both P and N
    assert len(filtered_df) == 2
    assert excluded_count == 3
    assert list(filtered_df["species"]) == ["A", "E"]


def test_filter_by_missing_nutrients_no_nans(sample_df_complete, caplog):
    """
    Test that no rows are excluded when data is complete.
    """
    caplog.set_level(logging.INFO)
    df = sample_df_complete.copy()

    filtered_df, excluded_count = filter_by_missing_nutrients(
        df, p_n_available=True, logger=caplog
    )

    assert len(filtered_df) == 3
    assert excluded_count == 0


def test_filter_by_missing_nutrients_pn_not_available(sample_df_with_nans, caplog):
    """
    Test that no filtering occurs when p_n_available is False.
    """
    caplog.set_level(logging.INFO)
    df = sample_df_with_nans.copy()

    filtered_df, excluded_count = filter_by_missing_nutrients(
        df, p_n_available=False, logger=caplog
    )

    assert len(filtered_df) == 5
    assert excluded_count == 0
    assert "Skipping missing nutrient filter" in caplog.text


def test_filter_by_missing_nutrients_empty_df(caplog):
    """
    Test behavior with empty dataframe.
    """
    caplog.set_level(logging.INFO)
    df = pd.DataFrame(columns=["species", "phosphorus", "nitrogen"])

    filtered_df, excluded_count = filter_by_missing_nutrients(
        df, p_n_available=True, logger=caplog
    )

    assert len(filtered_df) == 0
    assert excluded_count == 0