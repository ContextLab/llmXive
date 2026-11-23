"""
Tests for T015a: Feature extraction (Part 1: Metadata).
Verifies that search_time and fixation_count are extracted correctly.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.features import load_trial_metadata, extract_features, process_dataset_features
from config import load_config

class TestMetadataExtraction:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_root = tempfile.mkdtemp()
        data_dir = Path(temp_root) / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        yield {
            "root": temp_root,
            "processed": processed_dir,
            "config": {
                "seeds": {"random": 42, "numpy": 42},
                "thresholds": {"default": [0.40, 0.50, 0.60]},
                "paths": {
                    "raw_data": str(data_dir / "raw"),
                    "processed_data": str(processed_dir),
                    "external_stimuli": str(data_dir / "external" / "stimuli"),
                    "results": str(data_dir / "results"),
                    "state": str(data_dir / "state")
                },
                "aggregation": False
            }
        }
        
        # Cleanup
        shutil.rmtree(temp_root)

    def test_load_trial_metadata_missing_file(self, temp_dirs):
        """Test behavior when preprocessed data file is missing."""
        df = load_trial_metadata(temp_dirs["config"])
        assert df.empty
        assert list(df.columns) == ['subject_id', 'trial_id', 'search_time', 'fixation_count', 'pupil_peak', 'pupil_mean', 'pupil_q25', 'pupil_q50', 'pupil_q75', 'x', 'y', 'timestamp', 'pupil_diameter']

    def test_extract_features_with_search_time(self, temp_dirs):
        """Test extraction when search_time is present in metadata."""
        # Create mock preprocessed data with search_time
        mock_data = pd.DataFrame({
            'subject_id': ['sub1', 'sub1', 'sub2', 'sub2'],
            'trial_id': [1, 1, 1, 1],
            'search_time': [2.5, 2.5, 3.0, 3.0],
            'pupil_diameter': [4.0, 4.1, 3.8, 3.9]
        })
        
        processed_file = Path(temp_dirs["config"]["paths"]["processed_data"]) / 'preprocessed_data.csv'
        mock_data.to_csv(processed_file, index=False)
        
        # Load and extract
        df = load_trial_metadata(temp_dirs["config"])
        features = extract_features(df, temp_dirs["config"])
        
        assert not features.empty
        assert 'search_time' in features.columns
        assert 'fixation_count' in features.columns
        
        # Check values
        assert features.loc[features['subject_id'] == 'sub1', 'search_time'].iloc[0] == 2.5
        assert features.loc[features['subject_id'] == 'sub1', 'fixation_count'].iloc[0] == 2
        assert features.loc[features['subject_id'] == 'sub2', 'search_time'].iloc[0] == 3.0

    def test_extract_features_missing_search_time(self, temp_dirs):
        """Test extraction when search_time is missing (should be null)."""
        # Create mock preprocessed data without search_time
        mock_data = pd.DataFrame({
            'subject_id': ['sub1', 'sub1'],
            'trial_id': [1, 1],
            'pupil_diameter': [4.0, 4.1]
        })
        
        processed_file = Path(temp_dirs["config"]["paths"]["processed_data"]) / 'preprocessed_data.csv'
        mock_data.to_csv(processed_file, index=False)
        
        # Load and extract
        df = load_trial_metadata(temp_dirs["config"])
        features = extract_features(df, temp_dirs["config"])
        
        assert not features.empty
        assert pd.isna(features['search_time'].iloc[0])
        assert features['status'].iloc[0] == 'MISSING_METADATA'
        assert features['fixation_count'].iloc[0] == 2

    def test_process_dataset_creates_output(self, temp_dirs):
        """Test that process_dataset_features creates features.csv."""
        # Create mock data
        mock_data = pd.DataFrame({
            'subject_id': ['sub1', 'sub1', 'sub2'],
            'trial_id': [1, 1, 1],
            'search_time': [2.0, 2.0, 4.0],
            'pupil_diameter': [4.0, 4.1, 3.8]
        })
        
        processed_file = Path(temp_dirs["config"]["paths"]["processed_data"]) / 'preprocessed_data.csv'
        mock_data.to_csv(processed_file, index=False)
        
        # Run processing
        process_dataset_features(temp_dirs["config"])
        
        # Verify output
        output_path = Path(temp_dirs["config"]["paths"]["processed_data"]) / 'features.csv'
        assert output_path.exists()
        
        result_df = pd.read_csv(output_path)
        assert 'search_time' in result_df.columns
        assert 'fixation_count' in result_df.columns
        assert 'target_salience' in result_df.columns
        assert 'status' in result_df.columns
        assert len(result_df) == 2  # Two subjects