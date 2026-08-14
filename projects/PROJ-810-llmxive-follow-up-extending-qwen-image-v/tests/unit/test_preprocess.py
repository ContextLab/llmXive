"""
Unit tests for code/data/preprocess.py

Tests:
- Extract ground truth labels from mock data
- Handle missing columns
- Validate output schema
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.data.preprocess import extract_ground_truth_labels, load_raw_dataset

class TestExtractGroundTruthLabels:
    
    def test_extract_text_and_image_labels(self):
        """Test extraction of both text and image labels."""
        mock_data = pd.DataFrame([
            {
                'image_id': 'img_001',
                'annotations': [
                    {'bbox': [10, 10, 100, 50], 'label': 'text'},
                    {'bbox': [200, 200, 300, 300], 'label': 'image'}
                ]
            }
        ])
        
        result = extract_ground_truth_labels(mock_data)
        
        assert len(result) == 2
        assert 'region_id' in result.columns
        assert 'modality_label' in result.columns
        assert 'bbox' in result.columns
        
        labels = set(result['modality_label'])
        assert 'text' in labels
        assert 'image' in labels
        
        # Check region_id format
        assert result.iloc[0]['region_id'].startswith('img_001_region_')
    
    def test_extract_with_alternative_label_keys(self):
        """Test extraction when label is under 'type' or 'modality' key."""
        mock_data = pd.DataFrame([
            {
                'image_id': 'img_002',
                'annotations': [
                    {'bbox': [0, 0, 50, 50], 'type': 'text'},
                    {'bbox': [60, 60, 100, 100], 'modality': 'image'}
                ]
            }
        ])
        
        result = extract_ground_truth_labels(mock_data)
        
        assert len(result) == 2
        assert result.iloc[0]['modality_label'] == 'text'
        assert result.iloc[1]['modality_label'] == 'image'
    
    def test_skip_unknown_labels(self):
        """Test that labels not 'text' or 'image' are skipped."""
        mock_data = pd.DataFrame([
            {
                'image_id': 'img_003',
                'annotations': [
                    {'bbox': [0, 0, 10, 10], 'label': 'text'},
                    {'bbox': [20, 20, 30, 30], 'label': 'unknown_type'},
                    {'bbox': [40, 40, 50, 50], 'label': 'image'}
                ]
            }
        ])
        
        result = extract_ground_truth_labels(mock_data)
        
        assert len(result) == 2
        # Should only have text and image
        assert set(result['modality_label']) == {'text', 'image'}
    
    def test_missing_bbox_column_raises_error(self):
        """Test that missing bbox column raises ValueError."""
        mock_data = pd.DataFrame([
            {
                'image_id': 'img_004',
                'other_col': ['data']
            }
        ])
        
        with pytest.raises(ValueError, match="Could not find bounding box column"):
            extract_ground_truth_labels(mock_data)
    
    def test_empty_annotations(self):
        """Test handling of empty annotations list."""
        mock_data = pd.DataFrame([
            {
                'image_id': 'img_005',
                'annotations': []
            }
        ])
        
        result = extract_ground_truth_labels(mock_data)
        
        assert len(result) == 0
        assert list(result.columns) == ['region_id', 'modality_label', 'bbox']

class TestLoadRawDataset:
    
    @patch('code.data.preprocess.RAW_DATA_PATH')
    def test_file_not_found(self, mock_path):
        """Test that FileNotFoundError is raised if raw data is missing."""
        mock_path.exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            load_raw_dataset()
    
    @patch('code.data.preprocess.RAW_DATA_PATH')
    @patch('pandas.read_parquet')
    def test_load_success(self, mock_read, mock_path):
        """Test successful loading of parquet file."""
        mock_path.exists.return_value = True
        mock_df = pd.DataFrame([{'id': 1}])
        mock_read.return_value = mock_df
        
        result = load_raw_dataset()
        
        mock_read.assert_called_once()
        pd.testing.assert_frame_equal(result, mock_df)