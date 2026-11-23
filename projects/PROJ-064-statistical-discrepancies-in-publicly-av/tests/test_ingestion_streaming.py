"""
Unit tests for streaming data ingestion functionality.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import itertools

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import DataIngestionPipeline

class TestStreamingIngestion:
    """Test cases for streaming ingestion functionality."""
    
    @pytest.fixture
    def mock_source_config(self):
        """Provide a mock source configuration."""
        return {
            'name': 'test_source',
            'url': 'https://example.com/data.csv',
            'checksum': 'abc123'
        }
    
    @pytest.fixture
    def pipeline(self, mock_source_config, tmp_path):
        """Create a pipeline instance with temporary directories."""
        return DataIngestionPipeline(
            source_config=mock_source_config,
            state_dir=str(tmp_path / "state"),
            data_dir=str(tmp_path / "data"),
            verify_checksum=False
        )
    
    def test_deterministic_sample(self, pipeline):
        """Test deterministic sampling produces consistent results."""
        # Create a mock iterator
        mock_data = [{'id': i, 'value': i*2} for i in range(100)]
        iterator = iter(mock_data)
        
        # Sample 10 rows
        sample1 = pipeline._deterministic_sample(iterator, 10, seed=42)
        
        # Create new iterator and sample again
        iterator2 = iter(mock_data)
        sample2 = pipeline._deterministic_sample(iterator2, 10, seed=42)
        
        # Should be identical
        assert len(sample1) == 10
        assert len(sample2) == 10
        assert sample1 == sample2
    
    def test_online_statistics_computation(self, pipeline):
        """Test online statistics computation."""
        # Create mock data
        mock_data = [
            {'precinct_votes': 100, 'county_total': 100},
            {'precinct_votes': 150, 'county_total': 140},
            {'precinct_votes': 200, 'county_total': 210},
            {'precinct_votes': 50, 'county_total': 50},
            {'precinct_votes': None, 'county_total': 100},  # Missing data
        ]
        
        stats = pipeline._compute_online_statistics(iter(mock_data), batch_size=2)
        
        # Verify basic stats
        assert stats['total_precincts'] == 4  # One missing
        assert stats['batches_processed'] >= 1
        assert 'avg_discrepancy_pct' in stats
    
    def test_batch_processing(self, pipeline):
        """Test batch processing logic."""
        batch = [
            {'precinct_votes': 100, 'county_total': 100},
            {'precinct_votes': 150, 'county_total': 140},
        ]
        
        batch_stats = pipeline._process_batch(batch)
        
        assert batch_stats['count'] == 2
        assert batch_stats['precinct_sum'] == 250
        assert batch_stats['county_reported'] == 240
        # Discrepancy: |100-100| + |150-140| = 0 + 10 = 10
        assert batch_stats['discrepancy_abs'] == 10
    
    def test_directional_anomaly_detection(self, pipeline):
        """Test detection of directional anomalies (precinct sum > county total)."""
        batch = [
            {'precinct_votes': 100, 'county_total': 100},  # Normal
            {'precinct_votes': 150, 'county_total': 140},  # Anomaly
            {'precinct_votes': 50, 'county_total': 60},   # Normal
        ]
        
        batch_stats = pipeline._process_batch(batch)
        
        assert batch_stats['directional_anomalies'] == 1
    
    def test_missing_data_handling(self, pipeline):
        """Test handling of missing data."""
        batch = [
            {'precinct_votes': 100, 'county_total': 100},
            {'precinct_votes': None, 'county_total': 100},  # Missing
            {'precinct_votes': 50, 'county_total': None},   # Missing
        ]
        
        batch_stats = pipeline._process_batch(batch)
        
        assert batch_stats['missing_data'] == 2
        assert batch_stats['count'] == 1  # Only one valid record
    
    def test_zero_county_votes_handling(self, pipeline):
        """Test handling of zero county votes."""
        batch = [
            {'precinct_votes': 100, 'county_total': 100},
            {'precinct_votes': 150, 'county_total': 0},  # Zero county votes
        ]
        
        batch_stats = pipeline._process_batch(batch)
        
        # Record with zero county votes should be skipped
        assert batch_stats['count'] == 1
    
    def test_aggregate_stats(self, pipeline):
        """Test aggregation of batch statistics."""
        total = {
            'total_precincts': 10,
            'total_precinct_sum': 1000.0,
            'total_county_reported': 950.0,
            'total_discrepancy_abs': 50.0,
            'total_discrepancy_pct': 5.0,
            'missing_data_count': 2,
            'directional_anomalies': 1,
            'batches_processed': 1
        }
        
        batch = {
            'count': 5,
            'precinct_sum': 500.0,
            'county_reported': 480.0,
            'discrepancy_abs': 20.0,
            'discrepancy_pct': 4.0,
            'missing_data': 1,
            'directional_anomalies': 0
        }
        
        pipeline._aggregate_stats(total, batch)
        
        assert total['total_precincts'] == 15
        assert total['total_precinct_sum'] == 1500.0
        assert total['total_county_reported'] == 1430.0
        assert total['total_discrepancy_abs'] == 70.0
        assert total['total_discrepancy_pct'] == 9.0
        assert total['missing_data_count'] == 3
        assert total['directional_anomalies'] == 1
        assert total['batches_processed'] == 2
    
    @patch('ingestion.load_dataset')
    def test_stream_dataset(self, mock_load_dataset, pipeline):
        """Test streaming dataset loading."""
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter([{'a': 1}, {'a': 2}]))
        mock_load_dataset.return_value = mock_ds
        
        result = pipeline._stream_dataset('test_dataset', split='train', streaming=True)
        
        mock_load_dataset.assert_called_once_with(
            'test_dataset',
            name=None,
            split='train',
            streaming=True
        )
        
        rows = list(result)
        assert len(rows) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])