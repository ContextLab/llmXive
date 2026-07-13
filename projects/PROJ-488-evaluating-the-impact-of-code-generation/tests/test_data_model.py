"""
Tests for the data model definitions in code/data_model.py.
"""
import pytest
from datetime import datetime
import statistics

from code.data_model import CodeSnippet, MetricScore, DatasetGroup, MetricResult, validate_metric_result

class TestCodeSnippet:
    def test_create_snippet(self):
        snippet = CodeSnippet(
            id="123",
            source="test",
            code="print('hi')",
            length=10,
            language="python"
        )
        assert snippet.id == "123"
        assert snippet.length == 10

    def test_auto_length_calculation(self):
        snippet = CodeSnippet(
            id="124",
            source="test",
            code="x = 1",
            length=None,
            language="python"
        )
        assert snippet.length == 5

    def test_to_dict(self):
        snippet = CodeSnippet("1", "src", "code", 4, "py")
        d = snippet.to_dict()
        assert d['id'] == "1"
        assert d['code'] == "code"

    def test_from_dict(self):
        data = {"id": "2", "source": "src", "code": "y=2", "length": 3, "language": "py"}
        snippet = CodeSnippet.from_dict(data)
        assert snippet.id == "2"
        assert snippet.language == "py"

class TestMetricScore:
    def test_create_score(self):
        score = MetricScore("1", "complexity", 5.5)
        assert score.snippet_id == "1"
        assert score.score == 5.5
        assert isinstance(score.timestamp, datetime)

    def test_serialization(self):
        score = MetricScore("1", "complexity", 5.5)
        d = score.to_dict()
        assert isinstance(d['timestamp'], str)
        assert d['metric_type'] == 'complexity'

class TestDatasetGroup:
    def test_add_snippet(self):
        group = DatasetGroup("Human")
        snippet = CodeSnippet("1", "src", "c", 1, "py")
        group.add_snippet(snippet)
        assert len(group.snippets) == 1

    def test_compute_aggregates_empty(self):
        group = DatasetGroup("Empty")
        agg = group.compute_aggregates()
        assert agg['count'] == 0
        assert agg['avg_length'] == 0.0

    def test_compute_aggregates_with_data(self):
        group = DatasetGroup("Test")
        group.add_snippet(CodeSnippet("1", "s", "a", 10, "p"))
        group.add_snippet(CodeSnippet("2", "s", "bb", 20, "p"))
        agg = group.compute_aggregates()
        assert agg['count'] == 2
        assert agg['avg_length'] == 15.0

class TestMetricResult:
    def test_calculate_from_scores(self):
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = MetricResult.calculate_from_scores(scores, "GroupA", "metricX")
        
        assert result.group_label == "GroupA"
        assert result.metric_type == "metricX"
        assert result.count == 5
        assert result.mean == 3.0
        assert result.median == 3.0
        assert result.min_val == 1.0
        assert result.max_val == 5.0

    def test_calculate_from_scores_empty(self):
        result = MetricResult.calculate_from_scores([], "Empty", "metric")
        assert result.count == 0
        assert result.mean == 0.0

    def test_schema_validation(self):
        result = MetricResult.calculate_from_scores([1.0], "G", "M")
        assert validate_metric_result(result) is True

        # Test invalid type manually constructed
        from code.data_model import MetricResult
        class BadResult:
            def to_dict(self):
                return {"group_label": "G", "metric_type": "M", "mean": "string", "median": 0, "variance": 0, "std_dev": 0, "count": 0, "min_val": 0, "max_val": 0}
        
        # This should fail validation because mean is string
        assert validate_metric_result(BadResult()) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])