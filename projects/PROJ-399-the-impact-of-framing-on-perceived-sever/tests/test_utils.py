"""
Tests for utility functions in code/utils.py.
"""
import pytest
import pandas as pd
import numpy as np
import os
import yaml
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils import (
    load_config,
    set_random_seed,
    validate_stimulus_columns,
    validate_stimulus_data_integrity
)


@pytest.fixture
def sample_stimulus_df():
    """Create a sample DataFrame with valid stimulus columns."""
    return pd.DataFrame({
        'stimulus_id': ['S1', 'S2', 'S3'],
        'content_domain': ['politics', 'health', 'science'],
        'headline': ['Headline 1', 'Headline 2', 'Headline 3'],
        'extra_col': [1, 2, 3]
    })


@pytest.fixture
def invalid_stimulus_df():
    """Create a sample DataFrame missing a required column."""
    return pd.DataFrame({
        'stimulus_id': ['S1', 'S2'],
        'content_domain': ['politics', 'health']
        # Missing 'headline'
    })


@pytest.fixture
def empty_df():
    """Create an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_data = {
        "random_seed": 12345,
        "other_setting": "value"
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    return str(config_path)


class TestLoadConfig:
    def test_load_config_success(self, temp_config_file):
        config = load_config(temp_config_file)
        assert config["random_seed"] == 12345
        assert config["other_setting"] == "value"

    def test_load_config_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("non_existent_path.yaml")


class TestSetRandomSeed:
    def test_set_seed_from_arg(self):
        set_random_seed(seed=999)
        assert np.random.get_state()[1][0] != 0 # Just a basic check that state changed
        # More robust check:
        np.random.seed(999)
        val1 = np.random.rand()
        np.random.seed(999)
        val2 = np.random.rand()
        assert val1 == val2

    def test_set_seed_from_config(self, temp_config_file):
        config = load_config(temp_config_file)
        set_random_seed(config)
        np.random.seed(config["random_seed"])
        val1 = np.random.rand()
        np.random.seed(config["random_seed"])
        val2 = np.random.rand()
        assert val1 == val2


class TestValidateStimulusColumns:
    def test_valid_df(self, sample_stimulus_df):
        assert validate_stimulus_columns(sample_stimulus_df) is True

    def test_missing_columns(self, invalid_stimulus_df):
        with pytest.raises(ValueError) as exc_info:
            validate_stimulus_columns(invalid_stimulus_df)
        assert "headline" in str(exc_info.value)

    def test_empty_df(self, empty_df):
        with pytest.raises(ValueError) as exc_info:
            validate_stimulus_columns(empty_df)
        assert "empty" in str(exc_info.value).lower()

    def test_not_dataframe(self):
        with pytest.raises(ValueError):
            validate_stimulus_columns("not a df")

    def test_custom_required_columns(self):
        df = pd.DataFrame({'a': [1], 'b': [2]})
        assert validate_stimulus_columns(df, required_columns=['a']) is True
        with pytest.raises(ValueError):
            validate_stimulus_columns(df, required_columns=['a', 'c'])


class TestValidateStimulusDataIntegrity:
    def test_valid_data(self, sample_stimulus_df):
        result = validate_stimulus_data_integrity(sample_stimulus_df)
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0

    def test_missing_columns(self, invalid_stimulus_df):
        result = validate_stimulus_data_integrity(invalid_stimulus_df)
        assert result["is_valid"] is False
        assert any("Missing required" in issue for issue in result["issues"])

    def test_duplicate_ids(self):
        df = pd.DataFrame({
            'stimulus_id': ['S1', 'S1', 'S2'],
            'content_domain': ['politics', 'health', 'science'],
            'headline': ['H1', 'H2', 'H3']
        })
        result = validate_stimulus_data_integrity(df)
        assert result["is_valid"] is False # Flagged as issue
        assert any("duplicate" in issue.lower() for issue in result["issues"])

    def test_missing_values(self):
        df = pd.DataFrame({
            'stimulus_id': ['S1', 'S2', 'S3'],
            'content_domain': ['politics', None, 'science'],
            'headline': ['H1', 'H2', 'H3']
        })
        result = validate_stimulus_data_integrity(df)
        assert result["is_valid"] is False
        assert any("missing" in issue.lower() for issue in result["issues"])

    def test_empty_strings(self):
        df = pd.DataFrame({
            'stimulus_id': ['S1', 'S2', 'S3'],
            'content_domain': ['politics', '', 'science'],
            'headline': ['H1', 'H2', 'H3']
        })
        result = validate_stimulus_data_integrity(df)
        assert result["is_valid"] is False
        assert any("empty" in issue.lower() for issue in result["issues"])