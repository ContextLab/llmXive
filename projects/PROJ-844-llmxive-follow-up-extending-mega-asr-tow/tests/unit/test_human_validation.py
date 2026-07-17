"""
Unit tests for the human_validation module.
"""
import pytest
import os
import sys
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from human_validation import load_and_merge_subsets, create_validation_sample, generate_annotation_csv

@pytest.fixture
def mock_config():
    return {
        'random_seed': 42,
        'validation_sample_size': 10,
        'paths': {
            'validation_dir': 'data/validation'
        },
        'librispeech': {
            'subset_path': 'data/derived/librispeech_subset.parquet'
        },
        'coraa': {
            'subset_path': 'data/derived/coraa_subset.parquet'
        }
    }

@pytest.fixture
def mock_data():
    return [
        {'audio_path': 'audio1.wav', 'text': 'Hello world', 'speaker_id': 'spk1', 'snr_bucket': 'low', 'dataset_source': 'librispeech'},
        {'audio_path': 'audio2.wav', 'text': 'Test sentence', 'speaker_id': 'spk1', 'snr_bucket': 'low', 'dataset_source': 'librispeech'},
        {'audio_path': 'audio3.wav', 'text': 'Another test', 'speaker_id': 'spk2', 'snr_bucket': 'high', 'dataset_source': 'coraa'},
        {'audio_path': 'audio4.wav', 'text': 'More data', 'speaker_id': 'spk2', 'snr_bucket': 'high', 'dataset_source': 'coraa'},
        {'audio_path': 'audio5.wav', 'text': 'Sample 5', 'speaker_id': 'spk3', 'snr_bucket': 'med', 'dataset_source': 'librispeech'},
    ]

def test_create_validation_sample_stratification(mock_config, mock_data):
    """Test that sampling respects strata distribution."""
    # Request a sample size larger than data to ensure all are taken
    result = create_validation_sample(mock_data, len(mock_data), mock_config)
    assert len(result) == len(mock_data)
    
    # Check that speaker IDs are preserved
    speaker_ids = [item['speaker_id'] for item in result]
    assert 'spk1' in speaker_ids
    assert 'spk2' in speaker_ids

def test_create_validation_sample_proportional(mock_config, mock_data):
    """Test proportional allocation."""
    # Request a small sample
    result = create_validation_sample(mock_data, 2, mock_config)
    # Should have at least 1 item (or 2 depending on rounding logic)
    assert len(result) <= 2
    assert len(result) > 0

def test_generate_annotation_csv_schema(mock_config, mock_data):
    """Test that the generated CSV has the correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_annotations.csv'
        generate_annotation_csv(mock_data, output_path, mock_config)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            expected_fields = [
                'sample_id', 'audio_path', 'text', 'speaker_id', 
                'snr_bucket', 'dataset_source', 'intelligibility_score', 
                'annotation_status'
            ]
            
            for field in expected_fields:
                assert field in fieldnames, f"Missing field: {field}"
            
            rows = list(reader)
            assert len(rows) == len(mock_data)
            
            # Check that intelligibility_score is PENDING (as per protocol)
            for row in rows:
                assert row['intelligibility_score'] == 'PENDING'
                assert row['annotation_status'] == 'READY_FOR_ANNOTATION'

def test_generate_annotation_csv_real_paths(mock_config, mock_data):
    """Test that real audio paths are preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_annotations.csv'
        generate_annotation_csv(mock_data, output_path, mock_config)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check that audio paths match input
            input_paths = {item['audio_path'] for item in mock_data}
            output_paths = {row['audio_path'] for row in rows}
            
            assert input_paths == output_paths