"""
Unit tests for temporal validation functionality.
"""
import pytest
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.validate_temporal import (
    parse_date,
    load_manifest,
    load_phenotype_data,
    check_temporal_fields,
    validate_studies_from_manifest,
    TemporalVerificationWarning,
    TemporalVerificationError
)

class TestParseDate:
    def test_parse_standard_date(self):
        """Test parsing standard YYYY-MM-DD format."""
        result = parse_date("2023-01-15")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime(self):
        """Test parsing datetime format."""
        result = parse_date("2023-01-15 14:30:00")
        assert result is not None
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_invalid_date(self):
        """Test parsing invalid date returns None."""
        result = parse_date("not-a-date")
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_date("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None returns None."""
        result = parse_date(None)
        assert result is None

class TestCheckTemporalFields:
    def test_no_temporal_fields(self):
        """Test detection when no temporal fields exist."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'resistance_score': [0.5, 0.7, 0.3]
        })
        phenotype_data = {
            'study_id': 'test_study',
            'df': df,
            'columns': list(df.columns)
        }
        
        status, verified, missing = check_temporal_fields(phenotype_data)
        assert status == 'unverified'
        assert len(missing) > 0

    def test_baseline_keyword_detection(self):
        """Test detection of baseline/pre-challenge keywords."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'baseline_status': ['pre-challenge', 'pre-challenge', 'pre-challenge'],
            'resistance_score': [0.5, 0.7, 0.3]
        })
        phenotype_data = {
            'study_id': 'test_study',
            'df': df,
            'columns': list(df.columns)
        }
        
        status, verified, missing = check_temporal_fields(phenotype_data)
        assert status == 'verified'
        assert len(verified) > 0

    def test_date_comparison(self):
        """Test date comparison logic."""
        df = pd.DataFrame({
            'sample_date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'inoculation_date': ['2023-01-10', '2023-01-11', '2023-01-12'],
            'resistance_score': [0.5, 0.7, 0.3]
        })
        phenotype_data = {
            'study_id': 'test_study',
            'df': df,
            'columns': list(df.columns)
        }
        
        status, verified, missing = check_temporal_fields(phenotype_data)
        assert status == 'verified'
        assert 'sample_date' in verified or 'inoculation_date' in verified

    def test_missing_inoculation_date(self):
        """Test when inoculation date is missing but sample date exists."""
        df = pd.DataFrame({
            'sample_date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'resistance_score': [0.5, 0.7, 0.3]
        })
        phenotype_data = {
            'study_id': 'test_study',
            'df': df,
            'columns': list(df.columns)
        }
        
        status, verified, missing = check_temporal_fields(phenotype_data)
        # Should be verified if baseline keywords are found, otherwise unverified
        assert status in ['verified', 'unverified']

class TestLoadManifest:
    def test_load_valid_manifest(self, tmp_path):
        """Test loading a valid manifest file."""
        manifest_data = [
            {'study_id': 'ST001', 'title': 'Test Study'},
            {'study_id': 'ST002', 'title': 'Another Study'}
        ]
        
        manifest_file = tmp_path / "study_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f)
        
        result = load_manifest(manifest_file)
        assert len(result) == 2
        assert result[0]['study_id'] == 'ST001'

    def test_load_nonexistent_manifest(self, tmp_path):
        """Test loading a non-existent manifest file."""
        with pytest.raises(FileNotFoundError):
            load_manifest(tmp_path / "nonexistent.json")

class TestLoadPhenotypeData:
    def test_load_phenotype_csv(self, tmp_path):
        """Test loading phenotype CSV file."""
        # Create mock raw directory
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        phenotype_file = raw_dir / "ST001_phenotype.csv"
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'resistance_score': [0.5, 0.7, 0.3]
        })
        df.to_csv(phenotype_file, index=False)
        
        # Mock the global DATA_RAW_DIR
        with patch('code.data.validate_temporal.DATA_RAW_DIR', raw_dir):
            result = load_phenotype_data("ST001")
            
        assert result is not None
        assert result['study_id'] == 'ST001'
        assert len(result['df']) == 3

    def test_phenotype_not_found(self, tmp_path):
        """Test when phenotype file doesn't exist."""
        with patch('code.data.validate_temporal.DATA_RAW_DIR', tmp_path):
            result = load_phenotype_data("NONEXISTENT")
        assert result is None

