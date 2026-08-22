"""
Unit tests for code/processing/alignment.py

Tests the merging logic of salience scores and eye-tracking metrics.
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if necessary
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from processing.alignment import (
    load_salience_scores,
    load_fixation_metrics,
    merge_datasets,
    validate_alignment,
    write_aligned_dataset
)
from config import get_paths


class TestLoadSalienceScores:
    def test_load_salience_scores_success(self, tmp_path):
        """Test loading valid salience JSON files."""
        # Create mock directory structure
        salience_dir = tmp_path / "salience_maps"
        salience_dir.mkdir()
        
        # Create mock JSON files
        mock_data = [
            {"trial_id": "T001", "face_roi": {"mean": 0.5, "std": 0.1}},
            {"trial_id": "T002", "face_roi": {"mean": 0.7, "std": 0.2}}
        ]
        
        for i, data in enumerate(mock_data):
            with open(salience_dir / f"salience_{i}.json", 'w') as f:
                json.dump(data, f)
        
        # Mock get_paths to return our temp directory
        with patch('processing.alignment.get_paths') as mock_paths:
            mock_paths.return_value = {'processed_salience_maps': str(salience_dir)}
            
            df = load_salience_scores()
            
            assert len(df) == 2
            assert 'TrialID' in df.columns
            assert 'mean_salience' in df.columns
            assert df.iloc[0]['mean_salience'] == 0.5
            assert df.iloc[1]['mean_salience'] == 0.7

    def test_load_salience_scores_empty_dir(self, tmp_path):
        """Test loading from an empty directory."""
        salience_dir = tmp_path / "salience_maps"
        salience_dir.mkdir()
        
        with patch('processing.alignment.get_paths') as mock_paths:
            mock_paths.return_value = {'processed_salience_maps': str(salience_dir)}
            
            df = load_salience_scores()
            
            assert len(df) == 0
            assert list(df.columns) == ['TrialID', 'mean_salience', 'salience_std']


class TestMergeDatasets:
    def test_merge_success(self):
        """Test merging two DataFrames on TrialID."""
        fixation_df = pd.DataFrame({
            'TrialID': ['T001', 'T002', 'T003'],
            'dwell_time': [100, 200, 300]
        })
        
        salience_df = pd.DataFrame({
            'TrialID': ['T001', 'T002', 'T004'],
            'mean_salience': [0.5, 0.7, 0.9]
        })
        
        merged = merge_datasets(salience_df, fixation_df)
        
        # Inner join should result in 2 rows (T001, T002)
        assert len(merged) == 2
        assert set(merged['TrialID']) == {'T001', 'T002'}
        assert 'dwell_time' in merged.columns
        assert 'mean_salience' in merged.columns

    def test_merge_no_overlap(self):
        """Test merging when there is no overlap in TrialIDs."""
        fixation_df = pd.DataFrame({
            'TrialID': ['T001', 'T002'],
            'dwell_time': [100, 200]
        })
        
        salience_df = pd.DataFrame({
            'TrialID': ['T003', 'T004'],
            'mean_salience': [0.5, 0.7]
        })
        
        merged = merge_datasets(salience_df, fixation_df)
        
        assert len(merged) == 0

    def test_merge_duplicate_ids(self):
        """Test merging with duplicate TrialIDs."""
        fixation_df = pd.DataFrame({
            'TrialID': ['T001', 'T001', 'T002'],
            'dwell_time': [100, 100, 200]
        })
        
        salience_df = pd.DataFrame({
            'TrialID': ['T001', 'T002'],
            'mean_salience': [0.5, 0.7]
        })
        
        merged = merge_datasets(salience_df, fixation_df)
        
        # T001 appears twice in fixation, once in salience -> 2 rows for T001
        assert len(merged) == 3


class TestValidateAlignment:
    def test_validation_pass(self):
        """Test validation on a clean dataset."""
        df = pd.DataFrame({
            'TrialID': ['T001', 'T002'],
            'mean_salience': [0.5, 0.7],
            'dwell_time': [100, 200],
            'first_fixation_prob': [0.8, 0.9]
        })
        
        report = validate_alignment(df)
        
        assert report['status'] == 'PASS'
        assert report['total_trials'] == 2
        assert len(report['issues']) == 0

    def test_validation_empty(self):
        """Test validation on an empty dataset."""
        df = pd.DataFrame(columns=['TrialID', 'mean_salience'])
        
        report = validate_alignment(df)
        
        assert report['status'] == 'FAIL'
        assert "Merged dataset is empty" in report['issues']

    def test_validation_duplicates(self):
        """Test validation with duplicate TrialIDs."""
        df = pd.DataFrame({
            'TrialID': ['T001', 'T001'],
            'mean_salience': [0.5, 0.7],
            'dwell_time': [100, 200],
            'first_fixation_prob': [0.8, 0.9]
        })
        
        report = validate_alignment(df)
        
        assert report['status'] == 'WARN'
        assert any("duplicate" in issue for issue in report['issues'])

    def test_validation_missing_values(self):
        """Test validation with missing critical values."""
        df = pd.DataFrame({
            'TrialID': ['T001', 'T002'],
            'mean_salience': [0.5, None],
            'dwell_time': [100, 200],
            'first_fixation_prob': [0.8, 0.9]
        })
        
        report = validate_alignment(df)
        
        assert report['status'] == 'WARN'
        assert any("missing" in issue for issue in report['issues'])


class TestWriteAlignedDataset:
    def test_write_aligned_dataset(self, tmp_path):
        """Test writing the aligned dataset to CSV."""
        df = pd.DataFrame({
            'TrialID': ['T001', 'T002'],
            'mean_salience': [0.5, 0.7],
            'dwell_time': [100, 200]
        })
        
        report = {'status': 'PASS', 'issues': []}
        
        # Mock get_paths to return temp directory
        output_file = str(tmp_path / "aligned_metrics.csv")
        
        with patch('processing.alignment.get_paths') as mock_paths:
            mock_paths.return_value = {'processed_aligned_metrics': output_file}
            
            result_path = write_aligned_dataset(df, report)
            
            assert os.path.exists(result_path)
            loaded_df = pd.read_csv(result_path)
            assert len(loaded_df) == 2
            assert 'disclaimer' in loaded_df.columns
            assert "CORRELATIONAL ONLY" in loaded_df.iloc[0]['disclaimer']