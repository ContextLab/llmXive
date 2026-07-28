"""
Unit tests for data models defined in src.data.models.
"""
import pytest
from src.data.models import RetrievalMethod, CodeSnippet, QueryResult, PerformanceDelta


class TestRetrievalMethod:
    """Tests for the RetrievalMethod enum."""

    def test_enum_values(self):
        """Verify enum members have correct string values."""
        assert RetrievalMethod.BM25.value == "bm25"
        assert RetrievalMethod.DUAL_ENCODER.value == "dual_encoder"
        assert RetrievalMethod.RAG.value == "rag"

    def test_enum_comparison(self):
        """Verify enum members can be compared."""
        assert RetrievalMethod.BM25 == RetrievalMethod.BM25
        assert RetrievalMethod.BM25 != RetrievalMethod.RAG


class TestCodeSnippet:
    """Tests for the CodeSnippet dataclass."""

    def test_minimal_snippet(self):
        """Test creation with required fields only."""
        snippet = CodeSnippet(
            snippet_id="123",
            language="python",
            code="def foo(): pass",
            docstring="A simple function"
        )
        assert snippet.snippet_id == "123"
        assert snippet.language == "python"
        assert snippet.code == "def foo(): pass"
        assert snippet.docstring == "A simple function"
        assert snippet.repo_name is None
        assert snippet.tokens == []

    def test_full_snippet(self):
        """Test creation with all fields."""
        snippet = CodeSnippet(
            snippet_id="456",
            language="java",
            code="public class Main {}",
            docstring="Main class",
            repo_name="test-repo",
            file_path="src/Main.java",
            function_name="Main",
            tokens=["public", "class", "Main"]
        )
        assert snippet.repo_name == "test-repo"
        assert snippet.file_path == "src/Main.java"
        assert snippet.function_name == "Main"
        assert len(snippet.tokens) == 3


class TestQueryResult:
    """Tests for the QueryResult dataclass."""

    def test_minimal_query_result(self):
        """Test creation with required fields."""
        result = QueryResult(
            query_id="q1",
            query_text="sort a list",
            method=RetrievalMethod.BM25,
            retrieved_snippets=[],
            ground_truth_ids=["gt1"]
        )
        assert result.query_id == "q1"
        assert result.query_text == "sort a list"
        assert result.method == RetrievalMethod.BM25
        assert result.retrieved_snippets == []
        assert result.ground_truth_ids == ["gt1"]
        assert result.nDCG_at_k is None
        assert result.rank_list == []

    def test_full_query_result(self):
        """Test creation with all fields populated."""
        snippet = CodeSnippet(
            snippet_id="s1",
            language="python",
            code="sorted(x)",
            docstring="Sort list"
        )
        result = QueryResult(
            query_id="q2",
            query_text="sort list python",
            method=RetrievalMethod.DUAL_ENCODER,
            retrieved_snippets=[snippet],
            ground_truth_ids=["gt1", "gt2"],
            nDCG_at_k=0.95,
            precision_at_k=0.5,
            recall_at_k=0.5,
            execution_time_ms=120.5,
            rank_list=[("s1", 0.98)]
        )
        assert result.nDCG_at_k == 0.95
        assert result.precision_at_k == 0.5
        assert result.recall_at_k == 0.5
        assert result.execution_time_ms == 120.5
        assert len(result.rank_list) == 1


class TestPerformanceDelta:
    """Tests for the PerformanceDelta dataclass."""

    def test_delta_calculation(self):
        """Test that delta fields are calculated correctly."""
        delta = PerformanceDelta(
            query_id="q3",
            baseline_method=RetrievalMethod.BM25,
            target_method=RetrievalMethod.RAG,
            baseline_score=0.5,
            target_score=0.8,
            metric_name="nDCG@10"
        )
        assert delta.absolute_delta == 0.3
        # (0.8 - 0.5) / 0.5 * 100 = 60.0
        assert delta.relative_delta_pct == 60.0

    def test_negative_delta(self):
        """Test calculation when target is worse than baseline."""
        delta = PerformanceDelta(
            query_id="q4",
            baseline_method=RetrievalMethod.BM25,
            target_method=RetrievalMethod.DUAL_ENCODER,
            baseline_score=0.8,
            target_score=0.6,
            metric_name="Precision@5"
        )
        assert delta.absolute_delta == -0.2
        # (0.6 - 0.8) / 0.8 * 100 = -25.0
        assert delta.relative_delta_pct == -25.0