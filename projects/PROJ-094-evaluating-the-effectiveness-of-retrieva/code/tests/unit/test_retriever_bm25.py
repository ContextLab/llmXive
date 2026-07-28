"""
Unit tests for the BM25 retriever implementation.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.models.retriever_bm25 import BM25Retriever, load_bm25_retriever, evaluate_retrieval
from src.data.models import CodeSnippet


@pytest.fixture
def sample_processed_data(tmp_path):
    """Create sample processed data for testing."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    # Create a sample JSONL file
    jsonl_file = processed_dir / "test_data.jsonl"
    snippets = [
        {
            "id": "snippet_1",
            "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "language": "python",
            "repository": "test_repo",
            "docstring": "Calculate fibonacci number"
        },
        {
            "id": "snippet_2",
            "code": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)",
            "language": "python",
            "repository": "test_repo",
            "docstring": "Calculate factorial"
        },
        {
            "id": "snippet_3",
            "code": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]",
            "language": "python",
            "repository": "test_repo",
            "docstring": "Sort array using bubble sort"
        }
    ]

    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for snippet in snippets:
            f.write(json.dumps(snippet) + '\n')

    return processed_dir


class TestBM25Retriever:
    """Tests for the BM25Retriever class."""

    def test_init(self, sample_processed_data):
        """Test initialization of BM25Retriever."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)
        assert retriever.processed_data_path == sample_processed_data
        assert len(retriever.snippets) == 0
        assert retriever.bm25_index is None

    def test_load_processed_data(self, sample_processed_data):
        """Test loading of processed data."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)
        retriever._load_processed_data()

        assert len(retriever.snippets) == 3
        assert retriever.snippet_ids == ["snippet_1", "snippet_2", "snippet_3"]
        assert retriever.snippets[0].language == "python"

    def test_build_index(self, sample_processed_data):
        """Test building the BM25 index."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)
        retriever.build_index()

        assert retriever.bm25_index is not None
        assert len(retriever.tokenized_corpus) == 3

    def test_retrieve(self, sample_processed_data):
        """Test retrieval functionality."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)
        retriever.build_index()

        results = retriever.retrieve("fibonacci", k=2)

        assert len(results) > 0
        # The fibonacci snippet should be in the top results
        snippet_ids = [r.snippet_id for r in results]
        assert "snippet_1" in snippet_ids

    def test_retrieve_empty_query(self, sample_processed_data):
        """Test retrieval with empty query."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)
        retriever.build_index()

        results = retriever.retrieve("", k=2)
        assert len(results) == 0

    def test_retrieve_non_existent_path(self, tmp_path):
        """Test retrieval with non-existent data path."""
        retriever = BM25Retriever(str(tmp_path / "non_existent"), seed=42)

        with pytest.raises(FileNotFoundError):
            retriever.build_index()

    def test_retrieve_no_jsonl_files(self, tmp_path):
        """Test retrieval when no JSONL files exist."""
        data_dir = tmp_path / "processed"
        data_dir.mkdir()

        retriever = BM25Retriever(str(data_dir), seed=42)

        with pytest.raises(ValueError):
            retriever.build_index()

    def test_retrieve_batch(self, sample_processed_data):
        """Test batch retrieval."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)
        retriever.build_index()

        queries = ["fibonacci", "factorial"]
        results = retriever.retrieve_batch(queries, k=2)

        assert len(results) == 2
        assert "fibonacci" in results
        assert "factorial" in results
        assert len(results["fibonacci"]) > 0
        assert len(results["factorial"]) > 0

    def test_retrieve_without_build_index(self, sample_processed_data):
        """Test retrieval without building index first."""
        retriever = BM25Retriever(str(sample_processed_data), seed=42)

        with pytest.raises(RuntimeError):
            retriever.retrieve("test query")


class TestLoadBM25Retriever:
    """Tests for the load_bm25_retriever factory function."""

    def test_load_bm25_retriever(self, sample_processed_data):
        """Test loading a BM25 retriever."""
        retriever = load_bm25_retriever(str(sample_processed_data), seed=42)

        assert retriever is not None
        assert retriever.bm25_index is not None

    def test_load_bm25_retriever_force_rebuild(self, sample_processed_data):
        """Test loading with force rebuild."""
        retriever = load_bm25_retriever(
            str(sample_processed_data),
            seed=42,
            force_rebuild=True
        )

        assert retriever is not None
        assert retriever.bm25_index is not None


class TestEvaluateRetrieval:
    """Tests for the evaluate_retrieval function."""

    def test_evaluate_retrieval(self, sample_processed_data):
        """Test retrieval evaluation."""
        retriever = load_bm25_retriever(str(sample_processed_data), seed=42)

        queries = [
            {
                "query": "fibonacci",
                "relevant_ids": ["snippet_1"]
            },
            {
                "query": "factorial",
                "relevant_ids": ["snippet_2"]
            }
        ]

        metrics = evaluate_retrieval(retriever, queries, k_values=[1, 2])

        assert metrics is not None
        assert "num_queries" in metrics
        assert metrics["num_queries"] == 2

        # Check that metrics were calculated for k=1 and k=2
        for k in [1, 2]:
            for metric in ["precision", "recall", "ndcg"]:
                key = f"method_bm25_k{k}_{metric}"
                assert key in metrics