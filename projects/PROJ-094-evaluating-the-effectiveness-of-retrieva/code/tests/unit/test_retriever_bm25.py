"""
Unit tests for the BM25 Retriever implementation.
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.models.retriever_bm25 import BM25Retriever, load_bm25_retriever, evaluate_retrieval
from src.data.models import CodeSnippet


@pytest.fixture
def sample_processed_data():
    """Create a temporary JSONL file with sample code snippets."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        snippets = [
            CodeSnippet(id="1", text="def sort_list(arr): return sorted(arr)", language="python", repo="test", ground_truth=[]),
            CodeSnippet(id="2", text="def read_file(path): with open(path) as f: return f.read()", language="python", repo="test", ground_truth=[]),
            CodeSnippet(id="3", text="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)", language="python", repo="test", ground_truth=[]),
            CodeSnippet(id="4", text="public class Sort { public static void sort(int[] arr) { } }", language="java", repo="test", ground_truth=[]),
            CodeSnippet(id="5", text="function readfile(path) { return fs.readFileSync(path); }", language="javascript", repo="test", ground_truth=[])
        ]
        for snippet in snippets:
            f.write(json.dumps({
                'id': snippet.id,
                'text': snippet.text,
                'language': snippet.language,
                'repo': snippet.repo,
                'ground_truth': snippet.ground_truth
            }) + '\n')
    return Path(f.name)


class TestBM25Retriever:
    """Tests for the BM25Retriever class."""

    def test_initialization(self, sample_processed_data):
        """Test that the retriever can be initialized."""
        retriever = BM25Retriever(
            snippets=[
                CodeSnippet(id="1", text="def sort_list(arr): return sorted(arr)", language="python", repo="test", ground_truth=[]),
                CodeSnippet(id="2", text="def read_file(path): with open(path) as f: return f.read()", language="python", repo="test", ground_truth=[])
            ]
        )
        assert retriever.bm25_index is not None
        assert len(retriever.snippets) == 2

    def test_retrieve_returns_results(self, sample_processed_data):
        """Test that retrieval returns non-empty results."""
        retriever = load_bm25_retriever(sample_processed_data)
        results = retriever.retrieve("sort list", top_k=5)
        assert len(results) > 0
        assert all(isinstance(score, float) for _, score in results)

    def test_retrieve_respects_top_k(self, sample_processed_data):
        """Test that retrieval respects the top_k parameter."""
        retriever = load_bm25_retriever(sample_processed_data)
        results_5 = retriever.retrieve("sort", top_k=5)
        results_3 = retriever.retrieve("sort", top_k=3)
        assert len(results_5) <= 5
        assert len(results_3) <= 3
        assert len(results_3) <= len(results_5)

    def test_save_and_load_index(self, sample_processed_data):
        """Test that the index can be saved and loaded."""
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            index_path = Path(f.name)

        retriever = load_bm25_retriever(sample_processed_data, index_path)
        assert index_path.exists()

        # Load the index
        loaded_retriever = BM25Retriever.load_index(index_path)
        assert loaded_retriever.bm25_index is not None
        assert len(loaded_retriever.snippets) == len(retriever.snippets)


class TestLoadBM25Retriever:
    """Tests for the load_bm25_retriever function."""

    def test_load_from_jsonl(self, sample_processed_data):
        """Test loading from a JSONL file."""
        retriever = load_bm25_retriever(sample_processed_data)
        assert retriever.bm25_index is not None
        assert len(retriever.snippets) == 5

    def test_load_creates_index(self, sample_processed_data):
        """Test that loading creates the BM25 index."""
        retriever = load_bm25_retriever(sample_processed_data)
        assert retriever.bm25_index is not None


class TestEvaluateRetrieval:
    """Tests for the evaluate_retrieval function."""

    def test_evaluate_returns_metrics(self, sample_processed_data):
        """Test that evaluation returns the expected metrics."""
        retriever = load_bm25_retriever(sample_processed_data)
        queries = ["sort list", "read file", "fibonacci"]
        ground_truth = {
            "query_0": ["1"],
            "query_1": ["2"],
            "query_2": ["3"]
        }

        results = evaluate_retrieval(retriever, queries, ground_truth, k_values=[5, 10])

        assert "P@5" in results
        assert "P@10" in results
        assert "R@5" in results
        assert "R@10" in results
        assert "nDCG@5" in results
        assert "nDCG@10" in results

    def test_evaluate_handles_empty_ground_truth(self, sample_processed_data):
        """Test that evaluation handles empty ground truth gracefully."""
        retriever = load_bm25_retriever(sample_processed_data)
        queries = ["sort list"]
        ground_truth = {"query_0": []}

        results = evaluate_retrieval(retriever, queries, ground_truth, k_values=[5])

        assert results["P@5"] == 0.0
        assert results["R@5"] == 0.0
        assert results["nDCG@5"] == 0.0