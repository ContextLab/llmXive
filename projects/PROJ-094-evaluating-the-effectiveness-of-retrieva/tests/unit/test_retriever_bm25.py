"""
Unit tests for the BM25 Retriever implementation.
"""

import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from src.models.retriever_bm25 import BM25Retriever, load_bm25_retriever, evaluate_retrieval
from src.data.models import CodeSnippet


@pytest.fixture
def sample_processed_data():
    """Create sample processed data for testing."""
    data = [
        {
            "id": "snippet_1",
            "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            "tokens": ["def", "fibonacci", "n", "return", "n", "if", "n", "<=", "1", "else", "fibonacci", "n", "-", "1", "+", "fibonacci", "n", "-", "2"]
        },
        {
            "id": "snippet_2",
            "code": "class HttpClient: def get(self, url): return requests.get(url)",
            "tokens": ["class", "HttpClient", "def", "get", "self", "url", "return", "requests", "get", "url"]
        },
        {
            "id": "snippet_3",
            "code": "def quicksort(arr): return sorted(arr)",
            "tokens": ["def", "quicksort", "arr", "return", "sorted", "arr"]
        },
        {
            "id": "snippet_4",
            "code": "def bubble_sort(arr): n = len(arr); for i in range(n): for j in range(0, n-i-1): if arr[j] > arr[j+1]: arr[j], arr[j+1] = arr[j+1], arr[j]",
            "tokens": ["def", "bubble_sort", "arr", "n", "=", "len", "arr", "for", "i", "in", "range", "n", "for", "j", "in", "range", "0", "n", "-", "i", "-", "1", "if", "arr", "j", ">", "arr", "j", "+", "1", "arr", "j", ",", "arr", "j", "+", "1", "=", "arr", "j", "+", "1", ",", "arr", "j"]
        }
    ]
    return data


@pytest.fixture
def temp_processed_file(sample_processed_data):
    """Create a temporary JSONL file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in sample_processed_data:
            f.write(json.dumps(item) + '\n')
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def temp_data_dir(temp_processed_file):
    """Create a temporary directory structure for testing."""
    data_dir = Path(temp_processed_file).parent
    train_file = data_dir / "train.jsonl"
    test_file = data_dir / "test.jsonl"
    Path(temp_processed_file).rename(train_file)
    # Create a copy for test
    with open(train_file, 'r') as src, open(test_file, 'w') as dst:
        dst.write(src.read())
    yield data_dir
    # Cleanup
    train_file.unlink()
    test_file.unlink()
    data_dir.rmdir()


class TestBM25Retriever:
    """Tests for the BM25Retriever class."""

    def test_initialization(self, sample_processed_data):
        """Test BM25Retriever initialization."""
        snippet_ids = [s["id"] for s in sample_processed_data]
        tokenized_corpus = [s["tokens"] for s in sample_processed_data]

        retriever = BM25Retriever(tokenized_corpus, snippet_ids)

        assert retriever.tokenized_corpus == tokenized_corpus
        assert retriever.snippet_ids == snippet_ids
        assert retriever.bm25 is not None

    def test_initialization_length_mismatch(self, sample_processed_data):
        """Test that initialization fails with mismatched lengths."""
        snippet_ids = [s["id"] for s in sample_processed_data[:2]]
        tokenized_corpus = [s["tokens"] for s in sample_processed_data]

        with pytest.raises(ValueError, match="must have the same length"):
            BM25Retriever(tokenized_corpus, snippet_ids)

    def test_retrieve(self, sample_processed_data):
        """Test retrieval functionality."""
        snippet_ids = [s["id"] for s in sample_processed_data]
        tokenized_corpus = [s["tokens"] for s in sample_processed_data]

        retriever = BM25Retriever(tokenized_corpus, snippet_ids)

        results = retriever.retrieve("fibonacci", top_k=2)

        assert len(results) <= 2
        assert all(isinstance(r, tuple) for r in results)
        assert all(isinstance(r[0], str) and isinstance(r[1], float) for r in results)
        # The fibonacci snippet should be ranked first
        assert results[0][0] == "snippet_1"

    def test_retrieve_zero_results(self, sample_processed_data):
        """Test retrieval with a query that matches nothing."""
        snippet_ids = [s["id"] for s in sample_processed_data]
        tokenized_corpus = [s["tokens"] for s in sample_processed_data]

        retriever = BM25Retriever(tokenized_corpus, snippet_ids)

        results = retriever.retrieve("nonexistentkeyword12345", top_k=5)

        # Should return empty or only snippets with very low scores
        assert isinstance(results, list)

    def test_save_and_load(self, sample_processed_data):
        """Test saving and loading the retriever."""
        snippet_ids = [s["id"] for s in sample_processed_data]
        tokenized_corpus = [s["tokens"] for s in sample_processed_data]

        retriever = BM25Retriever(tokenized_corpus, snippet_ids)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_index"
            retriever.save(save_path)

            assert (save_path / "bm25_index.pkl").exists()

            loaded_retriever = BM25Retriever.load(save_path)

            assert loaded_reverter.tokenized_corpus == retriever.tokenized_corpus
            assert loaded_retriever.snippet_ids == retriever.snippet_ids

    def test_save_missing_file(self, sample_processed_data):
        """Test loading from a non-existent path."""
        snippet_ids = [s["id"] for s in sample_processed_data]
        tokenized_corpus = [s["tokens"] for s in sample_processed_data]

        retriever = BM25Retriever(tokenized_corpus, snippet_ids)

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_path = Path(tmpdir) / "non_existent" / "index"

            with pytest.raises(FileNotFoundError):
                BM25Retriever.load(non_existent_path)


class TestLoadBM25Retriever:
    """Tests for the load_bm25_retriever function."""

    def test_load_from_temp_dir(self, temp_data_dir):
        """Test loading retriever from a temporary directory."""
        retriever = load_bm25_retriever(temp_data_dir, split="train")

        assert isinstance(retriever, BM25Retriever)
        assert len(retriever.snippet_ids) == 4

    def test_invalid_split(self, temp_data_dir):
        """Test loading with an invalid split."""
        with pytest.raises(ValueError, match="Invalid split"):
            load_bm25_retriever(temp_data_dir, split="invalid")

    def test_missing_data_file(self, temp_data_dir):
        """Test loading when data file is missing."""
        missing_dir = temp_data_dir / "missing"
        missing_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            load_bm25_retriever(missing_dir, split="train")

    def test_cache_loading(self, temp_data_dir):
        """Test loading from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # First load (creates cache)
            retriever1 = load_bm25_retriever(temp_data_dir, split="train", cache_dir=cache_dir)

            # Second load (should use cache)
            retriever2 = load_bm25_retriever(temp_data_dir, split="train", cache_dir=cache_dir)

            assert len(retriever1.snippet_ids) == len(retriever2.snippet_ids)