class TestValidateStudiesFromManifest:
    def test_validate_single_verified_study(self, tmp_path):
        """Test validation with one verified study."""
        manifest = [{'study_id': 'ST001'}]
        
        # Create mock phenotype with baseline
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        phenotype_file = raw_dir / "ST001_phenotype.csv"
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'baseline_status': ['pre-challenge', 'pre-challenge']
        })
        df.to_csv(phenotype_file, index=False)
        
        with patch('code.data.validate_temporal.DATA_RAW_DIR', raw_dir):
            results = validate_studies_from_manifest(manifest)
        
        assert results['summary']['total'] == 1
        assert results['summary']['verified'] == 1

    def test_validate_multiple_studies(self, tmp_path):
        """Test validation with multiple studies."""
        manifest = [
            {'study_id': 'ST001'},
            {'study_id': 'ST002'},
            {'study_id': 'ST003'}
        ]
        
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # ST001: verified
        df1 = pd.DataFrame({
            'sample_id': [1],
            'baseline_status': ['pre-challenge']
        })
        df1.to_csv(raw_dir / "ST001_phenotype.csv", index=False)
        
        # ST002: unverified (no temporal fields)
        df2 = pd.DataFrame({
            'sample_id': [1],
            'resistance_score': [0.5]
        })
        df2.to_csv(raw_dir / "ST002_phenotype.csv", index=False)
        
        # ST003: verified
        df3 = pd.DataFrame({
            'sample_id': [1],
            'timepoint': ['baseline']
        })
        df3.to_csv(raw_dir / "ST003_phenotype.csv", index=False)
        
        with patch('code.data.validate_temporal.DATA_RAW_DIR', raw_dir):
            results = validate_studies_from_manifest(manifest)
        
        assert results['summary']['total'] == 3
        assert results['summary']['verified'] == 2
        assert results['summary']['unverified'] == 1

class TestMain:
    def test_main_with_verified_studies(self, tmp_path, capsys):
        """Test main function with verified studies."""
        # Setup directories
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create manifest
        manifest = [{'study_id': 'ST001'}]
        manifest_file = raw_dir / "study_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Create verified phenotype
        phenotype_file = raw_dir / "ST001_phenotype.csv"
        df = pd.DataFrame({
            'sample_id': [1],
            'baseline_status': ['pre-challenge']
        })
        df.to_csv(phenotype_file, index=False)
        
        with patch('code.data.validate_temporal.DATA_RAW_DIR', raw_dir), \
             patch('code.data.validate_temporal.DATA_PROCESSED_DIR', processed_dir):
            with pytest.raises(SystemExit) as exc_info:
                from code.data.validate_temporal import main
                main()
            
            assert exc_info.value.code == 0
        
        # Verify output file created
        output_file = processed_dir / "temporal_validation_log.json"
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        assert data['summary']['verified'] >= 1

    def test_main_with_no_verified_studies(self, tmp_path, capsys):
        """Test main function with no verified studies."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        manifest = [{'study_id': 'ST001'}]
        manifest_file = raw_dir / "study_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Create unverified phenotype
        phenotype_file = raw_dir / "ST001_phenotype.csv"
        df = pd.DataFrame({
            'sample_id': [1],
            'resistance_score': [0.5]
        })
        df.to_csv(phenotype_file, index=False)
        
        with patch('code.data.validate_temporal.DATA_RAW_DIR', raw_dir), \
             patch('code.data.validate_temporal.DATA_PROCESSED_DIR', processed_dir):
            with pytest.raises(SystemExit) as exc_info:
                from code.data.validate_temporal import main
                main()
            
            assert exc_info.value.code == 1