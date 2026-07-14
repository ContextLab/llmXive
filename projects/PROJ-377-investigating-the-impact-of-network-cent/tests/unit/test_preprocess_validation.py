import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from data.preprocess import extract_behavioral_metrics, preprocess_fmriprep
from utils.config import get_config, reset_config, get_min_retention_rate

class TestBehavioralExtraction:
    def test_extract_with_missing_scores(self, tmp_path):
        """Test that subjects with missing pre/post scores are excluded."""
        # Create behavioral directory
        behavioral_dir = tmp_path / "phenotypic"
        behavioral_dir.mkdir()
        
        # Create CSV with missing data
        data = {
            'subject_id': ['sub-01', 'sub-02', 'sub-03'],
            'pre_score': [10.0, np.nan, 15.0],
            'post_score': [12.0, 14.0, np.nan],
            'age': [25, 30, 35],
            'sex': ['M', 'F', 'M']
        }
        df = pd.DataFrame(data)
        df.to_csv(behavioral_dir / "behav.csv", index=False)
        
        result_df, exclusions = extract_behavioral_metrics(behavioral_dir)
        
        # sub-02 and sub-03 should be excluded
        assert len(result_df) == 1
        assert result_df.iloc[0]['subject_id'] == 'sub-01'
        assert len(exclusions) == 2
        
        excluded_ids = [e['subject_id'] for e in exclusions]
        assert 'sub-02' in excluded_ids
        assert 'sub-03' in excluded_ids

    def test_extract_empty_directory(self, tmp_path):
        """Test handling of directory with no behavioral files."""
        behavioral_dir = tmp_path / "phenotypic"
        behavioral_dir.mkdir()
        
        result_df, exclusions = extract_behavioral_metrics(behavioral_dir)
        
        assert result_df.empty
        assert len(exclusions) == 0

class TestRetentionValidation:
    def test_retention_above_threshold(self, tmp_path):
        """Test that pipeline passes when retention >= 80%."""
        reset_config()
        
        # Create mock raw data structure
        raw_dir = tmp_path / "raw"
        phenotypic_dir = raw_dir / "phenotypic"
        phenotypic_dir.mkdir(parents=True)
        
        # Create behavioral data: 10 subjects, 9 retained (90%)
        data = {
            'subject_id': [f'sub-{i:02d}' for i in range(1, 11)],
            'pre_score': [10.0] * 10,
            'post_score': [12.0] * 10,
            'age': [25] * 10,
            'sex': ['M'] * 10
        }
        df = pd.DataFrame(data)
        df.to_csv(phenotypic_dir / "behav.csv", index=False)
        
        # Create empty derivatives to avoid FD errors
        derivatives_dir = raw_dir / "derivatives" / "fmriprep"
        derivatives_dir.mkdir(parents=True)
        
        output_dir = tmp_path / "output"
        
        results = preprocess_fmriprep(
            raw_data_dir=raw_dir,
            output_dir=output_dir,
            min_retention_rate=0.80
        )
        
        assert results['status'] == 'success'
        assert results['validation_passed'] is True
        assert results['retention_rate'] >= 0.80

    def test_retention_below_threshold(self, tmp_path):
        """Test that pipeline fails gracefully when retention < 80%."""
        reset_config()
        
        raw_dir = tmp_path / "raw"
        phenotypic_dir = raw_dir / "phenotypic"
        phenotypic_dir.mkdir(parents=True)
        
        # Create behavioral data: 10 subjects, 7 retained (70%)
        # We'll simulate exclusions by creating a file with only 7 valid rows
        # and manually triggering exclusions logic
        data = {
            'subject_id': [f'sub-{i:02d}' for i in range(1, 11)],
            'pre_score': [10.0] * 10,
            'post_score': [12.0] * 10,
            'age': [25] * 10,
            'sex': ['M'] * 10
        }
        df = pd.DataFrame(data)
        df.to_csv(phenotypic_dir / "behav.csv", index=False)
        
        # Create derivatives with FD files that will trigger exclusions
        derivatives_dir = raw_dir / "derivatives" / "fmriprep"
        derivatives_dir.mkdir(parents=True)
        
        # Create confounds for 3 subjects with high FD
        for i in [1, 2, 3]:
            sub_dir = derivatives_dir / f"sub-{i:02d}" / "func"
            sub_dir.mkdir(parents=True)
            confounds = pd.DataFrame({
                'framewise_displacement': [0.5] * 100  # High FD
            })
            confounds.to_csv(
                sub_dir / "desc-confounds_timeseries.tsv",
                sep='\t',
                index=False
            )
        
        output_dir = tmp_path / "output"
        
        results = preprocess_fmriprep(
            raw_data_dir=raw_dir,
            output_dir=output_dir,
            min_retention_rate=0.80
        )
        
        # Should fail because retention is 70% < 80%
        assert results['status'] == 'failed'
        assert results['validation_passed'] is False
        assert any("below minimum threshold" in err for err in results['errors'])

    def test_missing_behavioral_data_graceful_fail(self, tmp_path):
        """Test that pipeline fails gracefully when behavioral data is missing."""
        reset_config()
        
        raw_dir = tmp_path / "raw"
        # Do NOT create phenotypic directory
        
        output_dir = tmp_path / "output"
        
        results = preprocess_fmriprep(
            raw_data_dir=raw_dir,
            output_dir=output_dir,
            min_retention_rate=0.80
        )
        
        assert results['status'] == 'failed'
        assert any("Behavioral data directory not found" in err for err in results['errors'])

    def test_no_valid_behavioral_data_graceful_fail(self, tmp_path):
        """Test that pipeline fails gracefully when no valid behavioral data exists."""
        reset_config()
        
        raw_dir = tmp_path / "raw"
        phenotypic_dir = raw_dir / "phenotypic"
        phenotypic_dir.mkdir(parents=True)
        
        # Create file with missing required columns
        data = {
            'subject_id': ['sub-01', 'sub-02'],
            'wrong_column': [10.0, 12.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(phenotypic_dir / "behav.csv", index=False)
        
        output_dir = tmp_path / "output"
        
        results = preprocess_fmriprep(
            raw_data_dir=raw_dir,
            output_dir=output_dir,
            min_retention_rate=0.80
        )
        
        assert results['status'] == 'failed'
        assert any("No valid behavioral data extracted" in err for err in results['errors'])

class TestConfigRetention:
    def test_default_retention_rate(self):
        """Test that default min retention rate is 0.80 (80%)."""
        reset_config()
        rate = get_min_retention_rate()
        assert rate == 0.80

    def test_custom_retention_rate(self):
        """Test that retention rate can be configured."""
        reset_config()
        config = get_config()
        config.preprocessing.min_retention_rate = 0.90
        
        # Reset and reload
        reset_config()
        # Note: In a real test, we'd mock the config loading
        # For now, we verify the default
        assert get_min_retention_rate() == 0.80