class TestEvaluateRetrieval:
    """Tests for the evaluate_retrieval function."""

    def test_evaluate_basic(self, temp_data_dir):
        """Test basic evaluation functionality."""
        retriever = load_bm25_retriever(temp_data_dir, split="train")

        queries = [
            {
                "id": "q1",
                "query": "fibonacci",
                "ground_truth_ids": ["snippet_1"]
            },
            {
                "id": "q2",
                "query": "http client",
                "ground_truth_ids": ["snippet_2"]
            }
        ]

        metrics = evaluate_retrieval(retriever, queries, k_values=[1, 2])

        assert "p@1" in metrics
        assert "p@2" in metrics
        assert "r@1" in metrics
        assert "r@2" in metrics
        assert "ndcg@1" in metrics
        assert "ndcg@2" in metrics

        # Check that metrics are between 0 and 1
        for k in [1, 2]:
            assert 0 <= metrics[f"p@{k}"] <= 1
            assert 0 <= metrics[f"r@{k}"] <= 1
            assert 0 <= metrics[f"ndcg@{k}"] <= 1

    def test_evaluate_empty_ground_truth(self, temp_data_dir):
        """Test evaluation with empty ground truth."""
        retriever = load_bm25_retriever(temp_data_dir, split="train")

        queries = [
            {
                "id": "q1",
                "query": "fibonacci",
                "ground_truth_ids": []
            }
        ]

        metrics = evaluate_retrieval(retriever, queries, k_values=[1])

        # Should return 0 for all metrics
        assert metrics["p@1"] == 0.0
        assert metrics["r@1"] == 0.0
        assert metrics["ndcg@1"] == 0.0

    def test_evaluate_no_matches(self, temp_data_dir):
        """Test evaluation when no results match."""
        retriever = load_bm25_retriever(temp_data_dir, split="train")

        queries = [
            {
                "id": "q1",
                "query": "nonexistentkeyword123",
                "ground_truth_ids": ["snippet_1"]
            }
        ]

        metrics = evaluate_retrieval(retriever, queries, k_values=[1])

        # Should return 0 for all metrics
        assert metrics["p@1"] == 0.0
        assert metrics["r@1"] == 0.0
        assert metrics["ndcg@1"] == 0.0