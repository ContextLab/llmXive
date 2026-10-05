import pytest
from src.data.models import RetrievalMethod, CodeSnippet, QueryResult, PerformanceDelta


class TestRetrievalMethod:
    """Tests for the RetrievalMethod enum."""
    
    def test_retrieval_method_values(self):
        """Test that enum values are correct."""
        assert RetrievalMethod.BM25.value == "bm25"
        assert RetrievalMethod.NEURAL.value == "neural"
        assert RetrievalMethod.RAG.value == "rag"
    
    def test_retrieval_method_from_string(self):
        """Test creating enum from string value."""
        assert RetrievalMethod("bm25") == RetrievalMethod.BM25
        assert RetrievalMethod("neural") == RetrievalMethod.NEURAL
        assert RetrievalMethod("rag") == RetrievalMethod.RAG


class TestCodeSnippet:
    """Tests for the CodeSnippet dataclass."""
    
    def test_create_snippet(self):
        """Test creating a CodeSnippet instance."""
        snippet = CodeSnippet(
            id="test-1",
            repo="test/repo",
            path="file.py",
            language="python",
            code="def hello(): pass",
            docstring="A hello function"
        )
        assert snippet.id == "test-1"
        assert snippet.repo == "test/repo"
        assert snippet.code == "def hello(): pass"
    
    def test_snippet_with_tokens(self):
        """Test creating a CodeSnippet with tokens."""
        snippet = CodeSnippet(
            id="test-2",
            repo="test/repo",
            path="file.py",
            language="python",
            code="def hello(): pass",
            docstring="A hello function",
            tokens=["def", "hello", "(", ")", ":", "pass"]
        )
        assert snippet.tokens == ["def", "hello", "(", ")", ":", "pass"]
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        snippet = CodeSnippet(
            id="test-3",
            repo="test/repo",
            path="file.py",
            language="python",
            code="def hello(): pass",
            docstring="A hello function",
            tokens=["def", "hello"]
        )
        data = snippet.to_dict()
        assert data["id"] == "test-3"
        assert data["tokens"] == ["def", "hello"]
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test-4",
            "repo": "test/repo",
            "path": "file.py",
            "language": "python",
            "code": "def hello(): pass",
            "docstring": "A hello function",
            "tokens": ["def", "hello"]
        }
        snippet = CodeSnippet.from_dict(data)
        assert snippet.id == "test-4"
        assert snippet.tokens == ["def", "hello"]
    
    def test_round_trip(self):
        """Test serialization and deserialization round-trip."""
        original = CodeSnippet(
            id="test-5",
            repo="test/repo",
            path="file.py",
            language="python",
            code="def hello(): pass",
            docstring="A hello function",
            tokens=["def", "hello"]
        )
        data = original.to_dict()
        restored = CodeSnippet.from_dict(data)
        assert original.id == restored.id
        assert original.code == restored.code
        assert original.tokens == restored.tokens


class TestQueryResult:
    """Tests for the QueryResult dataclass."""
    
    def test_create_query_result(self):
        """Test creating a QueryResult instance."""
        result = QueryResult(
            query_id="q-1",
            method=RetrievalMethod.BM25,
            ground_truth_ids=["s-1", "s-2"]
        )
        assert result.query_id == "q-1"
        assert result.method == RetrievalMethod.BM25
        assert len(result.retrieved_snippets) == 0
    
    def test_add_retrieved_snippet(self):
        """Test adding retrieved snippets."""
        snippet = CodeSnippet(
            id="s-1",
            repo="test/repo",
            path="file.py",
            language="python",
            code="def hello(): pass",
            docstring="A hello function"
        )
        result = QueryResult(
            query_id="q-1",
            method=RetrievalMethod.BM25,
            retrieved_snippets=[snippet],
            retrieved_scores=[0.95]
        )
        assert len(result.retrieved_snippets) == 1
        assert result.retrieved_scores == [0.95]
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        snippet = CodeSnippet(
            id="s-1",
            repo="test/repo",
            path="file.py",
            language="python",
            code="def hello(): pass",
            docstring="A hello function"
        )
        result = QueryResult(
            query_id="q-1",
            method=RetrievalMethod.BM25,
            retrieved_snippets=[snippet],
            retrieved_scores=[0.95],
            ground_truth_ids=["s-1"],
            metrics={"ndcg@10": 0.95},
            execution_time_ms=10.5
        )
        data = result.to_dict()
        assert data["query_id"] == "q-1"
        assert data["method"] == "bm25"
        assert len(data["retrieved_snippets"]) == 1
        assert data["metrics"]["ndcg@10"] == 0.95
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "query_id": "q-1",
            "method": "bm25",
            "retrieved_snippets": [
                {
                    "id": "s-1",
                    "repo": "test/repo",
                    "path": "file.py",
                    "language": "python",
                    "code": "def hello(): pass",
                    "docstring": "A hello function"
                }
            ],
            "retrieved_scores": [0.95],
            "ground_truth_ids": ["s-1"],
            "metrics": {"ndcg@10": 0.95},
            "execution_time_ms": 10.5
        }
        result = QueryResult.from_dict(data)
        assert result.query_id == "q-1"
        assert result.method == RetrievalMethod.BM25
        assert len(result.retrieved_snippets) == 1
        assert result.metrics["ndcg@10"] == 0.95


