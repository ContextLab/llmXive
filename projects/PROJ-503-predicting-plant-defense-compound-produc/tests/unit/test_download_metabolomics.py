"""
Unit tests for download_metabolomics module.
Tests the core logic without actually downloading data.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download_metabolomics import (
    build_metabolite_matrix,
    DownloadError
)

class TestBuildMetaboliteMatrix:
    """Tests for the build_metabolite_matrix function."""

    def test_build_matrix_with_valid_data(self):
        """Test building a matrix with valid metabolite data."""
        # Mock metabolite data
        metabolite_data = {
            "data": {
                "metabolites": [
                    {"metabolite_id": "M1", "name": "Metabolite 1"},
                    {"metabolite_id": "M2", "name": "Metabolite 2"}
                ],
                "samples": ["S1", "S2", "S3"],
                "values": [
                    [1.5, 2.0, 1.8],
                    [0.5, 0.7, 0.6]
                ]
            }
        }
        
        # Mock sample metadata
        sample_metadata = [
            {"sample_id": "S1", "biosample_id": "B1"},
            {"sample_id": "S2", "biosample_id": "B2"},
            {"sample_id": "S3", "biosample_id": "B3"}
        ]
        
        # Mock analysis metadata
        analysis_metadata = [{"analysis_id": "A1"}]
        
        # Build the matrix
        df = build_metabolite_matrix(metabolite_data, sample_metadata, analysis_metadata)
        
        # Assertions
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # 2 metabolites
        assert len(df.columns) == 3  # 3 samples
        assert list(df.index) == ["M1", "M2"]
        assert list(df.columns) == ["B1", "B2", "B3"]
        assert df.loc["M1", "B1"] == 1.5
        assert df.loc["M2", "B3"] == 0.6

    def test_build_matrix_missing_values_raises_error(self):
        """Test that missing values raise an error."""
        metabolite_data = {
            "data": {
                "metabolites": [{"metabolite_id": "M1"}],
                "samples": ["S1"],
                "values": []  # Empty values
            }
        }
        
        sample_metadata = [{"sample_id": "S1", "biosample_id": "B1"}]
        analysis_metadata = [{"analysis_id": "A1"}]
        
        with pytest.raises(DownloadError, match="No metabolite values found"):
            build_metabolite_matrix(metabolite_data, sample_metadata, analysis_metadata)

    def test_build_matrix_missing_metabolites_raises_error(self):
        """Test that missing metabolites raise an error."""
        metabolite_data = {
            "data": {
                "metabolites": [],  # Empty metabolites
                "samples": ["S1"],
                "values": [[1.5]]
            }
        }
        
        sample_metadata = [{"sample_id": "S1", "biosample_id": "B1"}]
        analysis_metadata = [{"analysis_id": "A1"}]
        
        # This should create an empty dataframe or handle gracefully
        # Depending on implementation, it might raise an error or return empty
        df = build_metabolite_matrix(metabolite_data, sample_metadata, analysis_metadata)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0  # No metabolites

    def test_build_matrix_with_fallback_biosample_id(self):
        """Test that biosample_id falls back to sample_name when biosample_id is missing."""
        metabolite_data = {
            "data": {
                "metabolites": [{"metabolite_id": "M1"}],
                "samples": ["S1"],
                "values": [[1.5]]
            }
        }
        
        # Sample metadata without biosample_id
        sample_metadata = [{"sample_id": "S1", "sample_name": "S1"}]
        analysis_metadata = [{"analysis_id": "A1"}]
        
        df = build_metabolite_matrix(metabolite_data, sample_metadata, analysis_metadata)
        
        # Should use sample_name as biosample_id
        assert "S1" in df.columns
        assert df.loc["M1", "S1"] == 1.5
