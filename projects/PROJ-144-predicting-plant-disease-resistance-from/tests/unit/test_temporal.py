"""
Unit tests for temporal validation functionality.
"""

import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.validate_temporal import validate_temporal_consistency, validate_studies_from_manifest
from utils.exceptions import TemporalVerificationError, DataUnavailableError


class TestTemporalValidation:
    """Test cases for temporal validation functions."""

    def test_validate_temporal_consistency_with_baseline_column(self):
        """Test validation passes when baseline column exists."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'baseline_metabolite': [10.5, 12.3, 11.1],
            'disease_status': [0, 1, 0]
        })
        
        result = validate_temporal_consistency(df, "test_study_1")
        
        assert result["study_id"] == "test_study_1"
        assert result["passed"] is True
        assert "baseline" in str(result["details"]["keywords_found"]).lower()

    def test_validate_temporal_consistency_with_pre_challenge_keyword(self):
        """Test validation passes when pre-challenge keyword is found in values."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'time_point': ['pre-challenge', 'pre-challenge', 'baseline'],
            'metabolite_a': [10.5, 12.3, 11.1]
        })
        
        result = validate_temporal_consistency(df, "test_study_2")
        
        assert result["study_id"] == "test_study_2"
        assert result["passed"] is True

    def test_validate_temporal_consistency_with_time_zero(self):
        """Test validation passes when time=0 is present."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'time': [0, 0, 0],
            'metabolite_a': [10.5, 12.3, 11.1]
        })
        
        result = validate_temporal_consistency(df, "test_study_3")
        
        assert result["study_id"] == "test_study_3"
        assert result["passed"] is True

    def test_validate_temporal_consistency_fails_no_markers(self):
        """Test validation fails when no temporal markers are found."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'metabolite_a': [10.5, 12.3, 11.1],
            'disease_status': [0, 1, 0]
        })
        
        with pytest.raises(TemporalVerificationError):
            validate_temporal_consistency(df, "test_study_4")

    def test_validate_temporal_consistency_empty_dataframe(self):
        """Test validation fails for empty DataFrame."""
        df = pd.DataFrame(columns=['sample_id', 'metabolite_a'])
        
        with pytest.raises(TemporalVerificationError):
            validate_temporal_consistency(df, "test_study_5")

    def test_validate_studies_from_manifest_missing_file(self):
        """Test that missing manifest raises DataUnavailableError."""
        with pytest.raises(DataUnavailableError):
            validate_studies_from_manifest(Path("/nonexistent/manifest.json"))

    def test_validate_studies_from_manifest_with_temporal_data(self):
        """Test full validation flow with real file structure."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create raw data directory
            raw_dir = tmpdir / "data" / "raw"
            raw_dir.mkdir(parents=True)
            
            # Create processed data directory
            processed_dir = tmpdir / "data" / "processed"
            processed_dir.mkdir(parents=True)
            
            # Create manifest
            manifest = [{
                "study_id": "temporal_test_study",
                "title": "Test Study",
                "download_url": "http://example.com",
                "phenotype_url": "http://example.com/phenotype"
            }]
            
            manifest_path = raw_dir / "study_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Create phenotype file with temporal markers
            phenotype_df = pd.DataFrame({
                'sample_id': [1, 2, 3],
                'time_point': ['baseline', 'pre-challenge', 'pre_inoculation'],
                'disease_resistance': [1, 0, 1]
            })
            
            phenotype_path = raw_dir / "temporal_test_study_phenotype.csv"
            phenotype_df.to_csv(phenotype_path, index=False)
            
            # Run validation
            results = validate_studies_from_manifest(manifest_path)
            
            assert len(results) == 1
            assert results[0]["study_id"] == "temporal_test_study"
            assert results[0]["passed"] is True

    def test_validate_studies_from_manifest_fails_without_temporal_data(self):
        """Test full validation flow fails when temporal data is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create raw data directory
            raw_dir = tmpdir / "data" / "raw"
            raw_dir.mkdir(parents=True)
            
            # Create manifest
            manifest = [{
                "study_id": "no_temporal_study",
                "title": "Test Study No Temporal",
                "download_url": "http://example.com",
                "phenotype_url": "http://example.com/phenotype"
            }]
            
            manifest_path = raw_dir / "study_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f)
            
            # Create phenotype file WITHOUT temporal markers
            phenotype_df = pd.DataFrame({
                'sample_id': [1, 2, 3],
                'metabolite_a': [10.5, 12.3, 11.1],
                'disease_resistance': [1, 0, 1]
            })
            
            phenotype_path = raw_dir / "no_temporal_study_phenotype.csv"
            phenotype_df.to_csv(phenotype_path, index=False)
            
            # Run validation - should raise TemporalVerificationError
            with pytest.raises(TemporalVerificationError):
                validate_studies_from_manifest(manifest_path)