class TestPerformanceDelta:
    """Tests for the PerformanceDelta dataclass."""
    
    def test_create_performance_delta(self):
        """Test creating a PerformanceDelta instance."""
        delta = PerformanceDelta(
            query_id="q-1",
            baseline_method=RetrievalMethod.BM25,
            rag_method=RetrievalMethod.RAG,
            baseline_metrics={"ndcg@10": 0.7},
            rag_metrics={"ndcg@10": 0.8}
        )
        assert delta.query_id == "q-1"
        assert delta.baseline_method == RetrievalMethod.BM25
        assert delta.rag_method == RetrievalMethod.RAG
    
    def test_compute_deltas(self):
        """Test computing performance deltas."""
        delta = PerformanceDelta(
            query_id="q-1",
            baseline_method=RetrievalMethod.BM25,
            rag_method=RetrievalMethod.RAG,
            baseline_metrics={"ndcg@10": 0.7, "precision@5": 0.5},
            rag_metrics={"ndcg@10": 0.8, "precision@5": 0.6}
        )
        delta.compute_deltas()
        assert delta.delta_metrics["ndcg@10"] == 0.1
        assert delta.delta_metrics["precision@5"] == 0.1
    
    def test_compute_deltas_missing_keys(self):
        """Test computing deltas when some metrics are missing."""
        delta = PerformanceDelta(
            query_id="q-1",
            baseline_method=RetrievalMethod.BM25,
            rag_method=RetrievalMethod.RAG,
            baseline_metrics={"ndcg@10": 0.7},
            rag_metrics={"precision@5": 0.6}
        )
        delta.compute_deltas()
        assert delta.delta_metrics["ndcg@10"] == -0.7  # 0 - 0.7
        assert delta.delta_metrics["precision@5"] == 0.6  # 0.6 - 0
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        delta = PerformanceDelta(
            query_id="q-1",
            baseline_method=RetrievalMethod.BM25,
            rag_method=RetrievalMethod.RAG,
            baseline_metrics={"ndcg@10": 0.7},
            rag_metrics={"ndcg@10": 0.8}
        )
        delta.compute_deltas()
        data = delta.to_dict()
        assert data["query_id"] == "q-1"
        assert data["baseline_method"] == "bm25"
        assert data["delta_metrics"]["ndcg@10"] == 0.1
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "query_id": "q-1",
            "baseline_method": "bm25",
            "rag_method": "rag",
            "baseline_metrics": {"ndcg@10": 0.7},
            "rag_metrics": {"ndcg@10": 0.8},
            "delta_metrics": {"ndcg@10": 0.1}
        }
        delta = PerformanceDelta.from_dict(data)
        assert delta.query_id == "q-1"
        assert delta.delta_metrics["ndcg@10"] == 0.1
    
    def test_from_dict_auto_compute_deltas(self):
        """Test that deltas are auto-computed if missing."""
        data = {
            "query_id": "q-1",
            "baseline_method": "bm25",
            "rag_method": "rag",
            "baseline_metrics": {"ndcg@10": 0.7},
            "rag_metrics": {"ndcg@10": 0.8}
        }
        delta = PerformanceDelta.from_dict(data)
        assert delta.delta_metrics["ndcg@10"] == 0.1