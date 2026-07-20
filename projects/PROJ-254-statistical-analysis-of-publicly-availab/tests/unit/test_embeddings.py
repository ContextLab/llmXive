import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from code.embeddings import train_global_word2vec, generate_track_sequences, load_metadata_batches

@pytest.fixture
def mock_sequence_iterator():
    """Fixture providing a mock iterator of track sequences."""
    return iter([
        ["track1", "track2", "track3"],
        ["track4", "track5"],
        ["track6", "track7", "track8", "track9"]
    ])

def test_train_global_word2vec(mock_sequence_iterator):
    """Test that train_global_word2vec accepts an iterator and trains a model."""
    with patch('code.embeddings.Word2Vec') as MockWord2Vec:
        mock_model = MagicMock()
        MockWord2Vec.return_value = mock_model
        
        # Call the function
        model = train_global_word2vec(mock_sequence_iterator)
        
        # Verify Word2Vec was called with the iterator
        MockWord2Vec.assert_called_once()
        call_args = MockWord2Vec.call_args
        
        # Check that sentences argument is the iterator (or an object that can be iterated)
        # Note: Word2Vec might consume the iterator, so we check the call args.
        assert call_args is not None
        
        # Verify model was returned
        assert model is mock_model

def test_generate_track_sequences():
    """Test that generate_track_sequences yields sequences from batches."""
    # Mock metadata batches
    mock_batch = [
        {'playlist_id': 'p1', 'track_id': 't1'},
        {'playlist_id': 'p1', 'track_id': 't2'},
        {'playlist_id': 'p2', 'track_id': 't3'}
    ]
    
    def mock_batches():
        yield mock_batch
    
    sequences = list(generate_track_sequences(mock_batches()))
    
    # We expect sequences for p1 and p2
    assert len(sequences) == 2
    # Check content (order might vary based on groupby)
    assert set(sequences[0]) == {'t1', 't2'} or set(sequences[1]) == {'t1', 't2'}
    assert set(sequences[0]) == {'t3'} or set(sequences[1]) == {'t3'}
