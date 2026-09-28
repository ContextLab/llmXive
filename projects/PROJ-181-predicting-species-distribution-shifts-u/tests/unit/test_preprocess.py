"""
Unit tests for preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess import thin_occurrences, check_insufficient_data, filter_and_deduplicate


@pytest.fixture
def sample_occurrence_data():
    """Create sample occurrence data for testing."""
    data = {
        'species': ['Species_A', 'Species_A', 'Species_B', 'Species_C'],
        'decimalLatitude': [40.0, 40.001, 45.0, 50.0],
        'decimalLongitude': [-75.0, -75.001, -80.0, -90.0],
        'eventDate': ['2010-01-01', '2010-01-01', '2015-05-15', '2018-08-08'],
        'source_identifier': ['obs1', 'obs2', 'obs3', 'obs4'],
        'download_timestamp': [datetime.now().isoformat()] * 4,
        'original_dataset_name': ['dataset1', 'dataset1', 'dataset2', 'dataset3']
    }
    return pd.DataFrame(data)


def test_thin_occurrences_temp_file(sample_occurrence_data):
    """Test spatial thinning with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Save sample data
        sample_occurrence_data.to_csv(input_path, index=False)
        
        # Run thinning
        result = thin_occurrences(input_path, output_path, distance_km=0.1)
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Verify counts
        assert result['before_count'] == len(sample_occurrence_data)
        assert result['after_count'] <= result['before_count']
        
        # Verify output data
        output_df = pd.read_csv(output_path)
        assert len(output_df) == result['after_count']


def test_check_insufficient_data_temp_file():
    """Test data sufficiency check with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test data with insufficient records for one species
        data = {
            'species': ['Species_A', 'Species_A', 'Species_B', 'Species_C', 'Species_C'],
            'decimalLatitude': [40.0, 40.1, 45.0, 50.0, 50.1],
            'decimalLongitude': [-75.0, -75.1, -80.0, -90.0, -90.1],
            'eventDate': ['2010-01-01'] * 5,
            'source_identifier': ['obs1'] * 5,
            'download_timestamp': [datetime.now().isoformat()] * 5,
            'original_dataset_name': ['dataset1'] * 5
        }
        input_path = os.path.join(tmpdir, "input.csv")
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        # Test with threshold of 3 (Species_A and Species_C should be flagged)
        # Note: This test modifies global metrics, so we isolate the file path
        import preprocess
        original_metrics_dir = preprocess.METRICS_DIR
        
        # Temporarily redirect metrics
        metrics_tmp = os.path.join(tmpdir, "metrics")
        os.makedirs(metrics_tmp, exist_ok=True)
        preprocess.METRICS_DIR = Path(metrics_tmp)
        
        try:
            check_insufficient_data(input_path, threshold=3, period="test_period")
            
            # Check metrics file
            metrics_file = os.path.join(metrics_tmp, "data_sufficiency.json")
            assert os.path.exists(metrics_file)
            
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            
            # Should have entries for Species_B (only 1 record)
            # Species_A has 2, Species_C has 2 - both < 3
            species_flagged = [m['species'] for m in metrics if m['count'] < 3]
            assert len(species_flagged) > 0
        finally:
            # Restore original
            preprocess.METRICS_DIR = original_metrics_dir


def test_filter_and_deduplicate_temp_file(sample_occurrence_data):
    """Test filtering and deduplication with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.csv")
        
        # Add duplicate row
        duplicate_data = sample_occurrence_data.copy()
        duplicate_data = pd.concat([duplicate_data, duplicate_data.iloc[[0]]], ignore_index=True)
        duplicate_data.to_csv(input_path, index=False)
        
        # Run filtering
        result = filter_and_deduplicate(input_path, output_path)
        
        # Verify output exists
        assert os.path.exists(output_path)
        
        # Verify deduplication occurred
        assert result['after_count'] < result['before_count']
        
        # Verify output data
        output_df = pd.read_csv(output_path)
        assert len(output_df) == result['after_count']
        assert 'geometry' not in output_df.columns  # Ensure geometry not saved