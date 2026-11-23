"""
Unit tests for the Neural Retriever implementation.
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.models.retriever_neural import NeuralRetriever, load_neural_retriever, evaluate_retrieval
from src.data.models import CodeSnippet


@pytest.fixture
def sample_snippets():
    """Create sample code snippets for testing."""
    return [
        CodeSnippet(
            id="1",
            language="python",
            text="def hello_world():\n    print('Hello, World!')",
            url="https://example.com/1",
            docstring="Prints a greeting"
        ),
        CodeSnippet(
            id="2",
            language="python",
            text="def add(a, b):\n    return a + b",
            url="https://example.com/2",
            docstring="Adds two numbers"
        ),
        CodeSnippet(
            id="3",
            language="python",
            text="def multiply(a, b):\n    return a * b",
            url="https://example.com/3",
            docstring="Multiplies two numbers"
        ),
        CodeSnippet(
            id="4",
            language="java",
            text="public class Calculator {\n    public int add(int a, int b) {\n        return a + b;\n    }\n}",
            url="https://example.com/4",
            docstring="Java calculator class"
        )
    ]


@pytest.fixture
def mock_sentence_transformers():
    """Mock the SentenceTransformer class to avoid actual model loading."""
    with patch('src.models.retriever_neural.SentenceTransformer') as mock_cls:
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Mock the encode method to return deterministic embeddings
        def mock_encode(texts, convert_to_numpy=False, show_progress_bar=False):
            # Return embeddings based on text length to have some variation
            embeddings = []
            for text in texts:
                # Create a simple embedding based on text content
                emb = np.random.RandomState(hash(text) % (2**32)).rand(384).astype(np.float32)
                embeddings.append(emb)
            result = np.array(embeddings)
            if convert_to_numpy:
                return result
            return result.tolist()
        
        mock_instance.encode.side_effect = mock_encode
        mock_cls.return_value = mock_instance
        yield mock_cls


class TestNeuralRetriever:
    """Tests for the NeuralRetriever class."""

    def test_init(self, mock_sentence_transformers):
        """Test initialization of NeuralRetriever."""
        retriever = NeuralRetriever(
            model_name="test-model",
            device="cpu",
            max_batch_size=16
        )
        assert retriever.model_name == "test-model"
        assert retriever.device == "cpu"
        assert retriever.max_batch_size == 16
        assert retriever.model is not None

    def test_index_snippets(self, mock_sentence_transformers, sample_snippets):
        """Test indexing of code snippets."""
        retriever = NeuralRetriever(device="cpu")
        retriever.index_snippets(sample_snippets)
        
        assert retriever.snippet_embeddings is not None
        assert retriever.snippet_embeddings.shape[0] == len(sample_snippets)
        assert len(retriever.snippets) == len(sample_snippets)

    def test_retrieve_without_index(self, mock_sentence_transformers):
        """Test that retrieval fails without indexed snippets."""
        retriever = NeuralRetriever(device="cpu")
        with pytest.raises(ValueError, match="No snippets indexed"):
            retriever.retrieve("test query")

    def test_retrieve(self, mock_sentence_transformers, sample_snippets):
        """Test retrieval of top-k snippets."""
        retriever = NeuralRetriever(device="cpu")
        retriever.index_snippets(sample_snippets)
        
        results = retriever.retrieve("addition function", top_k=2)
        
        assert len(results) == 2
        assert all(isinstance(r[0], CodeSnippet) for r in results)
        assert all(isinstance(r[1], float) for r in results)
        # Scores should be between -1 and 1 for cosine similarity
        assert all(-1 <= r[1] <= 1 for r in results)

    def test_retrieve_batch(self, mock_sentence_transformers, sample_snippets):
        """Test batch retrieval."""
        retriever = NeuralRetriever(device="cpu")
        retriever.index_snippets(sample_snippets)
        
        queries = ["addition", "multiplication", "greeting"]
        results = retriever.retrieve_batch(queries, top_k=1)
        
        assert len(results) == len(queries)
        assert all(len(r) == 1 for r in results)

    def test_save_and_load_index(self, mock_sentence_transformers, sample_snippets):
        """Test saving and loading an index."""
        retriever = NeuralRetriever(device="cpu")
        retriever.index_snippets(sample_snippets)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index"
            retriever.save_index(index_path)
            
            # Verify files were created
            assert (index_path / "embeddings.npy").exists()
            assert (index_path / "snippets.json").exists()
            assert (index_path / "config.json").exists()
            
            # Load the index
            loaded_retriever = NeuralRetriever.load_index(index_path)
            
            assert loaded_retriever.model_name == retriever.model_name
            assert len(loaded_retriever.snippets) == len(retriever.snippets)
            assert np.allclose(
                loaded_retriever.snippet_embeddings,
                retriever.snippet_embeddings
            )


class TestLoadNeuralRetriever:
    """Tests for the load_neural_retriever function."""

    def test_load_neural_retriever(self, mock_sentence_transformers, sample_snippets):
        """Test the convenience function for creating a retriever."""
        retriever = load_neural_retriever(
            snippets=sample_snippets,
            model_name="test-model",
            device="cpu"
        )
        
        assert retriever.model_name == "test-model"
        assert retriever.snippet_embeddings is not None
        assert len(retriever.snippets) == len(sample_snippets)


class TestEvaluateRetrieval:
    """Tests for the evaluate_retrieval function."""

    def test_evaluate_retrieval(self, mock_sentence_transformers, sample_snippets):
        """Test evaluation of retrieval performance."""
        retriever = NeuralRetriever(device="cpu")
        retriever.index_snippets(sample_snippets)
        
        queries = ["addition function", "multiplication"]
        ground_truth = [
            [sample_snippets[1]],  # "add" snippet
            [sample_snippets[2]]   # "multiply" snippet
        ]
        
        metrics = evaluate_retrieval(
            retriever=retriever,
            queries=queries,
            ground_truth=ground_truth,
            top_k=2
        )
        
        assert metrics["method"] == "neural"
        assert "hits_at_k" in metrics
        assert "recall_at_k" in metrics
        assert "precision_at_k" in metrics
        assert metrics["num_queries"] == len(queries)
        assert 0 <= metrics["hits_at_k"] <= 1
        assert 0 <= metrics["recall_at_k"] <= 1
        assert 0 <= metrics["precision_at_k"] <= 1

    def test_evaluate_with_empty_ground_truth(self, mock_sentence_transformers, sample_snippets):
        """Test evaluation with empty ground truth."""
        retriever = NeuralRetriever(device="cpu")
        retriever.index_snippets(sample_snippets)
        
        queries = ["test query"]
        ground_truth = [[]]  # Empty ground truth
        
        metrics = evaluate_retrieval(
            retriever=retriever,
            queries=queries,
            ground_truth=ground_truth,
            top_k=1
        )
        
        # Recall should be 0 when ground truth is empty
        assert metrics["recall_at_k"] == 0.0
