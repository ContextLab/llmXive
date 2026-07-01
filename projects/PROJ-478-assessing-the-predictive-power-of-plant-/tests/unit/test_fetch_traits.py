"""
Unit tests for TRY data fetching and source verification.

Tests verify that:
1. Data is fetched from the correct source (Handbook 2013)
2. Source metadata is correctly parsed and verified
3. Non-Handbook 2013 sources are flagged as 'unverified protocol'
4. The fetch function returns the expected structure
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.fetch_traits import fetch_traits_from_try, verify_trait_source


class TestFetchTraitsFromTRY:
    """Tests for the fetch_traits_from_try function."""

    def test_fetch_returns_dataframe_structure(self):
        """Verify that fetch_traits_from_try returns a DataFrame with expected columns."""
        # Mock the requests.get response
        mock_data = {
            "results": [
                {
                    "species": "Helianthus annuus",
                    "trait": "SLA",
                    "value": 15.5,
                    "unit": "mm2/mg",
                    "source": "Handbook 2013"
                },
                {
                    "species": "Helianthus annuus",
                    "trait": "seed_mass",
                    "value": 0.02,
                    "unit": "g",
                    "source": "Handbook 2013"
                }
            ]
        }
        
        with patch('src.data.fetch_traits.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            df = fetch_traits_from_try(["Helianthus annuus"])
            
            assert isinstance(df, pd.DataFrame)
            assert "species" in df.columns
            assert "trait" in df.columns
            assert "value" in df.columns
            assert "unit" in df.columns
            assert "source" in df.columns
            assert len(df) == 2

    def test_fetch_handles_empty_results(self):
        """Verify behavior when no records are found."""
        mock_data = {"results": []}
        
        with patch('src.data.fetch_traits.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            df = fetch_traits_from_try(["NonExistentSpecies"])
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    def test_fetch_handles_api_error(self):
        """Verify behavior when API returns an error."""
        with patch('src.data.fetch_traits.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="API request failed"):
                fetch_traits_from_try(["Helianthus annuus"])


class TestVerifyTraitSource:
    """Tests for the verify_trait_source function."""

    def test_handbook_2013_is_verified(self):
        """Verify that 'Handbook 2013' source returns True."""
        assert verify_trait_source("Handbook 2013") is True

    def test_non_handbook_returns_false(self):
        """Verify that non-Handbook 2013 sources return False."""
        assert verify_trait_source("Kattge et al. 2011") is False
        assert verify_trait_source("TRY Database") is False
        assert verify_trait_source("Primary Literature") is False

    def test_case_insensitive_handbook(self):
        """Verify that case variations of 'Handbook 2013' are handled."""
        assert verify_trait_source("handbook 2013") is True
        assert verify_trait_source("HANDBOOK 2013") is True
        assert verify_trait_source("HandBook 2013") is True

    def test_none_source_returns_false(self):
        """Verify that None source returns False."""
        assert verify_trait_source(None) is False

    def test_empty_string_returns_false(self):
        """Verify that empty string source returns False."""
        assert verify_trait_source("") is False


class TestIntegration:
    """Integration tests combining fetch and verification."""

    def test_flag_unverified_protocol(self):
        """Verify that non-Handbook sources are flagged as 'unverified protocol'."""
        mock_data = {
            "results": [
                {
                    "species": "Helianthus annuus",
                    "trait": "SLA",
                    "value": 15.5,
                    "unit": "mm2/mg",
                    "source": "Kattge et al. 2011"
                },
                {
                    "species": "Helianthus annuus",
                    "trait": "height",
                    "value": 2.5,
                    "unit": "m",
                    "source": "Handbook 2013"
                }
            ]
        }
        
        with patch('src.data.fetch_traits.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            df = fetch_traits_from_try(["Helianthus annuus"])
            
            # Check that the first row is flagged as unverified
            assert df.iloc[0]["source_verified"] == "unverified protocol"
            assert df.iloc[1]["source_verified"] == "verified"

    def test_mixed_sources_handling(self):
        """Verify correct handling of mixed verified and unverified sources."""
        mock_data = {
            "results": [
                {"species": "A", "trait": "SLA", "value": 10, "unit": "mm2/mg", "source": "Handbook 2013"},
                {"species": "A", "trait": "SLA", "value": 12, "unit": "mm2/mg", "source": "Kattge 2011"},
                {"species": "B", "trait": "SLA", "value": 15, "unit": "mm2/mg", "source": "Handbook 2013"},
                {"species": "B", "trait": "SLA", "value": 14, "unit": "mm2/mg", "source": "Unknown Source"}
            ]
        }
        
        with patch('src.data.fetch_traits.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            df = fetch_traits_from_try(["A", "B"])
            
            # Verify counts
            assert df[df["source_verified"] == "verified"].shape[0] == 2
            assert df[df["source_verified"] == "unverified protocol"].shape[0] == 2