"""
Unit tests for the streaming loader module.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.data.streaming_loader import (
    StreamingStats,
    load_batch,
    load_dataset_streaming,
    compute_online_statistics
)
from src.data.ingestion import ReactionRecord


class TestStreamingStats:
    """Tests for StreamingStats class."""

    def test_initialization(self):
        """Test that stats initialize correctly."""
        stats = StreamingStats()
        assert stats.count == 0
        assert stats.sum_rate == 0.0
        assert stats.sum_pka == 0.0
        assert stats.min_rate == float('inf')
        assert stats.max_rate == float('-inf')

    def test_update_single_value(self):
        """Test updating with a single value."""
        stats = StreamingStats()
        stats.update(1.0, 10.0)
        
        assert stats.count == 1
        assert stats.sum_rate == 1.0
        assert stats.sum_pka == 10.0
        assert stats.mean_rate == 1.0
        assert stats.mean_pka == 10.0

    def test_update_multiple_values(self):
        """Test updating with multiple values."""
        stats = StreamingStats()
        stats.update(1.0, 10.0)
        stats.update(2.0, 20.0)
        stats.update(3.0, 30.0)
        
        assert stats.count == 3
        assert stats.mean_rate == 2.0
        assert stats.mean_pka == 20.0
        assert abs(stats.std_rate - 1.0) < 0.01
        assert abs(stats.std_pka - 10.0) < 0.01

    def test_min_max_tracking(self):
        """Test that min and max are tracked correctly."""
        stats = StreamingStats()
        stats.update(1.0, 10.0)
        stats.update(5.0, 50.0)
        stats.update(3.0, 30.0)
        
        assert stats.min_rate == 1.0
        assert stats.max_rate == 5.0
        assert stats.min_pka == 10.0
        assert stats.max_pka == 50.0

    def test_zero_count_statistics(self):
        """Test that statistics handle zero count gracefully."""
        stats = StreamingStats()
        assert stats.mean_rate == 0.0
        assert stats.mean_pka == 0.0
        assert stats.std_rate == 0.0
        assert stats.std_pka == 0.0

class TestLoadBatch:
    """Tests for load_batch function."""

    def test_invalid_source(self):
        """Test that invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid source"):
            list(load_batch(source="invalid"))

    @patch('src.data.streaming_loader._load_chembl_streaming')
    def test_load_batch_yields_correct_structure(self, mock_loader):
        """Test that load_batch yields correct structure."""
        # Create mock records
        mock_records = [
            ReactionRecord(
                smiles="CCN",
                normalized_rate=1.0,
                pka=10.0,
                temperature=298.0,
                ea=50.0,
                source="chembl"
            )
            for _ in range(5)
        ]
        
        mock_loader.return_value = iter(mock_records)
        
        batches = list(load_batch(source="chembl", batch_size=2))
        
        assert len(batches) == 3  # 2 full batches + 1 partial
        assert len(batches[0][0]) == 2
        assert len(batches[1][0]) == 2
        assert len(batches[2][0]) == 1
        
        # Check stats accumulation
        assert batches[0][1].count == 2
        assert batches[1][1].count == 4
        assert batches[2][1].count == 5

    @patch('src.data.streaming_loader._load_chembl_streaming')
    def test_load_batch_statistics_accuracy(self, mock_loader):
        """Test that statistics are accumulated correctly."""
        mock_records = [
            ReactionRecord(
                smiles=f"C{i}",
                normalized_rate=float(i),
                pka=float(i * 10),
                temperature=298.0,
                ea=50.0,
                source="chembl"
            )
            for i in range(1, 6)  # 1, 2, 3, 4, 5
        ]
        
        mock_loader.return_value = iter(mock_records)
        
        batches = list(load_batch(source="chembl", batch_size=3))
        
        # Final batch should have correct statistics
        final_batch, final_stats = batches[-1]
        assert final_stats.count == 5
        assert final_stats.mean_rate == 3.0  # (1+2+3+4+5)/5
        assert final_stats.mean_pka == 30.0  # (10+20+30+40+50)/5

class TestLoadDatasetStreaming:
    """Tests for load_dataset_streaming function."""

    @patch('src.data.streaming_loader.load_batch')
    def test_load_dataset_streaming_yields_individual_records(self, mock_load_batch):
        """Test that load_dataset_streaming yields individual records."""
        mock_batch1 = [
            ReactionRecord(smiles="C1", normalized_rate=1.0, pka=10.0, temperature=298.0, ea=50.0, source="chembl"),
            ReactionRecord(smiles="C2", normalized_rate=2.0, pka=20.0, temperature=298.0, ea=50.0, source="chembl"),
        ]
        mock_batch2 = [
            ReactionRecord(smiles="C3", normalized_rate=3.0, pka=30.0, temperature=298.0, ea=50.0, source="chembl"),
        ]
        mock_stats = MagicMock()
        
        mock_load_batch.return_value = iter([
            (mock_batch1, mock_stats),
            (mock_batch2, mock_stats),
        ])
        
        records = list(load_dataset_streaming(source="chembl", batch_size=2))
        
        assert len(records) == 3
        assert records[0].smiles == "C1"
        assert records[1].smiles == "C2"
        assert records[2].smiles == "C3"

    @patch('src.data.streaming_loader.load_batch')
    def test_load_dataset_streaming_max_records(self, mock_load_batch):
        """Test that max_records parameter limits output."""
        mock_batch = [
            ReactionRecord(smiles=f"C{i}", normalized_rate=float(i), pka=float(i*10), temperature=298.0, ea=50.0, source="chembl")
            for i in range(1, 11)
        ]
        mock_stats = MagicMock()
        
        mock_load_batch.return_value = iter([(mock_batch, mock_stats)])
        
        records = list(load_dataset_streaming(source="chembl", batch_size=10, max_records=3))
        
        assert len(records) == 3

class TestComputeOnlineStatistics:
    """Tests for compute_online_statistics function."""

    @patch('src.data.streaming_loader.load_batch')
    def test_compute_online_statistics_returns_complete_stats(self, mock_load_batch):
        """Test that compute_online_statistics returns complete statistics."""
        mock_batch = [
            ReactionRecord(smiles=f"C{i}", normalized_rate=float(i), pka=float(i*10), temperature=298.0, ea=50.0, source="chembl")
            for i in range(1, 6)
        ]
        mock_stats = MagicMock()
        mock_stats.count = 5
        mock_stats.mean_rate = 3.0
        mock_stats.mean_pka = 30.0
        
        mock_load_batch.return_value = iter([(mock_batch, mock_stats)])
        
        result = compute_online_statistics(source="chembl", batch_size=5)
        
        # The function returns the last batch_stats object
        assert result.count == 5
        assert result.mean_rate == 3.0
        assert result.mean_pka == 30.0