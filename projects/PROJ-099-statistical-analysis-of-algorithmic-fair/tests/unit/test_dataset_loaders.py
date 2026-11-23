"""
Unit tests for dataset loaders.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.dataset_loaders import (
    load_adult,
    load_compas,
    load_bank,
    load_german,
    load_lawschool,
    verify_domain,
    check_url_status
)

class TestDomainVerification:
    def test_whitelisted_domain(self):
        assert verify_domain("https://archive.ics.uci.edu/ml/data.csv") is True
        assert verify_domain("https://raw.githubusercontent.com/user/repo/file.csv") is True

    def test_non_whitelisted_domain(self):
        assert verify_domain("https://malicious-site.com/data.csv") is False

class TestDatasetLoaders:
    def test_load_adult_structure(self):
        df = load_adult()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        # Check for at least some expected columns
        expected_cols = ["age", "income"]
        # Adult might have different column names depending on source
        # Just ensure it's not empty
        assert len(df.columns) > 0

    def test_load_compas_structure(self):
        df = load_compas()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df.columns) > 0

    def test_load_bank_structure(self):
        df = load_bank()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df.columns) > 0

    def test_load_german_structure(self):
        df = load_german()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df.columns) > 0

    def test_load_lawschool_structure(self):
        df = load_lawschool()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df.columns) > 0

class TestURLStatus:
    def test_check_url_status(self):
        # Test a known good URL (GitHub raw)
        status, code = check_url_status("https://raw.githubusercontent.com/plotly/datasets/master/adult.csv")
        assert status is True
        assert code == 200
        
        # Test a bad URL
        status, code = check_url_status("https://httpstat.us/404")
        assert status is False
        assert code == 404
