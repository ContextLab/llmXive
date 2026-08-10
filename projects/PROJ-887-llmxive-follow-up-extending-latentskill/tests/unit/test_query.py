"""
Unit tests for the query module.

Tests FR-002 implementation: Query vector generation with latency measurement.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.query import (
    load_embedding_model,
    generate_query_vector,
    generate_query_vectors_batch,
    save_query_results,
    MODEL_NAME
)

class TestLoadEmbeddingModel:
    """Tests for load_embedding_model function."""
    
    @patch('src.retrieval.query.SentenceTransformer')
    def test_load_model_success(self, mock_sentence_transformer):
        """Test successful model loading."""
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model = load_embedding_model(cache_dir=Path(tmpdir))
            
            mock_sentence_transformer.assert_called_once()
            assert model == mock_model
            mock_model.get_sentence_embedding_dimension.assert_called_once()
    
    @patch('src.retrieval.query.SentenceTransformer')
    def test_load_model_creates_cache_dir(self, mock_sentence_transformer):
        """Test that cache directory is created."""
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "nonexistent" / "subdir"
            load_embedding_model(cache_dir=cache_path)
            
            assert cache_path.exists()
            
            # Verify the cache_dir was passed correctly
            call_args = mock_sentence_transformer.call_args
            assert call_args[1]['cache_folder'] == str(cache_path)


class TestGenerateQueryVector:
    """Tests for generate_query_vector function."""
    
    @patch('src.retrieval.query.SentenceTransformer')
    def test_generate_single_vector(self, mock_sentence_transformer):
        """Test generating a single query vector."""
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(to_list=lambda: [0.1, 0.2, 0.3])
        mock_sentence_transformer.return_value = mock_model
        
        model = MagicMock()
        model.encode.return_value = MagicMock(to_list=lambda: [0.1, 0.2, 0.3])
        
        embedding, latency = generate_query_vector(model, "test query")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]
        assert latency >= 0
    
    @patch('src.retrieval.query.SentenceTransformer')
    def test_generate_vector_no_latency(self, mock_sentence_transformer):
        """Test generating vector without latency measurement."""
        model = MagicMock()
        model.encode.return_value = MagicMock(to_list=lambda: [0.1, 0.2, 0.3])
        
        embedding, latency = generate_query_vector(model, "test query", log_latency=False)
        
        assert latency == 0.0


class TestGenerateQueryVectorsBatch:
    """Tests for generate_query_vectors_batch function."""
    
    def test_generate_batch(self):
        """Test generating embeddings for multiple texts."""
        model = MagicMock()
        
        # Mock encode to return embeddings for 3 texts
        mock_embeddings = [
            MagicMock(to_list=lambda: [0.1, 0.2]),
            MagicMock(to_list=lambda: [0.3, 0.4]),
            MagicMock(to_list=lambda: [0.5, 0.6])
        ]
        model.encode.return_value = mock_embeddings
        
        texts = ["text1", "text2", "text3"]
        embeddings, latencies = generate_query_vectors_batch(model, texts)
        
        assert len(embeddings) == 3
        assert len(latencies) == 3
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(lat >= 0 for lat in latencies)
    
    def test_generate_batch_empty_list(self):
        """Test handling of empty input list."""
        model = MagicMock()
        
        embeddings, latencies = generate_query_vectors_batch(model, [])
        
        assert len(embeddings) == 0
        assert len(latencies) == 0


class TestSaveQueryResults:
    """Tests for save_query_results function."""
    
    def test_save_results(self):
        """Test saving query results to JSON."""
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["query1", "query2"]
        latencies = [0.1, 0.2]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            
            save_query_results(embeddings, texts, latencies, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['total_queries'] == 2
            assert data['avg_latency'] == pytest.approx(0.15)
            assert len(data['results']) == 2
            assert data['results'][0]['text'] == "query1"
            assert data['results'][0]['latency_seconds'] == 0.1
    
    def test_save_results_with_metadata(self):
        """Test saving results with additional metadata."""
        embeddings = [[0.1]]
        texts = ["query"]
        latencies = [0.1]
        metadata = {"custom_field": "value"}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            
            save_query_results(embeddings, texts, latencies, output_path, metadata)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['metadata'] == {"custom_field": "value"}
    
    def test_save_results_creates_directory(self):
        """Test that save creates parent directories."""
        embeddings = [[0.1]]
        texts = ["query"]
        latencies = [0.1]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deep" / "nested" / "results.json"
            
            save_query_results(embeddings, texts, latencies, output_path)
            
            assert output_path.exists()


class TestIntegration:
    """Integration tests for the query module."""
    
    @patch('src.retrieval.query.SentenceTransformer')
    def test_full_workflow(self, mock_sentence_transformer):
        """Test the full workflow from model loading to saving results."""
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = [
            MagicMock(to_list=lambda: [0.1, 0.2, 0.3]),
            MagicMock(to_list=lambda: [0.4, 0.5, 0.6])
        ]
        mock_sentence_transformer.return_value = mock_model
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_path = Path(tmpdir) / "output.json"
            queries = ["test1", "test2"]
            
            # Load model
            model = load_embedding_model(cache_dir=cache_dir)
            
            # Generate embeddings
            embeddings, latencies = generate_query_vectors_batch(model, queries)
            
            # Save results
            save_query_results(embeddings, queries, latencies, output_path)
            
            # Verify output
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['total_queries'] == 2
            assert len(data['results']) == 2